# Corpus y procedencia

## Alcance inicial

Tomate, lechuga y fundamentos de agua/suelo/riego. Admitir secciones generales necesarias para explicar términos, no convertir todo un manual de horticultura en permiso para asesorar sobre pesticidas o cualquier cultivo. El documento de FAO en inglés se consulta desde preguntas en español con modelos multilingües. Registrar edición de forma explícita y no afirmar que 1998 es la última.

| ID | Fuente | Estado de investigación | Selección inicial |
|---|---|---|---|
| INTA-HUERTA-2008 | Manual de cultivos para la huerta orgánica familiar, Enrique Goites | Ingerido con hash fijado | Lechuga, tomate y períodos críticos |
| FAO56-1998 | Crop evapotranspiration, Allen et al. | Ingerido con hash fijado | Evaporación, transpiración y agua disponible |
| INTA-RIEGO-HORTICOLAS-2024 | Riego en cultivos hortícolas, Ferrari y Aguado | Ingerido con hash fijado | Agua disponible, programación y establecimiento |
| INTA-LECHUGA-2022 | Lechuga, Lopez Bilbao y Frezza | Ingerido con hash fijado | Suelo, salinidad, exceso de agua y programación |
| INTA-TOMATE-2020 | Recomendaciones generales para cultivar hortalizas: tomate, Gaitán y Carrizo | Ingerido con hash fijado | Frecuencia, floración y cuajado |

URLs, hashes y estado machine-readable están en `data/manifest.json`; `data/corpus/candidates.json`
conserva el resultado de la investigación de fuentes. Los cinco PDF se descargan desde repositorios
institucionales, pero no se versionan. Revisar derechos antes de redistribuir: acceso público no
equivale a permiso para subir copias a Git.

## Manifiesto de ingesta

source_id, title, authors, institution, edition/year, language, source_url, access_date, local_file, sha256, rights_status, selected_pdf_pages, printed_page_map, extraction_version, review_status. Ningún hash se inventa; valores faltantes bloquean admisión. Anotar páginas omitidas/escaneadas, tablas reconstruidas y OCR si se usa.

## Modelo de fragmento

source_id identifica el archivo/obra; page_id identifica página física; evidence_id identifica un pasaje inmutable de una corpus_version. No reutilizar doc_id ambiguo del ejemplo como fuente y página a la vez. Conservar texto original, texto limpio y offsets o referencia verificable. IDs derivan de contenido/procedencia/configuración estable.

## Extracción y control

Muestrear todas las tablas utilizadas en respuestas de referencia y páginas seleccionadas para tomate/lechuga. Tabla reconstruida conserva encabezados, unidad, fila y condiciones en cada registro textual, más página original y nota de transformación. Evitar que números se desprendan de la unidad. PDFs escaneados sin extracción se rechazan con diagnóstico; OCR es ampliación explícita.

Chunking inicial: ventanas de ~200 tokens léxicos y overlap ~60 como baseline docente. Medir tokens reales del modelo y respetar sus límites. Comparar otra configuración en dev antes de fijar. No partir condiciones o tablas sin conservar contexto. El hash del corpus y configuración cambia si cambia la extracción o el chunking.

## Baseline docente

Fuente de código: Teoria1/Codigo/RAG al commit 1f4cdbb37f59a049ef9b35c482ccb1de850fbc43. Conservar atribución y registrar qué módulos se adaptaron. No mezclar sus papers de RAG y qrels de muestra con el corpus/evaluación agronómicos.

## Corpus descargado e implementado

La selección efectiva está en `data/manifest.json`. El primer corte incluía INTA Huerta y FAO56,
con 12 fragmentos. La ampliación agrega tres publicaciones INTA y produce 27 fragmentos en total:
fundamentos de agua disponible y evapotranspiración, programación y monitoreo, establecimiento,
salinidad y exceso de agua en lechuga, y períodos críticos de tomate. Página física e impresa son
campos diferentes. La versión resultante es
`e9929440f552b1c7be1349118a1ee98c6cdba41fbd2e2ce05343247c918dfb7d`. Ver
`docs/evidence/tdd/02-corpus.md` y `docs/evidence/tdd/COR-EXP-01.md`.

```bash
uv run agro-rag download data/manifest.json
uv run agro-rag ingest data/manifest.json --output data/processed/catalogue
```

La descarga se realiza sólo mediante CLI administrativa, con hashes fijados y dominios institucionales permitidos. No se aceptan URLs de usuarios por API. Si un archivo publicado cambia, el comando falla: revisar nueva edición y actualizar el manifiesto antes de admitirlo.
