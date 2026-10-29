# Protocolo de evaluación preregistrado propuesto

Objetivo: medir aporte de recuperación híbrida/reranking y del verificador en español. No se prometen mejoras. Todo valor de esta sección es diseño experimental u objetivo, no resultado obtenido.

## Estado dev al 28/10/2026

Se ejecutó un smoke real de retrieval sobre 8 consultas respondibles y 12 evidencias, documentado
en `docs/evidence/tdd/03-live-eval.md`. Sus qrels están marcados `pending_human`: sirven para
verificar el pipeline y detectar costos/fallos, pero no sustituyen el conjunto de 60 casos ni
autorizan elegir configuración final. La API permanece en BM25.

Las métricas de ese smoke pertenecen a la versión anterior de 12 fragmentos y no se trasladan a la
versión ampliada. `data/evaluation/retrieval-dev-draft.jsonl` fue migrado por correspondencia de
pasajes a las 27 evidencias de la versión
`e9929440f552b1c7be1349118a1ee98c6cdba41fbd2e2ce05343247c918dfb7d`; conserva
`pending_human`. El smoke remoto usa Recall@20 porque la ampliación desplazó pasajes relevantes
sin eliminarlos. Los qrels deben revisarse humanamente antes de comparar configuraciones o
presentar resultados de calidad.

EVA-01 cuenta además con un cargador contractual automatizado: exige exactamente 60 casos
revisados, conserva la proporción 18/6/6 en cada split, impide que una familia cruce dev/test,
resuelve los `evidence_id` contra la versión del catálogo y congela el archivo por SHA-256. Los
36 casos respondibles forman el denominador IR; los otros 24 forman el denominador de
abstención. El borrador se conserva en `data/evaluation/benchmark-60-draft.jsonl`; el usuario cerró
la revisión el 28/10/2026 y el paquete final `data/evaluation/benchmark-60.jsonl` contiene 60 filas
`reviewed`, 30 dev/30 test y 18/6/6 por split. Hubo una sola aceptación humana; no se informa
acuerdo interanotador.

Validar el paquete final congelado:

```bash
uv run agro-rag validate-benchmark data/evaluation/benchmark-60.jsonl
```

La revisión humana debe contrastar cada pregunta, respuesta, claim, página e `evidence_id` con las
fuentes; corregir lo necesario; reemplazar `annotator`; y cambiar a `reviewed` sólo los casos
efectivamente revisados. El archivo final completo se valida sin `--draft`. El cargador final rechaza
automáticamente paquetes pendientes o mixtos. Si sólo revisa una persona, se declara un anotador y
no se informa acuerdo interanotador.

La corrida Playwright aceptada registró los 59 casos pendientes sin errores y coincidió en estado
en los 59; junto con el primer caso manual, los 60 estados fueron correctos. La revisión de
contenido/citas cerró con 49 PASS y 11 FAIL. Este resultado evalúa la configuración actual y no
reemplaza las ablaciones E1/E2/E3.

El reporte EVA-02 también tiene un contrato automatizado. Exige las variantes completas de E1,
E2 o E3, consultas pareadas, configuración y procedencia explícitas, resultados y errores por
pregunta, tokens, latencia p50/p95 y métricas separadas por recuperación, generación, agentes y
operación. Una ejecución `real` no puede mezclarse con `test_double` y exige revisión humana. El
comparador conserva deltas negativos y publica el denominador y los IDs excluidos. E1/E2/E3
definitivo ya no está bloqueado por EVA-01; queda pendiente acordar presupuesto, ejecutar las
variantes reales y revisar soporte.

## Ejecución asistida del checklist

`scripts/build_benchmark_checklist.py` convierte el borrador de 60 casos en un PDF rellenable con
Pass/Fail, resultado observado y notas por consulta. `scripts/run_benchmark_playwright.py` recorre
la aplicación Streamlit mediante un navegador real y registra por caso el estado esperado y
observado, coincidencia, latencia, texto visible y error. La salida automatizada es evidencia
operativa, no una calificación factual: una coincidencia de estado no demuestra que la respuesta,
los claims o las fuentes sean correctos. Esa decisión queda en el checklist humano.

### Regresión de estado del 28/10/2026

La primera corrida Playwright obtuvo 50/60 coincidencias de estado. Tras corregir decisiones
previas reproducibles y recuperación lexical, los diez desacuerdos originales pasaron en corridas
dirigidas. Tres regresiones completas posteriores obtuvieron 57/60, 58/60 y 57/60, con desacuerdos
en IDs diferentes entre pasadas. Por lo tanto, la mejora es observable pero no habilita declarar
60/60 estable: queda pendiente acotar la variación del investigador/verificador y repetir con un
protocolo de estabilidad, además de la revisión factual humana.

El runner admite `--repeat N` y guarda `run_index` en cada fila más un archivo
`*.summary.json` con conteos de estado, estabilidad y pass rate por consulta. Las repeticiones
multiplican llamadas y costo: en desarrollo se usan mocks; una corrida live repetida requiere
autorización explícita y debe registrar modelo, parámetros y fecha.

