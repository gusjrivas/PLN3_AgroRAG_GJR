# Compatibilidad del corpus sin metadatos curados

Base `3ec2445`, equivalente en contenido a `main` remoto `681bc46` durante la revisión.
Implementación y verificación por la misma sesión. El cambio queda en el árbol local.

La ingesta limpia reproducía 27 pasajes bajo `b9600921…` y el benchmark congelado rechazaba
ese catálogo. La representación usada para calcular el hash incluía los campos nuevos incluso
cuando todos tenían los valores de ausencia de curación. La ingesta recupera la representación
histórica únicamente en ese caso. Un manifiesto con valores curados sigue usando la representación
completa y genera otra identidad.

- RED. `python -m pytest tests/integration/test_corpus.py -k legacy_identity -q` terminó con
  código 1. El hash obtenido difería del hash histórico calculado para el manifiesto de prueba.
- GREEN. `python -m pytest tests/integration/test_corpus.py -q` terminó con código 0 y 33 pruebas
  aprobadas. Los valores por defecto explícitos y omitidos generan el mismo catálogo. Los cambios
  de metadatos curados siguen generando otro snapshot.
- Regresión. `python -m pytest -m 'not integration_live' -q` con Chromium terminó con código 0,
  342 pruebas aprobadas, 2 omitidas y 1 deseleccionada. Ruff, formato, mypy y `git diff --check`
  pasaron.
- Reproducción. Con los cinco PDF descargados en el checkout aislado y las dependencias instaladas
  desde el lock, la ingesta con el código corregido produjo 27 fragmentos y el corpus
  `e9929440f552b1c7be1349118a1ee98c6cdba41fbd2e2ce05343247c918dfb7d`.
  `validate-benchmark data/evaluation/benchmark-60.jsonl` aprobó los 60 casos.
- Pinecone. Las consultas de solo lectura devolvieron el manifiesto del mismo corpus, E5 en la
  revisión fijada y dimensión 384, y los 27 IDs esperados. Queda pendiente la inferencia completa
  con `hybrid_rerank`.
