# Ejecutar AgroRAG V2 con contenedores

Estado: implementación incremental. Imágenes, Compose local, gateway productivo, identidad/logs de
release y rollback de catálogo/imagen están verificados; CI de supply chain y garak continúan.

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

## Limitaciones todavía abiertas

- El recorrido browser→UI→API dentro de Compose y su ejecución en CI siguen pendientes; el smoke
  actual verificó UI health y API HTTP real con preview BM25.
- El scan Docker Scout local requiere autenticación y no se consideró ejecutado; el gate de CI debe
  usar un scanner no interactivo y registrar hallazgos/excepciones.
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

La imagen usa Caddy 2.11.4 fijado por digest, UID/GID 10002 y Caddyfile versionado. API/UI usan UID
10001. Los tres servicios tienen root filesystem read-only, tmpfs acotado, `cap_drop: ALL`,
`no-new-privileges`, límites de procesos/CPU/memoria y restart policy. Gateway recibe únicamente
`NET_BIND_SERVICE` para 80/443 y persiste certificados/configuración en volúmenes separados.

Crear fuera del repositorio un directorio de secretos con archivos `reader_key`, `openai_api_key` y
`gateway_auth`. Este último contiene una línea `usuario hash-bcrypt`; generar el hash de forma
interactiva para no dejar la contraseña en el historial:

```powershell
docker run --rm -it caddy:2.11.4-alpine caddy hash-password
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
