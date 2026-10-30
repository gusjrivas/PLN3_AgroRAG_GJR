# Ejecutar AgroRAG V2 con contenedores

Estado: implementación incremental. Imágenes, Compose local, gateway productivo, identidad/logs de
release, rollback y supply chain están verificados. El runner Garak aprobó build/smoke y contratos
offline; staging y el primer scan autorizado continúan pendientes.

## Requisitos

- Docker Engine con BuildKit.
- Docker Compose Plugin para las fases siguientes.
- No se necesita Python ni uv del proyecto para construir o ejecutar las imágenes.

## Construir imágenes

Las bases Python 3.12 y uv están fijadas por digest. El builder instala desde `uv.lock` y los
targets finales comparten un virtualenv no editable, sin dependencias de desarrollo.

```powershell
docker build --target api --build-arg APP_VERSION=0.2.0 --build-arg VCS_REF=<commit> -t agrorag-api:<commit> .
docker build --target ui --build-arg APP_VERSION=0.2.0 --build-arg VCS_REF=<commit> -t agrorag-ui:<commit> .
```

No pasar claves mediante `--build-arg`. `.dockerignore` excluye `.env*`, Git, entornos, tests,
outputs, corpus local y libros de evidencia. Las imágenes ejecutan como UID/GID `10001:10001`.

## Smoke de imagen

API sin catálogo/modelo sigue exponiendo sólo liveness; readiness permanece cerrada:

```powershell
docker run --rm -p 127.0.0.1:18000:8000 agrorag-api:<commit>
```

En otra terminal, `http://127.0.0.1:18000/health/live` debe devolver `{"status":"ok"}`. Para UI:

```powershell
docker run --rm -p 127.0.0.1:18501:8501 agrorag-ui:<commit>
```

`http://127.0.0.1:18501/_stcore/health` debe responder 200. Sin reader key, la pantalla muestra la
advertencia segura y no consulta API.

`GET /health/version` expone versión, commit, referencia inmutable de imagen y versión de catálogo,
sin configuración ni secretos. Cada respuesta API incluye `X-Request-ID`; el evento
`http_request_completed` se escribe como una línea JSON con método, path sin query string, estado y
duración. Uvicorn access log se desactiva para no duplicar ni registrar parámetros.

## Secretos en runtime

Los despliegues usarán archivos montados y una única variable por secreto:

- `AGRO_READER_KEY_FILE=/run/secrets/reader_key` en API y UI.
- `OPENAI_API_KEY_FILE=/run/secrets/openai_api_key` sólo en API cuando se seleccione OpenAI.
- `PINECONE_API_KEY_FILE=/run/secrets/pinecone_api_key` sólo en los perfiles que lo necesiten.

Definir a la vez el valor directo y `*_FILE`, o montar un archivo ausente/vacío, bloquea startup.
La imagen no contiene secretos, catálogo, certificados ni configuración productiva.

## Compose local

Preparar `.env` como en el runbook local y conservar al menos `AGRO_READER_KEY`. El overlay dev
publica API/UI exclusivamente en loopback. Los puertos se pueden cambiar con `AGRO_API_PORT` y
`AGRO_UI_PORT`.

Primero publicar el catálogo en el volumen. El job usa `data/manifest.json` y los PDF ya descargados
en `data/raw`; el bind es read-only y el job no tiene red:

```powershell
docker compose --profile admin -f compose.yaml -f compose.dev.yaml run --rm catalogue-admin
```

La operación es idempotente: repetirla con los mismos archivos conserva versión y cantidad. Luego:

```powershell
docker compose -f compose.yaml -f compose.dev.yaml up --build --wait
```

Abrir `http://127.0.0.1:8501`. UI llama a `http://api:8000` por la red Compose; sólo los puertos
loopback del overlay dev son visibles desde el host. El healthcheck local verifica liveness para
permitir exploración BM25 sin modelo; `/health/ready` continúa devolviendo no-ready hasta configurar
catálogo y proveedor generativo completos. El overlay productivo usará readiness autenticada.