## Conjunto

60 casos únicos: 36 respondibles (incluye 12 que integran más de un pasaje), 12 ambiguos/sin soporte y 12 adversariales/fuera de alcance. Dividir por grupos de intención/familias de paráfrasis: 30 dev y 30 test, con 18/6/6 de cada categoría en cada split. Las paráfrasis de la misma pregunta no cruzan splits. Semilla 42, lista de IDs congelada y hash. El corpus completo sigue disponible en RAG; lo retenido son las preguntas/etiquetas de test, no necesariamente documentos.

Cada caso: query_id, family_id, question, crop, category, expected_status, reference_answer, required_claims, relevant_evidence_ids, source_pages, split, annotator, review_status, corpus_version. Qrels binarios a nivel pasaje y, por separado, fuente; no mezclar denominadores. Anotación manual revisada; si sólo hay un anotador, declararlo y no inventar acuerdo interanotador. Idealmente segunda revisión en casos ambiguos y muestra del resto.

No generar y aceptar etiquetas con el mismo LLM que se evalúa sin revisión. Guardar anotaciones y
resultados por separado. El corpus ya está congelado y el paquete candidato resuelve sus IDs, pero
ninguna etiqueta pasa a aceptada hasta la revisión humana.

## Experimentos separados

E1 recuperación: BM25; vectorial; híbrido RRF; híbrido + reranker. Mismos corpus/chunks/consultas y límites de candidatos. Mantener configuración original docente como referencia técnica, reportando su limitación de idioma; comparar embeddings multilingües en dev sin atribuir toda la mejora al reranker si también cambió embedding.

E2 verificación: mismo retrieval y generador, con/sin verificador. Misma versión de prompt de investigación y contexto disponible, registrar búsquedas adicionales y presupuesto real. Cambios de respuesta, costo y latencia se reportan juntos. Ablation por rol claramente identificada; dos agentes no son dos modelos necesariamente.

E3 operación: caché on/off con mismo set, primera ejecución fría y posteriores calientes separadas. Tres pasadas por configuración para latencia; muestras pequeñas y proveedor remoto impiden generalizar como benchmark de capacidad.

## Métricas

| Dimensión | Definición |
|---|---|
| Precision@k | Pasajes relevantes recuperados / k, k=5 y 10 |
| Recall@k | Pasajes relevantes recuperados / total relevante anotado, k=5,10,20 |
| nDCG@10, MRR@10, Hit@k | Orden, primer relevante y presencia de soporte; especificar truncación |
| Context coverage | Claims requeridos con soporte disponible / claims requeridos |
| Soporte factual | Claims verificables respaldados / claims verificables emitidos, revisión humana |
| Citas correctas | Citas que respaldan su claim / citas emitidas; medir también resolución de ID por separado |
| Abstención/aclaración | Matriz de confusión expected_status vs status; precisión/recall por clase |
| Agentes | Decisión correcta del verificador, revisiones útiles/perjudiciales, búsquedas redundantes, pasos y límites |
| Generación | Similitud semántica con referencia como complemento; no equivale a verdad ni reemplaza soporte |
| Operación | p50/p95, tokens de entrada/salida, llamadas, fallos, costo estimado con tarifa fechada, hit rate caché |

Queries sin relevantes anotados no entran en promedios IR respondibles; sí entran en métricas de abstención y fallos. Reportar denominadores y casos excluidos. Si el agente se abstiene, no asignar precisión factual perfecta por lista vacía; registrar no aplicable y cobertura 0 según el caso. Reportar todos los casos, incluidos timeouts.

## Metas iniciales y decisiones

Recall@20 ≥0,85 sobre respondibles de dev como objetivo de diseño, no requisito universal ni garantía. Citas resolubles: 100% por construcción/validación. Cero excedencias del límite de revisiones o presupuesto en tests. Latencia p95 caliente ≤30s, deadline 60s, sujetos a medición en equipo registrado. Registrar hardware/CPU/RAM, versiones, revisiones de modelos, hash corpus, commit, configuración y fecha.

Elegir configuración con dev; congelar antes de test. Informar diferencias pareadas por consulta y bootstrap por query cuando el tamaño lo permita, con cautela por n pequeño. Si falla una meta, registrar resultado y causa; no cambiar silenciosamente las etiquetas ni ajustar con test. Un defecto de código puede corregirse con TDD y repetir todo el experimento con nueva versión dejando el anterior.

## Artefactos

questions.jsonl, qrels.csv, split_manifest.json, run_manifest.json, retrieval_per_query.csv, answers.jsonl, human_review.csv, summary.json y figuras. Ruta runs/<run_id> ignorada por defecto; sólo evidencia final curada se incorpora al reporte. Modelos/servicios simulados nunca se contabilizan como evidencia de calidad científica real.
