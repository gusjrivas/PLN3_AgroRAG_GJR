# 03: activación runtime explícita de retrieval semántico

Fecha: 27-28/10/2026. Responsable y revisión: misma sesión Codex; revisión humana pendiente. Rama:
`feat/semantic-runtime-activation`. Base integrada: `cb558f4`. Propiedad: bootstrap de retrieval, tokenizer,
settings, ensamblado API/UI, pruebas y documentación de 03. No se usaron secretos ni proveedores
pagos.

## RED

1. Runtime y tokenizer ausentes:

   `.venv\Scripts\python.exe -m pytest -q tests/unit/test_retrieval_runtime.py tests/unit/test_token_counter.py`

   Salida 1: `10 failed`; ambos módulos nuevos faltaban.

2. Integración/observabilidad ausentes:

   `.venv\Scripts\python.exe -m pytest -q tests/contract/test_query_api.py::test_configured_retrieval_runtime_is_disclosed_and_closed tests/unit/test_query.py::test_response_limitations_disclose_configured_retrieval_mode`

   Salida 1: `2 failed`; bootstrap no componía el runtime y `QueryService` no aceptaba el modo.

3. La UI confundía un preview semántico con una respuesta generada:

   `.venv\Scripts\python.exe -m pytest -q tests/ui/test_ui.py::test_semantic_preview_is_rendered_as_evidence_not_as_generated_answer`

   Salida 1: `1 failed`; la evidencia no se mostraba.

## GREEN

Se añadió composición explícita de BM25/vector/hybrid/hybrid_rerank. BM25 no inicializa modelos ni
red. Los modos semánticos requieren secreto, índice con manifiesto compatible y tokenizer con modelo
y revisión fijados; no descargan archivos por default. El pipeline conserva fallo operativo sin
fallback, límites de contexto y cierre idempotente del handle Pinecone.

Comando focalizado final:

`.venv\Scripts\python.exe -m pytest -q tests/contract/test_query_api.py tests/unit/test_query.py tests/ui/test_ui.py tests/unit/test_retrieval_runtime.py tests/unit/test_token_counter.py tests/unit/test_retrieval_pipeline.py`

Salida 0: `92 passed`.

## REFACTOR y límites

Mypy detectó dos incompatibilidades de typing durante refactor: propiedad read-only de
`corpus_version` y narrowing del runtime. Se corrigieron antes de continuar. El PDF actualizado se
renderizó en siete páginas y se inspeccionó completo; se eliminó un salto que dejaba una página casi
vacía.

Comandos de cierre:

- `.venv\Scripts\python.exe -m pytest`: salida 0, `184 passed, 2 deselected`; cobertura global
  `88.18%`, por encima del mínimo 85%.
- `.venv\Scripts\ruff.exe check .` y `.venv\Scripts\ruff.exe format --check .`: salida 0.
- `.venv\Scripts\mypy.exe src`: salida 0, 36 archivos sin errores.
- `.venv\Scripts\lint-imports.exe`: salida 0, dos contratos mantenidos.
- `npx --yes @fission-ai/openspec@1.14.3 validate --all --strict`: salida 0, siete cambios válidos.
- `.venv\Scripts\agro-rag.exe verify-delivery --root .`: salida 0, ocho artefactos verificados.

Commit de implementación: `6d461b4` (`feat: activate configurable semantic retrieval runtime`).

No se declara T.4 ni CAT-04 completos: faltan revisión humana de qrels, activación real de esta
configuración y E1/E2/E3. La prueba usa proveedores inyectados y acredita composición, no calidad.
