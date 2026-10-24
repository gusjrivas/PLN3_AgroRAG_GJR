# Evidencia TDD e integración: retrieval semántico dev

Fecha: 23/10/2026. Responsable y revisión: coordinador/RAG, misma sesión. Rama:
`feat/03-retrieval-live-eval`. Dependencia validada: PR #7. La API pública no se modificó.

## Dataset y entorno

- Catálogo: `abfd07d4cee4c423364424a822e95c9840d5c9ab0944f6cbfdf96c91cd8c8d5e`,
  12 evidencias de INTA Huerta 2008 y FAO56 1998.
- Borrador dev: `data/evaluation/retrieval-dev-draft.jsonl`, 8 consultas respondibles.
- SHA-256 exacto del JSONL: `bfe832f33b8683f0680953bba2b215c3e981b05867c30f29a8a7f30d1807d34f`.
- Etiquetas: `codex-draft`, `pending_human`. No son anotación humana ni test final.
- Embedding: `intfloat/multilingual-e5-small`, revisión
  `614241f622f53c4eeff9890bdc4f31cfecc418b3`, dimensión 384.
- Reranker: `BAAI/bge-reranker-v2-m3`, revisión
  `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`.
- Pinecone: índice `pln3-agrorag-e5-384`, namespace aislado
  `corpus-abfd07d4cee4c423-v2`, 12 chunks + 1 manifiesto.

Los modelos se ejecutaron en CPU. Las latencias siguientes excluyen carga inicial de modelos y
corresponden a una sola pasada; no satisfacen todavía el protocolo de tres pasadas fría/caliente.

## TDD

RED observados:

- `test_retrieval_metrics.py`: 3 fallos `ModuleNotFoundError` antes del módulo de métricas.
- Carga de qrels: 4 fallos por ausencia de `load_cases`.
- Runner: fallo por ausencia de `run_benchmark`; resumen de latencia: fallo por ausencia de
  `BenchmarkRun.latency`.
- Pipeline evaluable: fallo por ausencia de `corpus_version`/`rank` sin tokenizer.
- API actual de Sentence Transformers: fallo al invocar el método de dimensión deprecado.
- Integración real: Pinecone devolvió 400 porque el vector centinela del manifiesto era todo cero.
  El test unitario se cambió primero para exigir un vector unitario no nulo y falló contra la
  implementación anterior.

GREEN:

```text
.venv\Scripts\python.exe -m pytest tests/unit/test_retrieval_metrics.py -q
8 passed; exit 0

.venv\Scripts\python.exe -m pytest tests/unit/test_retrieval_pipeline.py tests/unit/test_retrieval_metrics.py -q
48 passed; exit 0

.venv\Scripts\python.exe -m pytest tests/unit/test_pinecone.py -q
13 passed; exit 0

PINECONE_NAMESPACE=corpus-abfd07d4cee4c423-v2 pytest -m integration_live tests/integration_live/test_pinecone_live.py -q
1 passed in 19.46s; exit 0
```

REFACTOR:

```text
.venv\Scripts\python.exe -m pytest -q
125 passed, 2 deselected (e2e e integration_live); exit 0

.venv\Scripts\ruff.exe check .
All checks passed; exit 0

.venv\Scripts\ruff.exe format --check .
122 files already formatted; exit 0

.venv\Scripts\mypy.exe src
Success: no issues found in 27 source files; exit 0

.venv\Scripts\lint-imports.exe
2 contracts kept, 0 broken; exit 0

npx --yes @fission-ai/openspec@latest validate 03-retrieval --strict
Change '03-retrieval' is valid; exit 0
```

La configuración de pytest se corrigió para excluir `integration_live` de la suite rápida; el job
real se ejecuta sólo con selección explícita y secretos locales.

El manifiesto usa ahora un vector unitario determinista; el filtro `kind=chunk` lo excluye de toda
consulta. El primer intento dejó 12 chunks sin manifiesto. Se verificó exactamente ese estado, se
indexó `v2`, se comprobó `12 + 1` y se eliminó únicamente el namespace parcial. La verificación
posterior mostró un solo namespace: `v2` con 13 vectores.

## Resultados provisionales

Métricas macro binarias sobre 8 consultas:

| Modo | MRR@10 | Recall@1 | Recall@5 | nDCG@10 |
|---|---:|---:|---:|---:|
| BM25 | 0,6875 | 0,625 | 0,750 | 0,7039 |
| Vector E5 | 0,8438 | 0,750 | 1,000 | 0,8827 |
| Hybrid RRF | 0,8958 | 0,875 | 0,875 | 0,9195 |
| Hybrid + BGE reranker | 1,0000 | 1,000 | 1,000 | 1,0000 |

Latencia por consulta, modelos ya cargados:

| Modo | media ms | p50 ms | p95 ms |
|---|---:|---:|---:|
| BM25 | 0,31 | 0,08 | 1,25 |
| Vector E5 + Pinecone | 205,48 | 207,75 | 233,23 |
| Hybrid RRF | 199,66 | 176,60 | 268,01 |
| Hybrid + BGE reranker CPU | 26169,41 | 27949,40 | 30559,45 |

El reranker supera el objetivo p95 de 30 s sólo en retrieval y el conjunto es pequeño, obvio y no
revisado por una persona. El resultado perfecto no se generaliza ni autoriza activación. RRF mejora
MRR/nDCG frente a vector, pero reduce Recall@5 de 1,0 a 0,875 en este borrador; se conserva el
resultado negativo.

## Puertas restantes

- Revisión humana de qrels y ampliación hacia el protocolo de 60 casos/splits.
- Tres pasadas fría/caliente con manifiesto de hardware y artefactos JSON/CSV.
- Tokenizer exacto del generador, deadline/worker para SDK y CPU, y propagación API de errores.
- Decisión documentada sobre costo/latencia del reranker; la API permanece en BM25.

La credencial se leyó desde `.env` ignorado y nunca se imprimió. No se modificó el índice heredado
`grivas` de 1536 dimensiones.
