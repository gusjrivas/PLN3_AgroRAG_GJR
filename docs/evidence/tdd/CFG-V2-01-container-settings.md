# Evidencia TDD: configuración y healthcheck container-safe

Fecha: 29/10/2026. Responsable y revisión: misma sesión coordinadora; revisión humana pendiente en
MR #30. Rama: `feat/v2-container-foundation`. Propiedad: settings backend/UI, healthcheck,
pruebas unitarias, `.env.example`, runbook, OpenSpec 07 y esta evidencia.

## RED — secretos montados

Se añadieron primero seis escenarios observables en
`tests/unit/test_container_settings.py`: reader/OpenAI/Pinecone desde archivo, redacción, conflicto
directo+archivo, archivo ausente/vacío e URL interna de UI.

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp/pytest-cfg-v2-red tests/unit/test_container_settings.py
```

Resultado: exit 1, `6 failed`. Settings ignoraba todas las variables `*_FILE`, no cargaba valores
ni rechazaba conflictos/archivos inválidos. La afirmación sobre `http://api:8000` se conservó como
caracterización: esa URL ya era aceptada y no se fabricó un RED.

## GREEN — resolución fail-closed

Backend y UI incorporan campos de ruta no representables y validación posterior. Cada archivo se
lee una vez en startup, se elimina whitespace exterior y se rechaza si no es legible o queda vacío.
Configurar valor y archivo simultáneamente falla. `hide_input_in_errors` y los campos `repr=False`
evitan incluir valores centinela en representaciones y errores.

El healthcheck también comenzó con un test RED separado:

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp/pytest-health-v2-red tests/unit/test_healthcheck_command.py
```

Resultado: exit 1, `3 failed`, porque el módulo no existía. GREEN añadió
`agro-rag-healthcheck`: consulta readiness con HTTP sin proxy ni shell, usa la reader key resuelta,
devuelve false ante error y no imprime el detalle de excepción.

La suite dirigida GREEN terminó con exit 0: `16 passed`.

## REFACTOR y regresión

Se aisló `test_missing_key_does_not_send_request` del `.env` privado local; el fallo ampliado era
contaminación del entorno ya documentada en DEL-02, no una regresión del producto.

- Suite offline completa aislada: exit 0, `229 passed, 2 deselected`.
- Ruff check: exit 0.
- Ruff format inicial: exit 1, dos archivos requerían formato; se aplicó Ruff y se repite en cierre.
- mypy estricto sobre `src`: exit 0, 37 archivos.
- import-linter: exit 0, 2 contratos mantenidos.
- OpenSpec 07 strict: exit 0, cambio válido.
- `uv lock --check`: exit 0, 146 paquetes resueltos sin cambiar dependencias.

No se consultaron proveedores, no se descargaron modelos y no se imprimieron secretos. ARC-V2-02,
las imágenes y Compose continúan pendientes; este corte no declara containerización completa.
