# META-02 — política común y contrato de retrieval

Fecha: 2026-11-08. Rama: `feat/meta-02-retrieval-policy`.
Base: `ab032e4f334c42ee875743a83c3ad1fa115d5bd5`. Issue: #44. PR draft: #45.
Responsable: agente RAG/datos A, coordinado por Gustavo Julián Rivas.

## Alcance y caracterización

Se modificaron únicamente el contrato y la orquestación de retrieval, el adaptador BM25, la
composición runtime y sus pruebas unitarias. API, `QueryService`, Pinecone, corpus y manifiesto no
se editaron. Antes del cambio:

```text
python -m pytest tests/unit/test_retrieval.py tests/unit/test_retrieval_pipeline.py tests/unit/test_retrieval_runtime.py -q
# exit 0: 54 passed
```

El contrato anterior recibía sólo `crop`; BM25 filtraba dentro del adaptador y el pipeline repetía
esa regla. No existían filtros estructurados ni una clasificación común para etapa/región.

## RED

Se escribieron primero seis escenarios observables:

- orden estable `exact` → `general` → `unknown` y exclusión de incompatibles;
- ausencia de filtros conserva el orden del proveedor;
- BM25 directo usa la política estructurada;
- pipeline usa la misma política y entrega filtros estructurados al ranker;
- compatibilidad temporal del argumento `crop` hasta META-03;
- runtime BM25 acepta filtros sin inicializar proveedores semánticos.

```text
python -m pytest tests/unit/test_retrieval.py tests/unit/test_retrieval_pipeline.py tests/unit/test_retrieval_runtime.py -q -k "meta_02 or bm25_runtime_does_not_initialize"
# exit 1: 6 failed, 53 deselected
```

Los seis fallos fueron funcionales: `RetrievalFilters` y la política no existían. No se usaron red,
modelos ni proveedores live.

## GREEN

Se agregó `RetrievalFilters` inmutable con vocabularios runtime y una política pura en application.
La política:

1. excluye cultivo contradictorio y restricciones específicas declaradas que contradicen etapa o
   región;
2. conserva exactos, luego generales y luego metadata desconocida;
3. mantiene el orden del proveedor dentro de cada clase;
4. usa cultivo sólo para excluir contradicciones: sin etapa/región no prioriza evidencia etiquetada
   sobre evidencia compatible sin cultivo;
5. no reordena ni excluye por metadata cuando no hay filtros.

El pipeline aplica la clasificación contra el catálogo local autoritativo después de cada ranking,
RRF y reranker, antes de diversidad y presupuesto. BM25 directo reutiliza la misma función pura.

La primera implementación mínima hizo pasar los seis escenarios originales (`6 passed, 53
deselected`) y la suite focalizada de ese punto quedó en `59 passed`. Después se alinearon los
nombres con el test-plan, se parametrizó la política en los cuatro modos y se agregó el escenario
explícito de cultivo; por eso esos conteos intermedios no describen la selección actual. El mismo
selector `-k` sobre el árbol final termina en `7 passed, 62 deselected`.

`FilterInput` conserva temporalmente `str | None` para que `QueryService` y evaluación sigan
funcionando hasta META-03; se normaliza inmediatamente a `RetrievalFilters`. Pinecone permanece
fuera de alcance: bootstrap usa un puente explícito que sólo empuja `crop`, mientras el pipeline
resuelve autoritativamente etapa/región en local. META-04 reemplazará ese puente al ampliar el
adaptador remoto.

## Correcciones de revisión

La revisión independiente detectó tres brechas: cultivo estaba influyendo en prioridad, los tipos
no-string podían producir `TypeError` al consultar un `frozenset`, y faltaba demostrar el límite del
puente Pinecone con filtros contextuales. Se escribieron primero los escenarios nuevos:

```text
python -m pytest tests/unit/test_retrieval.py tests/unit/test_retrieval_runtime.py -q -k "crop_only_excludes or retrieval_filters_reject or hybrid_runtime_composes"
# exit 1: 3 failed, 4 passed, 17 deselected
```

Los fallos observables fueron el reordenamiento `[tomato, untagged]` y dos `TypeError` para listas
en etapa/región. El escenario runtime ya pasaba y caracterizó el puente: Pinecone recibió sólo
`crop`, mientras la política local priorizó etapa/región. Tras corregir clasificación y validación,
el mismo comando terminó con exit 0: `7 passed, 17 deselected`.

## REFACTOR y regresión

```text
python -m pytest tests/unit/test_query.py tests/contract/test_query_api.py tests/unit/test_pinecone.py tests/unit/test_audit.py -q
# exit 0: 63 passed, 1 warning externa conocida

python -m pytest tests/unit/test_retrieval.py tests/unit/test_retrieval_pipeline.py tests/unit/test_retrieval_runtime.py tests/unit/test_retrieval_metrics.py -q
# exit 0: 78 passed; la política común se parametrizó en los cuatro modos

python -m pytest -q
# exit 0: 329 passed, 1 skipped, 3 deselected, 1 warning
```

La advertencia es la deprecación externa ya conocida de Starlette TestClient/httpx. El skip en
Windows corresponde a bits POSIX del runner Garak.

Controles finales:

- `python -m ruff check .`: exit 0;
- `python -m ruff format --check .`: exit 0, 243 archivos formateados;
- `python -m mypy src`: exit 0, 38 archivos sin issues;
- `.venv\Scripts\lint-imports.exe`: exit 0, 2 contratos conservados;
- OpenSpec `08-metadata-aware-retrieval --strict`: válido;
- `git diff --check`: exit 0.

## Estado de entrega

- Commit funcional: `ecff9f1` (`feat: add metadata-aware retrieval policy`); push pendiente del
  coordinador al registrar esta evidencia.
- Revisión independiente: completada por un agente distinto. El revisor detectó las tres brechas
  registradas arriba y, después de las correcciones, confirmó que no quedan bloqueantes; repitió
  retrieval+métricas (`78 passed`), Ruff, formato, mypy y `git diff --check`.
- Riesgo transitorio: consumidores actuales pueden seguir enviando sólo cultivo; etapa y región no
  llegarán desde API hasta META-03. Esto se documenta, no se oculta con inferencias.
- No se activó modo semántico, no se consultó Pinecone y no se cambió el default BM25.

