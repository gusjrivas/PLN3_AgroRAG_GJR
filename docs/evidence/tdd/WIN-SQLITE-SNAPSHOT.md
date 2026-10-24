# Evidencia TDD: portabilidad Windows de snapshots SQLite

Fecha: 23/10/2026. Responsable y revisión: coordinador/RAG, misma sesión. Rama:
`fix/windows-sqlite-snapshot`. Este corte desbloquea la reconstrucción local del corpus necesaria
para `03-retrieval/P.6`; no cambia el formato ni la identidad de los snapshots.

## RED observado

La descarga fijada por `data/manifest.json` completó dos fuentes y verificó sus hashes. La ingesta
real falló al activar el snapshot:

```text
.venv\Scripts\agro-rag.exe ingest data/manifest.json --output data/processed/catalogue
PermissionError: [WinError 32] ... catalogue.sqlite
exit 1
```

El mismo defecto se reprodujo de forma determinista con el fixture existente:

```text
.venv\Scripts\python.exe -m pytest tests/integration/test_corpus.py::test_cli_ingest_and_read_snapshot -q
1 failed; PermissionError [WinError 32] en os.replace; exit 1
```

La suite completa también tenía un fallo independiente de portabilidad en
`test_liveness_works_without_credentials_or_network`: reemplazar globalmente
`socket.socket.connect` interceptaba el socketpair interno que AnyIO necesita en Windows, antes de
que la aplicación pudiera responder.

## GREEN

`sqlite3.Connection` hace commit/rollback en su context manager pero no cierra el handle. Se agregó
`contextlib.closing` tanto en escritura como lectura; así el archivo queda cerrado antes de
`os.replace` o de limpiar el directorio temporal. El test de liveness ahora intercepta solamente
`httpx.AsyncClient.send`, que es el transporte de proveedor que la aserción pretende prohibir.

```text
.venv\Scripts\python.exe -m pytest tests/integration/test_corpus.py::test_cli_ingest_and_read_snapshot -q
1 passed; exit 0

.venv\Scripts\python.exe -m pytest tests/integration/test_corpus.py -q
14 passed; exit 0

.venv\Scripts\python.exe -m pytest tests/contract/test_health.py -q
2 passed; exit 0
```

La ingesta real posterior completó sin alterar archivos versionados ni publicar los PDFs:

```text
.venv\Scripts\agro-rag.exe ingest data/manifest.json --output data/processed/catalogue
version=abfd07d4cee4c423364424a822e95c9840d5c9ab0944f6cbfdf96c91cd8c8d5e
evidence_count=12; exit 0
```

## REFACTOR y límites

```text
.venv\Scripts\python.exe -m pytest -q
114 passed, 1 integration_live deselected; exit 0

.venv\Scripts\ruff.exe check .
All checks passed; exit 0

.venv\Scripts\ruff.exe format --check .
117 files already formatted; exit 0

.venv\Scripts\mypy.exe src
Success: no issues found in 25 source files; exit 0

.venv\Scripts\lint-imports.exe
2 contracts kept, 0 broken; exit 0

npx --yes @fission-ai/openspec@latest validate 02-corpus --strict
Change '02-corpus' is valid; exit 0
```

La advertencia de deprecación Starlette/httpx continúa fuera de este alcance. Los PDFs y el
catálogo generado permanecen ignorados por Git. No se usó ni imprimió ninguna credencial. No hubo
un revisor independiente disponible; la misma sesión revisó el diff y ejecutó los gates.
Commit de implementación y evidencia: `eb1cd64`.
