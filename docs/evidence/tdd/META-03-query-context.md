# META-03 — contexto, caché y suficiencia

Fecha: 2026-11-09. Rama: `feat/meta-03-query-context`.
Base: `471aa420a696b68c64addca429f2613a82d9ebde`. Issue: #46.
Responsable: agente META-03, coordinado por Gustavo Julián Rivas.

## Alcance y caracterización

El corte modifica el schema de contexto y la orquestación de consulta, junto con sus pruebas
unitarias y de contrato. No modifica adaptadores de retrieval, Pinecone, bootstrap, corpus,
manifiestos ni `Teoria*`.

Caracterización previa:

```text
python -m pytest tests/unit/test_query.py tests/contract/test_query_api.py -q
# exit 0: 47 passed, 1 warning
```

Antes de META-03, la API no admitía `region`, `QueryService` enviaba sólo `crop` a retrieval, la
clave LRU era `(corpus_version, pregunta_normalizada, crop)` y los agentes recibían evidencia sin
los metadatos curados nuevos.

## RED

Se escribieron primero los escenarios observables del test-plan:

- región y etapa llegan como `RetrievalFilters` y separan entradas de caché;
- una recomendación situacional con región ausente aclara sin invocar al modelo;
- contexto completo sin evidencia compatible termina en `insufficient_evidence`;
- una pregunta documental general continúa sin exigir región o etapa;
- investigador y verificador reciben metadata relevante junto con ID y texto;
- el contrato HTTP acepta únicamente los vocabularios controlados.

```text
python -m pytest tests/unit/test_query.py tests/contract/test_query_api.py -q
# exit 1: 6 failed, 47 passed, 3 warnings
```

Los seis fallos fueron funcionales: se observó `crop` en lugar de `RetrievalFilters`, una sola
llamada para etapas diferentes, llamada indebida al LLM cuando faltaba región, ausencia de metadata
en los payloads y rechazo/aceptación incorrectos en el schema HTTP.

Salvedad de trazabilidad: esa primera corrida se inició desde el worktree asignado, pero el entorno
Python resolvió el paquete editable en `C:\Repo\PLN3_AgroRAG_GJR\src`, que estaba en la misma base
sin META-03. Los tests sí eran los recién escritos en el worktree. El fallo funcional es real, pero
no se reconstruyó retroactivamente otra fase roja. Desde GREEN se fijó `PYTHONPATH` al `src` del
worktree para eliminar la ambigüedad.

No se usaron red, modelos ni proveedores live.

## GREEN

Se agregó `region` al contexto HTTP y se tiparon `growth_stage` y `region` con los vocabularios del
dominio. `QueryService` ahora construye un `RetrievalFilters` inmutable, usa crop/etapa/región en la
clave de caché y lo entrega al retriever. Las recomendaciones situacionales requieren etapa,
región y descripción del suelo; las preguntas documentales generales conservan el flujo normal.
Sin evidencia compatible se abstiene antes de generar. El contexto de investigador/verificador
incluye `crop`, `source_type`, `growth_stages`, `applicable_regions` y `applicability`, sin tratar
estos metadatos como evidencia factual.

```text
$env:PYTHONPATH=(Join-Path (Get-Location) 'src')
python -m pytest tests/unit/test_query.py tests/contract/test_query_api.py -q
# exit 0: 53 passed, 2 warnings
```

El coordinador repitió independientemente la suite focal con `PYTHONPATH` del worktree y un
`--basetemp` local escribible: exit 0, `53 passed`.

## Corrección UI: filtros estructurados de extremo a extremo

La revisión posterior detectó que la UI todavía exponía `growth_stage` como texto libre y no
permitía ingresar `region`. Antes de modificar el frontend se agregaron dos escenarios AppTest:
la consulta verificada debe mapear etiquetas legibles a valores HTTP controlados, y un reenvío de
aclaración debe conservar etapa y región sin importar módulos de backend.

```text
$env:PYTHONPATH=(Join-Path (Get-Location) 'src')
python -m pytest tests/ui/test_ui.py -q -p no:cacheprovider -k "controlled_growth_stage_and_region"
# RED, exit 1: 2 failed, 10 deselected
```

Ambos fallos fueron funcionales y terminaron en `StopIteration`: no existían los selectores
`Etapa del cultivo (opcional)` y `Región (opcional)`. Se reemplazó el texto libre de etapa por un
selector y se agregó el selector de región. Los mapeos viven en `agro_rag_ui` y sólo producen el
JSON de `ApiClient`; la UI no importa schemas, dominio, retrieval ni agentes del backend.

