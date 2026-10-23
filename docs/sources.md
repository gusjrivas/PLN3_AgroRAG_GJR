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
- `raglib/vector_pinecone.py::PineconeSearcher.__post_init__`: se conserva el nombre estándar
  `PINECONE_API_KEY`; la clave pasa a `SecretStr`, se redacta en representaciones y deberá
  inyectarse explícitamente en el adaptador real.
- La creación de índice, carga de modelos y `clear_namespace` del ejemplo no se ejecutan al
  importar ni al arrancar este proyecto. Su incorporación requiere el corte TDD de adaptadores,
  identidad de índice y namespace aislado definido por ADR-013.