`api` monta `/var/lib/agrorag/catalogue` read-only y `catalogue-admin` lo monta read-write. Reiniciar
o recrear servicios conserva el volumen. Detener sin eliminar datos:

```powershell
docker compose -f compose.yaml -f compose.dev.yaml down
```

`down -v` elimina de forma irreversible el volumen activo y sólo debe usarse después de backup o
para un volumen de prueba explícito. Para aislar ensayos, definir por ejemplo
`AGRO_CATALOGUE_VOLUME=agrorag_catalogue_v2_test` antes de ejecutar Compose.

## E2E Compose reproducible

El E2E de browser es opt-in porque requiere Docker y Chromium de Playwright. CI debe construir las
imágenes una vez y ejecutar exactamente esos tags:

```powershell
$env:AGRO_E2E_API_IMAGE = '<imagen-api-candidata>'
$env:AGRO_E2E_UI_IMAGE = '<imagen-ui-candidata>'
uv run pytest -m e2e tests/e2e/test_compose_browser.py
```

El test genera datos sintéticos, usa puertos/volumen únicos, no llama proveedores, prueba reinicio y
limpia sus recursos. No usa el catálogo ni volumen local del usuario.

## Limitaciones todavía abiertas

- La publicación GHCR sólo puede comprobarse al integrar en `main`; el PR ya verificó E2E, SBOM,
  scans y gate sobre las mismas imágenes candidatas.
- Falta un host Linux staging autorizado, dominio/TLS, presupuesto de proveedor y credenciales de
  ensayo para ejecutar el primer reporte Garak real. Ningún resultado adversarial fue fabricado.
- Docker Scout local requiere autenticación y no se usó como evidencia. Trivy 0.76.1 sí se ejecutó
  sin login y el workflow conserva JSON/SBOM; consultar la política y evidencia CI-V2-01.
- Estas imágenes contienen el perfil BM25 base. El job semántico/administrativo se define de forma
  separada para no incorporar dependencias pesadas al runtime API/UI.

## Overlay productivo

`compose.production.yaml` no contiene build ni bind mounts. Exige imágenes API/UI/gateway por
digest, un volumen de catálogo prepublicado, dominio, modelo OpenAI y tres secretos externos. Sólo
gateway publica 80/443; API y UI permanecen en la red Compose.

Construir/publicar el gateway versionado antes de desplegar:

```powershell
docker build --target gateway --build-arg VCS_REF=<commit> -t <registry>/agrorag-gateway:<commit> .
```

La imagen usa Caddy 2.11.7 fijado por digest, actualiza paquetes Alpine corregibles durante build,
UID/GID 10002 y Caddyfile versionado. API/UI usan UID
10001. Los tres servicios tienen root filesystem read-only, tmpfs acotado, `cap_drop: ALL`,
`no-new-privileges`, límites de procesos/CPU/memoria y restart policy. Gateway recibe únicamente
`NET_BIND_SERVICE` para 80/443 y persiste certificados/configuración en volúmenes separados.

Crear fuera del repositorio un directorio de secretos con archivos `reader_key`, `openai_api_key` y
`gateway_auth`. Este último contiene una línea `usuario hash-bcrypt`; generar el hash de forma
interactiva para no dejar la contraseña en el historial:

```powershell
docker run --rm -it caddy:2.11.7-alpine caddy hash-password
```

Asignar las variables del ambiente o secret store: `AGRO_API_IMAGE`, `AGRO_UI_IMAGE` y
`AGRO_GATEWAY_IMAGE` con referencias `@sha256:...`; `AGRO_CATALOGUE_VOLUME`, `AGRO_DOMAIN`,
`AGRO_OPENAI_MODEL`, `AGRO_SECRETS_DIR`, `AGRO_RELEASE_VERSION` (semver) y `AGRO_COMMIT_SHA`.
El overlay pasa `AGRO_API_IMAGE` también como identidad observable de la imagen. Validar sin revelar
contenido:

```powershell
docker compose -f compose.yaml -f compose.production.yaml config --quiet
docker compose -f compose.yaml -f compose.production.yaml up -d --wait --no-build
```

