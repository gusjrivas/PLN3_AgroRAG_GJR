# Corpus y procedencia

## Alcance inicial

Tomate, lechuga y fundamentos de agua/suelo/riego. Admitir secciones generales necesarias para explicar términos, no convertir todo un manual de horticultura en permiso para asesorar sobre pesticidas o cualquier cultivo. El documento de FAO en inglés se consulta desde preguntas en español con modelos multilingües. Registrar edición de forma explícita y no afirmar que 1998 es la última.

| ID | Fuente | Estado de investigación | Selección inicial |
|---|---|---|---|
| INTA-HUERTA-2008 | Manual de cultivos para la huerta orgánica familiar, Enrique Goites | PDF accesible verificado en investigación; no descargado/indexado para este TP | Lechuga p. impresa 67, tomate p.97 y anexo p.129; confirmar páginas físicas al ingerir |
| FAO56-1998 | Crop evapotranspiration, Allen et al. | Contenido oficial web verificado; seleccionar PDF con edición/correcciones documentadas | Conceptos y capítulos 5, 6 y 8, otras secciones sólo si aportan a preguntas del alcance |
| INTA-RIEGO-2009 | Riego en horticultura, Villafáfila y Wyss | Ficha FAO identificada; descarga pendiente | Diseño/instalación de pequeños sistemas de riego |

URLs y estado machine-readable en data/corpus/candidates.json. No son tres PDFs ya disponibles en el repositorio. Si la tercera fuente no se obtiene, el MVP puede funcionar con dos fuentes y declarar la limitación. Revisar licencias antes de redistribuir; acceso público no equivale a permiso para subir copias a Git.

## Manifiesto de ingesta

source_id, title, authors, institution, edition/year, language, source_url, access_date, local_file, sha256, rights_status, selected_pdf_pages, printed_page_map, extraction_version, review_status. Ningún hash se inventa; valores faltantes bloquean admisión. Anotar páginas omitidas/escaneadas, tablas reconstruidas y OCR si se usa.

## Modelo de fragmento

source_id identifica el archivo/obra; page_id identifica página física; evidence_id identifica un pasaje inmutable de una corpus_version. No reutilizar doc_id ambiguo del ejemplo como fuente y página a la vez. Conservar texto original, texto limpio y offsets o referencia verificable. IDs derivan de contenido/procedencia/configuración estable.

## Extracción y control

Muestrear todas las tablas utilizadas en respuestas de referencia y páginas seleccionadas para tomate/lechuga. Tabla reconstruida conserva encabezados, unidad, fila y condiciones en cada registro textual, más página original y nota de transformación. Evitar que números se desprendan de la unidad. PDFs escaneados sin extracción se rechazan con diagnóstico; OCR es ampliación explícita.

Chunking inicial: ventanas de ~200 tokens léxicos y overlap ~60 como baseline docente. Medir tokens reales del modelo y respetar sus límites. Comparar otra configuración en dev antes de fijar. No partir condiciones o tablas sin conservar contexto. El hash del corpus y configuración cambia si cambia la extracción o el chunking.

## Baseline docente

Fuente de código: Teoria1/Codigo/RAG al commit 1f4cdbb37f59a049ef9b35c482ccb1de850fbc43. Conservar atribución y registrar qué módulos se adaptaron. No mezclar sus papers de RAG y qrels de muestra con el corpus/evaluación agronómicos.

## Primer corpus descargado e implementado

La selección piloto efectiva está en `data/manifest.json`; reemplaza el estado de investigación de la tabla anterior para las dos fuentes descargadas. INTA: PDF 69, 72, 103 y dos filas de 131. FAO: PDF 27, 29 y sección final de 187. Resultado inicial: 12 fragmentos. Página física e impresa son campos diferentes. Ver docs/evidence/tdd/02-corpus.md.

```bash
uv run agro-rag download data/manifest.json
uv run agro-rag ingest data/manifest.json --output data/processed/catalogue
```

La descarga se realiza sólo mediante CLI administrativa, con hashes fijados y dominios institucionales permitidos. No se aceptan URLs de usuarios por API. Si un archivo publicado cambia, el comando falla: revisar nueva edición y actualizar el manifiesto antes de admitirlo.
