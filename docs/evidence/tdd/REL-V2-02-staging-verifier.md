# Evidencia TDD: verificador inmutable de release en staging

Fecha: 30/10/2026. Responsable y revisión: misma sesión coordinadora; revisión humana pendiente en
MR #30. Rama: `feat/v2-container-foundation`. Propiedad: verificador/workflow de staging, ruta de
operabilidad del gateway, contratos, OpenSpec, runbook y esta evidencia.

Commit de implementación: `2d61c7e` (`feat: verify immutable staging release`).

## RED

Se escribieron primero los contratos de manifiesto, target, confidencialidad, gateway y workflow.
El comando focalizado terminó con exit 2 durante colección y
`ModuleNotFoundError: No module named 'scripts.verify_staging_release'`. Además, el Caddyfile no
tenía `handle /health/*` y `.github/workflows/staging-release.yml` no existía. Por tanto, el runbook
pedía observar `/health/version` por gateway sin que esa ruta pudiera alcanzar API y sin una puerta
ejecutable que la comparara con el manifiesto publicado.

## GREEN

- `scripts/verify_staging_release.py` acepta únicamente un esquema cerrado con commit completo y
  paquetes `api`, `ui` y `gateway` del repositorio esperado mediante `@sha256`; tags, componentes
  faltantes, claves extra, paquete ajeno o commit distinto bloquean.
- El target debe ser un origen HTTPS sin path, query, fragmento ni credenciales. El cliente no usa
  proxies del ambiente ni sigue redirects y nunca incluye cuerpo/respuesta/secretos en errores.
- `/health/version` debe coincidir exactamente con versión, commit, referencia API por digest y
  corpus. `/v1/corpus` debe publicar el mismo corpus y evidencia no vacía. La pregunta sintética
  debe terminar como `answered`, con request ID UUID y al menos una cita.
- La evidencia conserva sólo hostname, hash/manifiesto/digests, identidad, conteos, modo, request ID
  y cantidad de citas. No copia pregunta, respuesta, Basic auth ni reader key. Un bloqueo alcanzado
  por el verificador también produce un resumen sanitizado.
- Caddy enruta `/health/*` y `/v1/*` a API bajo su `basic_auth` global; UI continúa como fallback.
- `staging-release-smoke` exige aprobación del environment `staging`, autorización/costo explícitos,
  descarga por run ID el artefacto `release-manifest-<commit>`, usa credenciales efímeras `0600`,
  sube el resumen 90 días y limpia con `always()`.

Resultados focalizados:

- pytest de verificador, gateway y workflows: exit 0, `15 passed`.
- Ruff check/format: exit 0.
- `uv run mypy scripts/verify_staging_release.py`: exit 0, un archivo sin issues.
- actionlint 1.7.12 sobre todos los workflows: exit 0.
- OpenSpec 1.14.3 estricto: exit 0, `8 passed`.
- Build del target gateway y `caddy validate` con secreto sintético efímero: exit 0.

## REFACTOR y regresión

El directorio temporal se inicializa antes de cualquier paso que use `always()`, evitando que un
fallo temprano convierta una ruta vacía en un target de upload/cleanup. El commit solicitado se pasa
por entorno después de validarlo y se vuelve a comparar dentro del manifiesto; ningún input de
workflow se interpola directamente como shell sin esa barrera. Request ID y modo se validan antes
de conservarlos para que una respuesta remota no inyecte contenido arbitrario en la evidencia.

Suite completa y controles: Ruff, format, mypy sobre 38 archivos de producto más el verificador,
dos contratos import-linter y `git diff --check`, exit 0. Pytest terminó con exit 0:
`275 passed, 3 deselected, 1 warning in 11.11s`.

El HEAD `ad786e6` aprobó en GitHub
[quality 41002537329](https://github.com/gusjrivas/PLN3_AgroRAG_GJR/actions/runs/41002537329):
offline, OpenSpec y browser terminaron `success`. También aprobó
[container supply chain 41002537339](https://github.com/gusjrivas/PLN3_AgroRAG_GJR/actions/runs/41002537339):
el gateway con la nueva ruta fue construido una vez junto con API/UI, y E2E, tres SBOM, tres scans,
política y evidencia terminaron `success`. Publicación se omitió correctamente por ser un PR.

## Límite pendiente

No se descargó un manifiesto publicado ni se llamó un staging real: el MR sigue draft, todavía no
existen paquetes post-merge, host/dominio/TLS, secrets de environment ni autorización/presupuesto
externos. La automatización es evidencia de preparación, no de despliegue. OpenSpec 5.3 continúa
abierto hasta adjuntar el run real, inventario del host, backup/restore, smoke, Garak y triage; 5.4
continúa abierto hasta promover exactamente esos digests y verificar salud/rollback.