API usa readiness autenticada en este overlay; por eso una credencial/modelo/catálogo incompletos
bloquean la cadena UI→gateway. Caddy aplica autenticación básica mínima, TLS automático, headers de
seguridad y logs JSON. En un ambiente corporativo, reemplazar basic auth por el ingress/IdP aprobado
sin exponer API directamente.

La sintaxis, separación de secretos y hardening fueron probados. La emisión TLS real queda pendiente
de dominio/DNS y la promoción por digest depende de seleccionar registry; no se declara un deploy
productivo real hasta ejecutar staging.

## Supply chain y política de vulnerabilidades

`.github/workflows/containers.yml` construye API/UI/gateway una sola vez, ejecuta el E2E Compose
sobre esos tags, genera SBOM SPDX JSON, escanea vulnerabilidades y secretos con Trivy 0.76.1, y
publica las mismas imágenes sólo en `main` o tags semver. No crea `latest`: conserva tag SHA,
digest y `release-manifest.json`; semver es una etiqueta adicional sobre los mismos bytes.

Toda acción externa está fijada a un commit completo. `scripts/check_vulnerability_policy.py`
bloquea siempre CRITICAL y secretos; HIGH exige una entrada completa y no vencida en
`configs/security/vulnerability-exceptions.json`. Las excepciones actuales corresponden únicamente
al binario oficial Caddy 2.11.7, tienen responsable y vencen el 15/11/2026. Vencidas o ausentes
bloquean automáticamente; deben eliminarse al publicar Caddy corregido. No son una declaración de
ausencia de riesgo ni autorizan promoción sin triage humano.

La ejecución de PR `40996190194` aprobó build único, E2E, tres SBOM/scans y el gate. La publicación
se omitió deliberadamente por no ser un push a `main`; al integrar, el workflow publica esos mismos
bytes por SHA y conserva el manifiesto de digests.

## Evaluación Garak

`compose.security.yaml` es independiente del runtime y sólo define el perfil one-shot `security`.
Construye `Dockerfile.garak` con Garak 0.17.0 y un lock exacto de 197 paquetes, corre como UID/GID
10003 sin puertos, capabilities ni
credenciales de proveedor, y escribe evidencia fuera del contenedor. La distribución oficial de
Garak arrastra PyTorch/CUDA: la imagen local validada mide 3.292.465.354 bytes. Debe publicarse y
cachearse por separado; nunca se incorpora a API/UI/gateway.

El lock actual incluye wheels CUDA y el Dockerfile falla cerrado fuera de `linux/amd64`. Soportar
ARM64 exige resolver/escanear un lock e imagen propios; no se presume portabilidad binaria.

Antes del scan, crear una identidad Basic exclusiva y de mínimo privilegio para staging. El secreto
`gateway_authorization` contiene `Basic <base64(usuario:password)>`; `reader_key` contiene la misma
reader key configurada en la API candidata. Ambos archivos deben provenir del secret store y tener
acceso restringido. No reutilizar el archivo Caddy `gateway_auth`: ese archivo contiene un hash y
no es una cabecera cliente.

En Linux, preparar un directorio restringido escribible por el UID del runner y configurar un
endpoint autorizado exacto:

```bash
sudo install -d -m 0700 -o 10003 -g 10003 /var/lib/agrorag/garak
export AGRO_GARAK_OUTPUT_DIR=/var/lib/agrorag/garak
export AGRO_GARAK_SECRETS_DIR=/ruta/del/secret-store/garak
export AGRO_GARAK_TARGET_URL=https://staging.example.org/v1/query
export AGRO_GARAK_RELEASE_ID=2.0.0-sha-<commit>
export AGRO_COMMIT_SHA=<commit-completo>
docker compose -f compose.security.yaml --profile security config --quiet
docker compose -f compose.security.yaml --profile security build garak
docker compose -f compose.security.yaml --profile security run --rm garak
```

