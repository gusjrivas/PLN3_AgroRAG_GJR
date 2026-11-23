# Auditoría de main y plan de correcciones

Fecha: 2026-11-22  
Commit auditado: `b9ad1b5ba047c116bc3dff2fbdefc5dd387f6483`  
Alcance: controles de calidad, dependencias vulnerables, cobertura, CI e higiene documental. No se ejecutó Garak.

## Resultado de la auditoría

### Hallazgos confirmados

1. **Dependencia vulnerable en el extra opcional de tracing.** `pyproject.toml` fija
   `opentelemetry-sdk==1.45.1`; `uv.lock` resuelve `opentelemetry-api==1.45.1`. `pip-audit`
   encontró CVE-2026-126360, corregido en `opentelemetry-api 1.45.2`. El extra no forma parte de
   la imagen runtime normal, pero CI instala tracing y actualmente no audita ese lock.
   [Aviso del proyecto OpenTelemetry](https://github.com/advisories/GHSA-mf5v-w3w3-f6cg).

2. **Runner Garak fijado a una dependencia con un HIGH conocido y excepción vencida.** El scan
   retenido del runner `d38814b` informa `CVE-2026-104851` en `fsspec 2025.3.0`, corregido desde
   `2026.6.0`. `infra/garak/requirements.lock` todavía fija la versión vulnerable y la excepción
   venció el 2026-11-15. Si se reconstruye hoy, la política actual rechaza la excepción expirada.
   El flujo `garak-runner.yml` construye y escanea la imagen sin ejecutar Garak; la remediación no
   requiere repetir la evaluación adversarial.

3. **Excepciones vencidas del gateway sin hallazgos actuales correspondientes.** El artefacto
   `container-supply-chain` del commit auditado (22/11) conserva scans de API, UI y gateway sin
   hallazgos HIGH/CRITICAL. Las seis entradas gateway vencieron el 15/11 y ya no aparecen en ese
   scan, incluida CVE-2026-78661 después del parche integrado. Mantenerlas confunde inventario
   vigente con historial; no justifica extenderlas 30 días.

4. **La cobertura de tracing no entra en el reporte estándar de CI.** La suite offline pasa,
   pero omite tres pruebas de tracing porque el extra opcional no está instalado y
   `infrastructure/tracing.py` queda en 0% en ese informe. CI ejecuta después los contratos de
   tracing, sin acumular su cobertura. El cambio propuesto de `--cov-append` es adecuado si se
   verifica en CI.

5. **Hay huecos de cobertura en adaptadores de infraestructura.** En la corrida local Windows,
   `tokenizer.py` quedó en 71%, `pinecone.py` en 77% y `bootstrap/app.py` en 79%. Son oportunidades
   para tests offline sobre ramas de validación y cableado; la cobertura global sí supera el
   umbral configurado.

### Hallazgos descartados o no accionables ahora

- La documentación de tiktoken no falta: README enlaza a `docs/run-local.md`, que documenta el
  perfil y el comando; existe evidencia de una consulta real con ese perfil.
- Las listas maestras de OpenSpec contienen secciones marcadas explícitamente como históricas.
  No se deben marcar como pendientes ni completar casillas sin evidencia individual.
- La regla `Teoria*` funciona como resguardo de procedencia y no exige que hoy exista una carpeta
  con ese nombre. Se conserva.
- Starlette emite una advertencia real sobre `httpx` en `TestClient`. No se cambia a `httpx2` ni
  se fija otra versión sin una prueba de compatibilidad: `httpx` también es cliente de runtime.

## Verificación de la base

- GitHub Actions en el commit auditado: `quality` y `container-supply-chain` completados con éxito.
- Local, Python 3.12.15 / Windows: Ruff, formato, mypy e import-linter correctos.
- `pytest --cov`: 349 passed, 4 skipped, 3 deselected, 1 warning; cobertura global 86.99%.
- Domain/application: 96%; supera el umbral de 90%.
- Política de vulnerabilidades: 3 tests pasan. Los scans de imágenes de API/UI/gateway actuales
  no contienen HIGH/CRITICAL; el artefacto histórico del runner sí contiene el HIGH señalado.
- No se verificaron builds Docker locales ni se lanzó Garak.

## Plan priorizado

### P0 — Corregir OpenTelemetry y auditar los extras

Actualizar el extra tracing a `opentelemetry-sdk==1.45.2`, regenerar el lock con la versión de uv
fijada en CI y añadir a CI una auditoría del lock que incluya `tracing` (sin fallar por el paquete
editable del proyecto). Mantener prueba contractual de tracing.

**Cierre:** `pip-audit` no reporta CVE-2026-126360; `uv sync --locked --extra tracing`, contratos
de tracing y quality CI pasan.

### P1 — Corregir el runner y limpiar excepciones de imagen

Actualizar Garak a 0.17.1, que admite `datasets` 5.x y `transformers` 5.19; regenerar el lock completo con `fsspec 2026.9.0`, actualizar policy y resúmenes de versión y reconstruir/escanear localmente sólo la imagen del runner. No ejecutar Garak ni publicar la imagen. Retirar la excepción CVE-2026-104851 únicamente si el scan local actual confirma que desapareció; si permanece, detener esa parte y documentar la causa para decidirla explícitamente.\nRetirar las seis excepciones gateway ausentes del scan vigente y conservar el artefacto como
trazabilidad.

**Cierre:** los dos scans vigentes no reportan los IDs retirados; los gates de política pasan con
la fecha actual; ninguna excepción se extiende por rutina.

### P2 — Incorporar la cobertura de tracing al informe

En el paso opcional de CI, acumular cobertura de `test_academic_tracing.py` y generar los reportes
después de esa ejecución. No relajar ni excluir módulos del umbral.

**Cierre:** CI muestra cobertura de `infrastructure/tracing.py` y mantienen sus umbrales actuales.

### P3 — Completar pruebas offline de infraestructura

Tomar los tests añadidos en el PR #60 como candidatos a revisar, no como cambio aprobado. Adaptar
los casos útiles sobre tokenizer, Pinecone y bootstrap a la base actual, con dobles deterministas
y sin red/modelos. Priorizar ramas con validaciones de identidad, errores y cierre de recursos.

**Cierre:** suite focal y completa pasan; Ruff/mypy/import-linter pasan; cobertura sube sin
exclusiones y la CI remota está verde.

### P4 — Investigar la advertencia de TestClient

Hacer una prueba de compatibilidad acotada de FastAPI/Starlette/httpx2 y revisar si el cliente
HTTP de runtime comparte esa dependencia. Cambiar sólo si la compatibilidad funcional y de
tipado está demostrada; de lo contrario registrar la advertencia como deuda conocida.

## Rama Claude / PR #60

El PR #60 no es integrable en su estado actual: no tiene checks reportados y GitHub lo marca con
conflictos frente a `main`. Su contenido no es enteramente inválido: el parche OpenTelemetry
coincide con el aviso oficial; las pruebas de cobertura y la acumulación de cobertura de tracing
son propuestas razonables. Se cierra y elimina la rama remota por estar obsoleta como rama de
integración; el PR cerrado conserva el diff como referencia. Los cambios útiles se reaplican sobre
una rama limpia según este plan y con CI verde.
