# Evidencia TDD: imágenes API/UI reproducibles

Fecha: 29/10/2026. Responsable y revisión: misma sesión coordinadora; revisión humana pendiente en
MR #30. Rama: `feat/v2-container-foundation`. Propiedad: `Dockerfile`, `.dockerignore`, contrato de
arquitectura, runbook y esta evidencia.

## RED

`tests/architecture/test_container_image_contract.py` se escribió antes de los archivos de imagen.

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp/pytest-img-v2-red tests/architecture/test_container_image_contract.py
```

Resultado: exit 1, `3 failed`. `Dockerfile` y `.dockerignore` no existían, por lo que faltaban
stages, targets, usuario, comandos exec-form, labels, prohibición de build secrets y exclusiones.

## GREEN

Se añadió un Dockerfile multi-stage con builder uv fijado, base Python 3.12 por digest, runtime
compartido y targets finales `api`/`ui`. `uv sync --frozen --no-dev --no-editable` instala el wheel
y dependencias bloqueadas. Los targets ejecutan con UID/GID 10001, labels OCI y CMD JSON; no usan
shell. El contexto excluye secretos y artefactos locales.

Contrato estático: exit 0, `3 passed`. Builds reales:

- `docker build --target api ... -t agrorag-api:v2-test .`: exit 0.
- `docker build --target ui ... -t agrorag-ui:v2-test .`: exit 0.
- Contexto transferido inicialmente: aproximadamente 419 KiB; el segundo build reutilizó caché.
- API/UI: usuario `10001:10001`, versión label `0.1.0`, revisión `working-tree`.
- Tamaños locales: API 203.224.765 bytes; UI 203.228.032 bytes.

Inspección dentro de las imágenes confirmó import de los paquetes instalados y ausencia de pytest y
mypy. Un smoke con contenedores temporales obtuvo HTTP 200 en API `/health/live` y UI
`/_stcore/health`; ambos contenedores fueron detenidos y eliminados al finalizar.

## Seguridad y límites

`docker scout cves --only-severity critical --exit-code agrorag-api:v2-test` terminó con exit 1
antes del análisis porque Docker Scout exige login. No se interpreta como scan aprobado ni como
hallazgo de la imagen. El escaneo no interactivo permanece puerta de CI-V2-01.

No se suministraron claves al build, no se descargaron modelos y el catálogo no se incluyó. Compose,
permisos read-only y E2E del stack permanecen para la fase siguiente.
