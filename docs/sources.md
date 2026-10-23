# Fuentes y alcance de la verificación

Consultadas para el plan el 21/10/2026. Las URLs main externas pueden cambiar; registrar versiones reales al instalar.

- Consigna: https://github.com/gusjrivas/PLN3_GJR/blob/1f4cdbb37f59a049ef9b35c482ccb1de850fbc43/Teoria1/Clase1_PLN3.pdf — pp.4-5 evaluación/proyecto, p.11 preproducción, pp.43-44 ejemplo/métricas.
- Código docente: https://github.com/gusjrivas/PLN3_GJR/tree/1f4cdbb37f59a049ef9b35c482ccb1de850fbc43/Teoria1/Codigo/RAG
- Plantilla: https://github.com/gusjrivas/PLN3_GJR/tree/1f4cdbb37f59a049ef9b35c482ccb1de850fbc43/Teoria1/Codigo/Cookiecutter
- Multiagente: https://github.com/gusjrivas/PLN3_GJR/blob/1f4cdbb37f59a049ef9b35c482ccb1de850fbc43/Teoria3/Codigo/src/agent/agent.py
- OpenSpec: https://github.com/Fission-AI/OpenSpec/blob/main/docs/getting-started.md y https://github.com/Fission-AI/OpenSpec/blob/main/docs/cli.md
- Engram: https://github.com/Gentleman-Programming/engram/blob/main/docs/AGENT-SETUP.md y https://github.com/Gentleman-Programming/engram/blob/main/docs/INSTALLATION.md
- Memoria compartida: https://github.com/Gentleman-Programming/engram/blob/main/docs/TEAM-USAGE.md
- Testing FastAPI: https://fastapi.tiangolo.com/tutorial/testing/
- Testing Streamlit: https://docs.streamlit.io/develop/api-reference/app-testing
- Embeddings candidato: https://huggingface.co/intfloat/multilingual-e5-small — exige prefijos query:/passage: en retrieval.
- Reranker candidato: https://huggingface.co/BAAI/bge-reranker-v2-m3 — multilingüe, evaluar costo CPU.
- Corpus: ver data/corpus/candidates.json y docs/corpus.md.

La revisión del ejemplo fue estática; no se afirma que sus servicios hayan sido ejecutados. El TP no hereda métricas del material de clase. Decisiones de diseño, metas y estimaciones de este paquete son propuestas propias, no requisitos adicionales atribuidos a los docentes.

## Adaptación trazable del código docente

- `raglib/config.py`: su carga de `.env` y variables Pinecone se adapta a
  `src/agro_rag/bootstrap/settings.py` mediante `pydantic-settings`.
- `raglib/vector_pinecone.py::PineconeSearcher`: se adapta en
  `src/agro_rag/infrastructure/pinecone.py`. Conserva el patrón de embeddings, `upsert`, `query` y
  filtros, pero implementa `CandidateRanker`, resuelve IDs contra el catálogo local y verifica
  corpus, modelo, revisión y dimensión mediante un manifiesto remoto.
- `raglib/pipeline.py` y `raglib/fusion.py`: su flujo BM25 + vector + RRF se separa entre los
  contratos puros de `application/retrieval_pipeline.py` y los adaptadores de infraestructura.
- `raglib/reranker.py`: se adapta en `src/agro_rag/infrastructure/reranker.py`, con carga diferida,
  revisión fijada y salida `ScoredId`.
- La creación de índice sólo ocurre con `index-pinecone --create-index`. La carga de modelos sólo
  ocurre al invocar el comando administrativo; no hay red, modelos ni SDK requeridos al importar.
  `clear_namespace` no se incorpora: cada versión usa un namespace nuevo y se rechazan namespaces
  con datos. El manifiesto se publica después de verificar conteo e IDs.
