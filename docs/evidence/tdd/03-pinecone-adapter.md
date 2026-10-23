# Evidencia TDD: adaptador docente Pinecone/E5

Fecha: 23/10/2026. Responsable y revisión: coordinador/RAG, misma sesión. Rama:
`feat/pinecone-adapter`. Base docente leída sin modificar:
`C:/Repo/PLN3_GJR/Teoria1/Codigo/RAG`, commit
`1f4cdbb37f59a049ef9b35c482ccb1de850fbc43`.

## Alcance y trazabilidad

Se adaptaron `raglib/vector_pinecone.py`, `pipeline.py`, `fusion.py` y `reranker.py` a los
contratos existentes del proyecto. El resultado separa `E5Embedder`, `PineconeVectorRanker` y
`CrossEncoderReranker`; carga SDK/modelos sólo desde bootstrap administrativo, usa IDs del
catálogo local, namespaces nuevos y un manifiesto verificable. No se copió `clear_namespace` ni la
creación automática al arrancar.

Archivos de comportamiento: `src/agro_rag/infrastructure/pinecone.py`,
`src/agro_rag/infrastructure/reranker.py`, `src/agro_rag/bootstrap/cli.py` y
`src/agro_rag/bootstrap/settings.py`. Pruebas: `tests/unit/test_pinecone.py` y
`tests/unit/test_reranker.py`.

## RED observado

- `python -m pytest tests/unit/test_pinecone.py -q`: 7 fallos porque el módulo del adaptador no
  existía.
- Pruebas del comando administrativo: 2 fallos antes de agregar settings y `index-pinecone`; una
  prueba se aisló del `.env` local para que no dependiera de la credencial real.
- Salida NumPy del modelo: el test falló porque `ndarray` no satisface `Sequence`; se agregó una
  normalización explícita sin truncar vectores.
- `python -m pytest tests/unit/test_reranker.py -q`: 3 fallos porque el adaptador CrossEncoder no
  existía.
- Creación segura: el escenario falló hasta exigir `create_if_missing`; por defecto un índice
  ausente produce error y no crea recursos.
- Verificación asíncrona: el escenario `does_not_publish_manifest_until_all_ids_are_visible`
  falló inicialmente con `TypeError` por ausencia de `verification_timeout`. La implementación
  posterior espera conteo e IDs y no publica el manifiesto si no puede verificarlos.
- El escenario `checks_existing_index_before_loading_model` falló porque el CLI cargaba E5 antes
  de comprobar un índice existente. Se reordenó el bootstrap para fallar temprano sin descargar
  pesos; `--create-index` conserva la carga previa necesaria para obtener la dimensión.

Los rojos fueron funcionales y se observaron antes de sus respectivos cambios. No se guardaron
commits rotos.

## GREEN y refactor

Comandos ejecutados desde la raíz:

```text
.venv\Scripts\python.exe -m pytest tests/unit/test_pinecone.py tests/unit/test_reranker.py tests/unit/test_settings.py -q
19 passed in 0.42s; exit 0

.venv\Scripts\python.exe -m pytest --ignore=tests/contract/test_health.py --ignore=tests/integration/test_corpus.py -q
98 passed, 1 deselected; exit 0

.venv\Scripts\ruff.exe check .
All checks passed; exit 0

.venv\Scripts\ruff.exe format --check .
116 files already formatted; exit 0

.venv\Scripts\mypy.exe src
Success: no issues found in 25 source files; exit 0

.venv\Scripts\lint-imports.exe
2 contracts kept, 0 broken; exit 0

npx --yes @fission-ai/openspec@latest validate 03-retrieval --strict
Change '03-retrieval' is valid; exit 0
```

`uv.lock` fue regenerado con el extra opcional `semantic`: `pinecone>=10,<11` y
`sentence-transformers>=5.1,<6`. Los modelos se fijan también por revisión. Las pruebas unitarias
no descargan pesos ni realizan llamadas de red.

## Suite completa y límites conocidos

`python -m pytest -q` produjo `101 passed, 12 failed, 1 deselected` en Windows. Los fallos no
tocan este corte: `tests/contract/test_health.py` reemplaza globalmente `socket.socket.connect` y
bloquea el socket interno de AnyIO; `tests/integration/test_corpus.py` mantiene un handle SQLite
abierto al ejecutar `os.replace` en Windows. Se registran, no se presentan como aprobados ni se
modifican dentro de este alcance.

La credencial local fue comprobada sin imprimirla y `.env` permanece ignorado. La cuenta contiene
un índice existente de 1536 dimensiones; no es compatible con E5 small de 384 dimensiones. No se
creó, borró ni escribió ningún recurso remoto. La creación queda detrás de
`index-pinecone --create-index`. `integration_live`, descarga de modelos y benchmark continúan
pendientes; por eso la API pública conserva BM25.

## Revisión

La misma sesión revisó diff, tipos, imports, ausencia de secretos y separación de capas. No hubo un
revisor independiente disponible. Commit final y URL del PR se completan en el handoff del PR; esta
evidencia no afirma integración real ni calidad semántica.