El adaptador loopback es el único componente que ve ambas credenciales y rechaza targets que no
sean HTTPS o no terminen en `/v1/query`. Garak prueba cuatro familias acotadas: prompt injection,
jailbreak, Base64 y generación de credenciales aparentes, con seed 1729, una generación y cap 32.
El costo máximo real depende de los prompts que expanda Garak; confirmar presupuesto/proveedor antes
de ejecutar. No apuntar este perfil a producción sin autorización explícita.

Los reportes e hitlogs quedan en `raw/` con modo `0600` y pueden contener prompts/respuestas; no se
suben a Git ni a artefactos de acceso general. `summary/<release>.json` contiene sólo agregados,
hashes de configuración/política y decisión. Un hallazgo HIGH sin triage, uno confirmado sin
excepción completa/vigente, una regresión o un detector esperado ausente bloquean el job. Completar
`infra/garak/triage.json`, `exceptions.json` y `baseline.json` mediante revisión humana; no convertir
automáticamente un hit heurístico en vulnerabilidad confirmada.

Trivy 0.76.1 dejó 0 CRITICAL, 1 HIGH y 0 secretos. El HIGH es CVE-2026-104851 de `fsspec`; afecta
`ReferenceFileSystem` al procesar un documento Kerchunk/reference no confiable, superficie que este
runner no invoca. `datasets 3.6` impide actualizar a la versión corregida sin salir del conjunto de
dependencias de Garak 0.17.0. La excepción vive aislada en
`configs/security/garak-runner-vulnerability-exceptions.json`, vence el 15/11/2026 y no se aplica a
API/UI/gateway. Referencia primaria:
https://github.com/fsspec/filesystem_spec/security/advisories/GHSA-27vj-qcqg-25rc.

## Backup y rollback

`compose.ops.yaml` agrega jobs offline y no forma parte del runtime. El backup monta el catálogo
read-only y el directorio de destino read-write; restore invierte únicamente el permiso del catálogo
y monta el backup read-only. Ambos ejecutan sin red, capabilities ni privilegios adicionales.

Antes de promover una candidata, conservar en el registro restringido de release los tres digests
API/UI/gateway y el Compose renderizado. Configurar un directorio absoluto fuera del repositorio y
crear un backup nombrado de forma inmutable:

```powershell
$env:AGRO_BACKUP_DIR = 'D:\backups\agrorag'
$env:AGRO_BACKUP_FILE = 'catalogue-2.0.0-20261030.zip'
$env:AGRO_RELEASE_VERSION = '2.0.0'
$env:AGRO_COMMIT_SHA = '<commit-completo>'
$env:AGRO_API_IMAGE = '<registry>/agrorag-api@sha256:<digest>'
docker compose --profile backup -f compose.yaml -f compose.ops.yaml run --rm catalogue-backup
```

El ZIP contiene sólo `active.json`, el SQLite activo y metadata con hashes, versión de corpus,
release, commit e imagen API. Copiarlo además a almacenamiento con retención/acceso controlados y
probar restore periódicamente; tener un ZIP en el mismo host no es una estrategia de recuperación.

Si falla la candidata, detener el stack antes de cambiar el puntero. Restaurar valida nombres y
SHA-256, publica el snapshot si falta y reemplaza `active.json` al final; no elimina snapshots:

```powershell
docker compose -f compose.yaml -f compose.production.yaml down
docker compose --profile restore -f compose.yaml -f compose.ops.yaml run --rm catalogue-restore
$env:AGRO_API_IMAGE = '<digest-api-anterior>'
$env:AGRO_UI_IMAGE = '<digest-ui-anterior>'
$env:AGRO_GATEWAY_IMAGE = '<digest-gateway-anterior>'
docker compose -f compose.yaml -f compose.production.yaml up -d --wait --no-build
docker compose -f compose.yaml -f compose.production.yaml exec api agro-rag-healthcheck
```

Confirmar luego `/health/version`, `/v1/corpus` y un caso funcional por gateway. Si el restore falla
integridad, no forzar ni editar el ZIP: mantener el stack detenido y usar el backup anterior. Nunca
usar `down -v` durante rollback.
