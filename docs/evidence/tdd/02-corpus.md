# COR-01/02/03: corpus piloto

Responsable/revisor: misma sesión Codex. Rama feat/02-corpus. Depende de PR #2. La petición del usuario autoriza avanzar el desarrollo; Engram de clientes locales sigue pendiente y no es una dependencia del producto.

## TDD

- RED inicial: 10 escenarios fallan por ausencia de la ingesta, `uv run pytest tests/integration/test_corpus.py -q`, salida 1. Log 02-red.txt.
- GREEN: extracción PDF real con fixtures sintéticas, validación y catálogo pasan los mismos escenarios.
- Endurecimiento: se añadió test rojo para snapshot existente corrupto (no lanzaba excepción) y CLI ausente. Log 02-hardening-red.txt. Se valida el snapshot existente antes de activar y se implementa CLI. Un test adicional de offsets caracteriza el chunker ya implementado, sin atribuirle un rojo inexistente.
- Descarga: 6 tests rojos antes de crear adaptador HTTP. Log 02-download-red.txt. URLs institucionales HTTPS, checksum, PDF y publicación tras validación; sin red real en tests.
- Refactor: modelos de admisión estrictos, Evidence/Catalogue en dominio estándar, SQLite/PDF/HTTP en infraestructura. Evidencia de regresión: 02-green.txt. Revisión propia, sin revisor independiente.

## Corpus real

Descargas efectivas: INTA 140 páginas y FAO 333 páginas. Hashes, selección y procedencia en data/manifest.json. FAO corresponde a copia USDA de 1998 con apéndice de errata y ejemplos corregidos de febrero de 2006; no se presenta como la última edición.

Se revisaron visualmente INTA PDF 131 (impresa 129), 103 (101), 72 (70) y FAO PDF 187 (161). Se contrastó texto extraído de los otros pasajes seleccionados. Las dos filas de tabla incluidas conservan encabezado y cultivo; se excluyen las tablas numéricas/columnas no revisadas, así como instrucciones de plaguicidas y contenidos ajenos al alcance.

`uv run agro-rag ingest data/manifest.json --output data/processed/catalogue` produjo 12 fragmentos; versión a85bec55032f5adea8675749c0cafa71be5ed61664535f93cdf4da9a981a9313. Los documentos y SQLite son locales y no se redistribuyen en Git. El manifiesto permite repetir la descarga, verificando hashes; acceso público no implica licencia de redistribución. Tercera fuente INTA-RIEGO-2009 aún pendiente.

## Límite de esta entrega

La activación corresponde a `catalogue_preview`, un catálogo local para la primera versión incremental. No se declara un índice Pinecone activo ni se completa COR-03 para catálogo+índice remoto. No se archiva 02-corpus. Quedan expansión/revisión de corpus, prueba semántica y evaluación científica.
