# OPS-OBS-03. Verificación integrada

Candidata local `demo-materia-2026-11-23-rc1` en `d0111a3`. Integración en el
worktree `.tmp/observability-grafana`, autor de la verificación integrada: coordinador.

## Docker y señales

- `docker build --target api-observability -t agrorag-api:observability .` y
  `docker build --target ui -t agrorag-ui:dev .` terminaron en exit 0.
- `docker compose -f compose.yaml -f compose.dev.yaml -f compose.observability.yaml config --quiet`
  terminó en exit 0.
- `docker build --progress=plain --output type=cacheonly .tmp/otel-smoke` terminó en exit 0.
  El ensayo local con AppTest, una API HTTP real, catálogo y modelo simulados y los componentes
  de Grafana LGTM se ejecutó dentro de una red aislada del build. Usó el tablero y
  los archivos de provisioning de la rama, sin modelo externo ni credenciales de proveedor.

El ensayo hizo dos consultas desde Streamlit y comprobó la respuesta verificada. Grafana
sirvió el tablero `agrorag-local`, Prometheus devolvió datos para todas las expresiones
del tablero, incluidos un hit y un miss, y Tempo devolvió las etapas `retrieval`,
`researcher` y `verifier` bajo `POST /v1/query`. La API respondió HTTP 200 con el
Collector detenido y exportó una nueva traza después de reiniciarlo.

## Regresión local

`python -m pytest -q --cov --cov-report= --basetemp .tmp/pytest-release` terminó en exit 0.
359 pruebas aprobadas, 1 omitida por plataforma, 3 deseleccionadas por el filtro de
integración del proyecto y 89,36 % de cobertura. Las ejecuciones anteriores agotaban el
límite de tres segundos al iniciar el primer AppTest en Windows. Ese arranque de prueba
tiene un margen de diez segundos. Sus aserciones y el código de Streamlit se conservaron.
Ruff, mypy, los dos contratos de importación, `uv lock --check` y la validación estricta
de OpenSpec terminaron en exit 0.
El conjunto de dependencias de runtime con el extra `tracing` se exportó con
`uv export --locked --extra tracing --no-dev --no-emit-project` y
`pip-audit --disable-pip --no-deps -r .tmp/obs-requirements.txt` terminó en exit 0,
sin vulnerabilidades conocidas en el conjunto auditado.

## Puertas de integración

El ensayo aislado cubre el tráfico entre componentes. El arranque completo con Compose y
un navegador real sigue pendiente. El intento de `docker compose up` recibió permiso denegado
en el pipe de Docker Desktop. El sandbox también impidió crear el índice Git del worktree
para preparar el commit. La validación de CI queda pendiente del commit y PR.

El [runbook](../../run-containerized.md#grafana-local-para-la-demo) contiene el recorrido
por Streamlit, Grafana y el ensayo de caída/reanudación. El informe y la presentación
se actualizarán después de la verificación del cierre técnico.
