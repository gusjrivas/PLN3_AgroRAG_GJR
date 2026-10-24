# COR-EXP-01 — ampliación institucional del corpus

Fecha: 24/10/2026. Responsable: coordinador/RAG, misma sesión. Rama:
`feat/corpus-expansion`. Los PDF permanecen fuera de Git y no se redistribuyen.

## Alcance y fuentes admitidas

El manifiesto agrega tres publicaciones oficiales de INTA a las dos fuentes existentes. Todas
usan HTTPS, URL institucional, hash SHA-256 fijado, páginas seleccionadas y estado de revisión.

| Fuente | SHA-256 | Selección curada |
|---|---|---|
| INTA-RIEGO-HORTICOLAS-2024 | `f8df19fe730b0e45a64bb2b0a17343b7584fbe803a6aa83d1524dad4d86dd1be` | agua disponible, evapotranspiración, programación y establecimiento |
| INTA-LECHUGA-2022 | `680b21d67b74a658be1c34f0c48502906a4a2ca4f33e84754b508e2f346679f9` | suelo, salinidad, cobertura, exceso de agua y programación |
| INTA-TOMATE-2020 | `13639481884578ab7215da55fa5810e034595d811cff859420e7f879e97eff36` | frecuencia, período crítico, floración y cuajado |

El estado `public_access_no_redistribution` evita confundir acceso público con permiso de
redistribución. La descarga administrativa mantiene lista cerrada de hosts, rechaza redirects y
valida el contenido contra el hash antes de admitirlo.

## RED

Comando focal inicial:

```powershell
$env:PYTHONPATH=(Resolve-Path 'src').Path
..\..\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --tb=short `
  --basetemp=.tmp\corpus-expand-red `
  tests/integration/test_download.py::test_inta_repository_is_an_allowed_institutional_source `
  tests/integration/test_corpus.py::test_curated_manifest_expands_irrigation_coverage
```

Resultado: código 1, `2 failed`. El host `repositorio.inta.gob.ar` todavía no estaba admitido y el
manifiesto sólo contenía las dos fuentes iniciales.

La primera ingesta real expuso además que Windows leía el manifiesto UTF-8 con la codificación del
sistema y alteraba marcadores con acentos. La prueba
`test_utf8_manifest_markers_are_preserved_on_windows` falló mostrando texto mojibake.

Finalmente, repetir el comando documentado con `--output data/processed/catalogue` falló sobre el
snapshot existente porque `Path.as_uri()` no acepta una ruta relativa. Se agregó
`test_repeated_ingest_accepts_documented_relative_output`; RED: código 1 con
`ValueError: relative path can't be expressed as a file URI`.

## GREEN y REFACTOR

Se admitió exclusivamente `repositorio.inta.gob.ar`, se incorporaron las selecciones revisadas y
se hizo explícita la lectura UTF-8. Para conservar la idempotencia con la ruta documentada,
`read_snapshot` resuelve la ruta antes de construir el URI SQLite.

Resultados finales:

```text
pytest: 169 passed, 2 deselected; código 0
ruff check: All checks passed; código 0
ruff format --check: 56 files already formatted; código 0
mypy: Success, 34 source files; código 0
import-linter: 2 contracts kept, 0 broken; código 0
openspec validate 02-corpus --strict: valid; código 0
verify-delivery: 8 artefactos verificados; código 0
```

La descarga idempotente informó `{"sources": 5}`. La ingesta repetida produjo:

```json
{"version":"e9929440f552b1c7be1349118a1ee98c6cdba41fbd2e2ce05343247c918dfb7d","evidence_count":27}
```

Un smoke lexical local recuperó pasajes nuevos para seis intenciones: textura y agua disponible,
frecuencia de tomate, susceptibilidad de lechuga al déficit, exceso de riego, lámina/programación
en lechuga y monitoreo del riego. Este smoke comprueba descubrimiento, no relevancia científica:
los qrels anteriores corresponden al corpus de 12 evidencias y deben regenerarse con revisión
humana para esta nueva versión.

No se consultaron LLM ni servicios pagos durante la suite. La revisión final fue realizada por la
misma sesión; no hubo un revisor independiente disponible bajo las restricciones de ejecución.