Etiquetas de etapa: Implantación, Crecimiento vegetativo, Floración, Cuajado de frutos, Desarrollo
de frutos y Pre-cosecha. Valores HTTP: `establishment`, `vegetative_growth`, `flowering`,
`fruit_set`, `fruit_development` y `pre_harvest`. La región inicial visible es Oasis Norte de
Mendoza (Argentina), enviada como `ar-mendoza-oasis-norte`. “Sin especificar” omite el campo.

```text
$env:PYTHONPATH=(Join-Path (Get-Location) 'src')
python -m pytest tests/ui/test_ui.py -q -p no:cacheprovider -k "controlled_growth_stage_and_region"
# GREEN, exit 0: 2 passed, 10 deselected
```

La aclaración reutiliza `submitted_context`; el test comprueba que la segunda llamada conserva
exactamente `growth_stage=fruit_development` y `region=ar-mendoza-oasis-norte`, agregando sólo las
respuestas de `clarification_context`.

## REFACTOR y regresión

Controles ejecutados por esta sesión:

```text
$env:PYTHONPATH=(Join-Path (Get-Location) 'src')
python -m ruff check src/agro_rag/api/schemas.py src/agro_rag/api/query.py src/agro_rag/application/query.py tests/unit/test_query.py tests/contract/test_query_api.py
# exit 0: All checks passed!

python -m mypy src
# exit 0: Success: no issues found in 38 source files
```

Ruff format detectó un ajuste mecánico en `application/query.py`; se aplicó con
`python -m ruff format`. Un intento de suite afectada dentro del sandbox terminó con `218 passed,
1 skipped, 47 errors`: los 47 fueron errores de setup por `PermissionError` al crear
`C:\Users\gusta\AppData\Local\Temp\pytest-of-gustavo.rivas`, no fallos de comportamiento. El
coordinador repitió la suite completa con `PYTHONPATH` del worktree y `--basetemp` local escribible:

```text
python -m pytest -q --basetemp .pytest-tmp-meta03-full -p no:cacheprovider
# exit 0: 335 passed, 1 skipped, 3 deselected, 1 warning
```

El skip de Windows corresponde a bits POSIX del runner Garak y la advertencia es la deprecación
externa conocida de Starlette TestClient/httpx.

Después de la corrección UI, la verificación independiente del coordinador usó explícitamente el
`PYTHONPATH` del worktree, desactivó `cacheprovider` y fijó temporales escribibles:

```text
$env:PYTHONPATH='<worktree-meta03>\src'
python -m pytest tests/ui/test_ui.py tests/unit/test_query.py tests/contract/test_query_api.py -q -p no:cacheprovider --basetemp C:\Repo\PLN3_AgroRAG_GJR\.tmp-meta03-ui-focus
# exit 0: 65 passed, 1 warning

python -m pytest -q -p no:cacheprovider --basetemp C:\Repo\PLN3_AgroRAG_GJR\.tmp-meta03-ui-full
# exit 0: 337 passed, 1 skipped, 3 deselected, 1 warning
```

Controles finales de la corrección:

```text
python -m ruff check src/agro_rag_ui/app.py src/agro_rag/api/schemas.py src/agro_rag/application/query.py tests/ui/test_ui.py tests/unit/test_query.py tests/contract/test_query_api.py
# exit 0: All checks passed!

python -m ruff format --check src/agro_rag_ui/app.py src/agro_rag/api/schemas.py src/agro_rag/application/query.py tests/ui/test_ui.py tests/unit/test_query.py tests/contract/test_query_api.py
# exit 0: 6 files already formatted

python -m mypy src
# exit 0: Success: no issues found in 38 source files

git diff --check
# exit 0
```

## Estado de entrega

- Sin commit ni push: la integración corresponde al coordinador.
- El schema público de respuesta, citas, errores HTTP tipados y auditoría redactada permanecen
  intactos; los nuevos cierres deterministas conservan `usage`, `cache_hit` y evento de auditoría.
- Verificación independiente de tests completada por el coordinador; revisión semántica final del
  diff permanece a cargo de integración.
- Validación exclusivamente offline con dobles; no demuestra calidad agronómica ni comportamiento
  de un modelo o índice remoto real.
