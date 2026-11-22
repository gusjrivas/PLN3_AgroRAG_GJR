# RET-03-tiktoken-openai

Base `e98e6ab`, rama `feat/openai-tiktoken-context`. Implementación y revisión local por la
misma sesión. El perfil activo se elige desde configuración y deja BM25 y Transformers
disponibles para los perfiles existentes.

- RED. `pytest tests/unit/test_token_counter.py tests/unit/test_retrieval_runtime.py -q` devolvió
  código 1 con cinco fallos por ausencia del adaptador y de su integración.
- GREEN. La misma selección terminó con código 0 y 17 pruebas aprobadas. Cubre texto literal,
  caché ausente o corrupta, proveedor incompatible y selección del contador en el runtime.
- Regresión. Suite offline y Chromium con 348 aprobadas, cinco omitidas y una deseleccionada.
  Las dos últimas variantes de configuración se verificaron en la suite focal de 17 pruebas.
  Ruff, formato, mypy, OpenSpec estricto y revisión de diferencias aprobados.
- Caché real. Se preparó `o200k_base` con `tiktoken 0.14.0`. La carga en modo local y el conteo de
  una muestra con texto especial coincidieron con el tokenizer de GPT-4o, bloqueando
  la función de descarga durante la comprobación del adaptador.

## Consulta real

Se arrancó Uvicorn con la factory normal y `AGRO_RETRIEVAL_MODE=hybrid_rerank`,
`AGRO_RETRIEVAL_TOKENIZER_BACKEND=tiktoken`, `AGRO_OPENAI_MODEL=gpt-4o` y recursos locales
preparados. Se mantuvieron los modelos E5 y CrossEncoder fijados, el corpus `e9929440…` y el
namespace Pinecone compatible.

`POST /v1/query` devolvió HTTP 200 en **43,28 s** para la consulta sobre el rendimiento de la
lechuga a 1,4 dS/m. Informó una caída potencial del 10 %, con cita a INTA Lechuga 2022, página 28.
El endpoint de evidencia devolvió HTTP 200. El verificador aprobó en la primera pasada. El
proveedor informó dos llamadas, 4.441 tokens de entrada y 115 de salida. Request ID
`b7386395-48bc-415b-a9a8-3c4723390ea3`. Una consulta comprueba integración y procedencia.
