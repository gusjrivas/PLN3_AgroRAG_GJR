# AgroRAG: asistente documental verificable para riego y estrés hídrico

**Trabajo integrador - Procesamiento de Lenguaje Natural III**

Autor y responsable académico: Gustavo Julián Rivas
Versión documental: 22/11/2026 (diagrama de flujo incorporado)
Repositorio: https://github.com/gusjrivas/PLN3_AgroRAG_GJR

Estado del documento: paquete académico actualizado con EVA-02, aceptación de 27 casos y
evaluación Garak documentadas. La reproducción en un entorno limpio será el paso posterior.

## 1. Objetivo, problema y alcance

AgroRAG es un asistente documental en español para consultar evidencia sobre riego y estrés
hídrico en tomate y lechuga. El problema abordado no es predecir el riego ni controlar un sistema
agrícola, sino recuperar pasajes verificables, construir una respuesta limitada por esos pasajes y
mostrar la procedencia de cada afirmación. El proyecto prioriza trazabilidad, abstención y fallos
operativos explícitos por encima de una respuesta aparentemente útil sin respaldo.

El alcance funcional incluye exploración lexical del corpus, recuperación semántica experimental,
un flujo de investigador y verificador, API FastAPI, interfaz Streamlit, citas direccionables y
auditoría redactada. Los estados públicos son `answered`, `needs_clarification` e
`insufficient_evidence`. Los errores del proveedor, los timeouts y los contratos inválidos no se
convierten en respuestas agronómicas.

Quedan fuera del MVP las predicciones con sensores, la automatización del riego, CNN o ViT,
fine-tuning, búsqueda web libre durante una consulta, GraphRAG y despliegue Kubernetes. El sistema
no prescribe litros de agua sin datos y evidencia suficientes. El corpus es piloto y no representa
la totalidad de recomendaciones aplicables a una finca, región o campaña.

### Criterios de éxito técnico

- Una respuesta aprobada sólo referencia `evidence_id` existentes en el catálogo activo.
- El frontend consume exclusivamente la API HTTP y no importa índices, agentes ni modelos.
- Los proveedores se inyectan desde bootstrap; importar módulos no descarga pesos ni abre red.
- Los secretos locales permanecen fuera de Git y nunca aparecen en auditoría o respuestas.
- Toda automatización nueva conserva evidencia RED, GREEN y REFACTOR.

## 2. Corpus y procedencia

El corpus piloto efectivo contiene 27 fragmentos revisados de cinco fuentes públicas. El repositorio
versiona el manifiesto, las páginas seleccionadas, los hashes esperados y el procedimiento de
descarga, pero no redistribuye los PDF. Una descarga cuyo hash no coincide se rechaza para evitar
que una edición cambie silenciosamente el corpus.

| Fuente | Selección | Uso | Limitación |
|---|---|---|---|
| INTA Huerta 2008 | Lechuga, tomate y períodos críticos | Recomendaciones específicas de cultivo | Cobertura acotada y edición histórica |
| FAO56 1998 | Evaporación, transpiración y agua disponible | Fundamentos técnicos | Texto en inglés y no específico de toda situación local |
| INTA Riego en cultivos hortícolas 2024 | Agua disponible, programación y establecimiento | Fundamentos y operación de riego por goteo | Referencia regional del Oasis Norte de Mendoza |
| INTA Lechuga 2022 | Suelo, salinidad, exceso de agua y programación | Cobertura específica de lechuga | Requiere interpretar cada recomendación en su contexto productivo |
| INTA Tomate 2020 | Frecuencia, floración y cuajado | Cobertura específica de tomate | Hoja informativa breve y regional |

Cada pasaje mantiene `source_id`, edición, URL, página física PDF, página impresa, sección,
cultivo, texto original, texto adaptado y offsets. `corpus_version` deriva del manifiesto y de la
configuración de extracción. El catálogo SQLite se activa mediante un puntero pequeño y cada
versión es inmutable. Una ingesta fallida conserva la versión anterior.

Las tablas seleccionadas se reconstruyen con encabezados, unidades, fila y contexto. Esta regla
evita separar un número de su significado. Las páginas escaneadas sin texto se rechazan: el OCR no
se activa como fallback silencioso. El manifiesto vigente debe consultarse para confirmar fechas,
hashes y derechos antes de una reproducción.

### Admisión reproducible

```powershell
uv run agro-rag download data/manifest.json
uv run agro-rag ingest data/manifest.json --output data/processed/catalogue
```

La descarga requiere Internet y sólo admite los dominios institucionales configurados. La ingesta
posterior es local. Los PDF y catálogos generados están ignorados por Git.

## 3. Arquitectura

La solución es un monolito modular de backend con Streamlit como proceso separado. La interfaz
consume JSON por HTTP.

<!-- query-flow -->

**Figura 1. Flujo de consulta.** El caso de uso puede pedir aclaración antes de recuperar
pasajes o abstenerse si falta evidencia. El verificador puede solicitar una revisión,
tras la cual el investigador y el verificador vuelven a intervenir.

| Capa | Responsabilidad | Restricción principal |
|---|---|---|
| domain | Evidencia y reglas puras | Sin frameworks ni proveedores |
| application | Casos de uso y puertos | Sin infraestructura, FastAPI o Streamlit |
| infrastructure | SQLite, BM25, OpenAI, Ollama, Pinecone, E5 y reranker | Implementa puertos, no reglas HTTP |
| api | Esquemas, autenticación y errores | Sin lógica agronómica |
| bootstrap | Configuración e inyección | Único ensamblaje de adaptadores |
| agro_rag_ui | Cliente HTTP y estado visual | No importa `agro_rag` |

El investigador recibe pregunta, cultivo y evidencia. Puede producir claims, pedir aclaración o
abstenerse. El verificador comprueba IDs y soporte, aprueba, solicita una revisión acotada o termina
en aclaración/abstención. Hay un máximo de una corrección, seis llamadas LLM, cuatro operaciones de
búsqueda, 12.000 tokens y 60 segundos globales. Retrieval sincrónico se despacha a un worker para
no bloquear el event loop.

La API distingue liveness de readiness. Liveness no llama proveedores. Readiness requiere corpus y
modelo configurados. Un semáforo limita dos consultas activas; el exceso devuelve 429. La caché LRU
de retrieval usa consulta normalizada, filtros de cultivo/etapa/región y versión de corpus, nunca cachea errores ni
respuestas generadas.

## 4. Implementación y reutilización

Backend y frontend usan Python 3.12. FastAPI expone salud, catálogo, evidencia y consultas;
Streamlit presenta fuentes y respuesta verificada. Pydantic valida settings/HTTP y SQLite conserva
el catálogo. BM25 es el default; vector, hybrid o hybrid_rerank requieren activación explícita e
identidad, secreto y tokenizer compatibles. OpenAI y Ollama son proveedores HTTP opcionales.

Se adaptaron del código docente `Teoria1/Codigo/RAG`, commit
`1f4cdbb37f59a049ef9b35c482ccb1de850fbc43`, los patrones de configuración, BM25, Pinecone, RRF y
reranking. No se copiaron limpieza automática ni creación de índices en startup. El diseño separa
fuente/página/pasaje y publica el manifiesto remoto sólo después de verificar IDs.

La integración semántica administrativa usa `intfloat/multilingual-e5-small`, revisión
`614241f622f53c4eeff9890bdc4f31cfecc418b3`, con dimensión 384. El reranker experimental usa
`BAAI/bge-reranker-v2-m3`, revisión `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`.
Ambos se cargan de forma diferida. `index-pinecone` requiere configuración completa y namespace
nuevo; `--create-index` es explícito. El runtime verifica corpus/modelo/revisión/dimensión, cuenta
contexto sin truncarlo con tokenizer fijado, no degrada a BM25 e informa el modo efectivo.

La implementación siguió TDD por escenarios. La suite contiene pruebas unitarias, contrato API,
integración local, UI, arquitectura y navegador. Ruff, mypy, import-linter, OpenSpec y GitHub
Actions forman las puertas de cada PR.

## 5. Metodología de evaluación

El protocolo preregistrado define un benchmark de 60 casos revisados: 36 respondibles, 12 sin
soporte y 12 adversariales, con split agrupado 30 dev y 30 test. Cada split conserva 18/6/6 y una
familia de paráfrasis nunca cruza entre ambos. Sólo dev puede usarse para elegir parámetros.

Cada caso registra pregunta, cultivo, categoría, estado esperado, respuesta de referencia, claims
requeridos, evidencias relevantes, páginas fuente, anotador, revisión y versión de corpus. El
validador implementado exige exactamente esa distribución, qrels resolubles y SHA-256 del JSONL.
Los 36 casos respondibles integran promedios IR; los otros 24 se evalúan en abstención y
aclaración, sin contaminar el denominador de recuperación.

El paquete final de 60 casos fue revisado humanamente y congelado con todas sus filas en estado
`reviewed`. La corrida asistida por navegador obtuvo 49 PASS y 11 FAIL de contenido/citas, con
60/60 estados observados correctos. El hash SHA-256 del benchmark es
`b12253c38bec4e2e58b20ddb4ec1303c515a360001db37c56e6e54246bdcba69`.

| Experimento | Variantes congeladas | Dimensión principal |
|---|---|---|
| E1 | BM25, vector, hybrid, hybrid + reranker | Retrieval y latencia |
| E2 | Sin verificador, con verificador | Soporte, citas y decisión del agente |
| E3 | Caché fría, caché caliente | Latencia, tokens, llamadas y costo |

El reporte EVA-02 exige consultas pareadas, errores completos, corpus/dataset/commit, versiones de
prompts y modelos, tokens, p50/p95 y métricas separadas en retrieval, generación, agentes y
operación. Una corrida `real` no puede mezclarse con `test_double` y exige revisión humana. Un
resultado negativo se conserva junto con su denominador e IDs excluidos.

Las métricas previstas incluyen Precision@k, Recall@k, nDCG@10, MRR@10, cobertura de contexto,
soporte factual, citas correctas, matriz de estados, decisiones del verificador, p50/p95, tokens,
llamadas, fallos y costo con tarifa fechada. Similitud semántica puede complementar la revisión,
pero no sustituye el soporte factual.

## 6. Resultados y evidencia

### Verificación de ingeniería

El PR #52 del bug #51 registra `340 passed, 1 skipped, 3 deselected`, Ruff, mypy y dos contratos
de importación aprobados. Son verificaciones de aquel corte, no una nueva suite completa ni
una medida de calidad agronómica. Esta actualización sólo verifica la superficie documental.

### Aceptación complementaria de 27 casos

El 12/11/2026 se revisaron tres registros manuales y se ejecutaron otros 24 casos por API con
BM25 y OpenAI `gpt-4o`; P02 se repitió para revisar su cita. P01-P26 proceden de `dev` y P27
reproduce el bug #51: no constituyen otro benchmark independiente.

Resultado: 19 conformes y 8 incompletos según rúbrica. Las 24 consultas nuevas devolvieron el
estado esperado y citas con fuente/página/pasaje coincidentes. P27 pidió aclaración sin usar LLM.

Los fallos son omisiones: P17 da 0,9 dS/m, pero omite el efecto a 1,4 dS/m. Se conserva la rúbrica:
`answered` y una cita válida no garantizan completitud. No son ocho vulnerabilidades o datos falsos.

Total nuevo: 36 llamadas y 68.267/2.042 tokens de entrada/salida, sin costo monetario atribuido.
Revisión de la misma sesión asistente, sin segundo anotador humano ni nueva ejecución visual.
La campaña se cierra con limitaciones; IDs fallidos, corpus y libro: `docs/evidence/acceptance-27/`.

### Smoke semántico preliminar

El smoke del 23/10/2026 usó ocho preguntas y doce evidencias, con etiquetas `pending_human`:
es un borrador histórico, no el benchmark de 60 casos. Detectó pérdida de Recall@5 con RRF
respecto del vector y p95 de 30,56 s del reranker sólo en retrieval. La comparación principal
posterior es EVA-02; no se generalizan los scores del smoke ni se mezclan sus denominadores.

### Corrida EVA-02 presupuestada

El 28/10/2026 se ejecutaron E1 y E2 sobre los 18 casos respondibles de `dev`; `test` permaneció
cerrado. Hybrid RRF obtuvo Recall@20 0,9722 y p95 215,98 ms. El reranker elevó MRR a 0,9259 y
nDCG@10 a 0,8908, pero su p95 fue 47.012,40 ms sólo para retrieval, por encima del objetivo de la
respuesta completa.

E2 completó 18 pares reales. Sin verificador consumió 33.213 tokens de entrada, 1.795 de salida y
USD 0,100982; con verificador consumió 66.736, 2.197 y USD 0,188810. Ambos modos produjeron el
estado esperado 18/18. El verificador aprobó todos los casos, no pidió revisiones y cambió cinco
textos.

La revisión humana de los 18 pares registró 12 PASS y 6 FAIL. El dictamen único por par no
demuestra mejora causal del verificador. La revisión dirigida previa de cinco cambios encontró
tres omisiones; ambas evidencias se conservan en `docs/evidence/tdd/EVA-02-budgeted-live.md`.

E3 se limitó a una consulta con tres repeticiones frías y tres calientes. La mediana bajó de 1.562
a 1.406 ms, sin reducir tokens ni costo porque la caché guarda retrieval, no generación. El gasto
real total de EVA-02, incluido el piloto duplicado de estimación, fue USD 0,334369. La API pública
permanece en BM25 por la latencia del reranker, el alcance limitado a `dev` y la ausencia de una
mejora factual causalmente atribuible al verificador.

## 7. Seguridad, operación y costos

Secretos fuera de Git; CI usa secret store. La API exige `X-API-Key`, valida esquema/tamaño,
limita concurrencia y redacta errores. La descarga administrativa restringe dominios, redirects,
rutas y hashes; startup no crea ni borra índices. Auditoría conserva request ID, corpus, decisión,
duración, llamadas, tokens y caché, sin pregunta, prompt, evidencia ni credenciales.

La corrida EVA-02 registró USD 0,334369 con tarifas fechadas y quedó por debajo del tope autorizado
de USD 0,50. OpenAI, Pinecone y las descargas pueden generar uso externo; el operador debe revisar
su cuenta y presupuesto. Ollama se ejecuta localmente. El reporte separa costo real y estimado.

### Evaluación adversarial Garak ya ejecutada

La evaluación Garak 0.17.0 corresponde a la candidata `d38814b4`, desplegada por digest en WSL.
El seguimiento final completó las familias inicialmente interrumpidas por presupuesto:

| Familia | Respuestas reales | Resultado final |
|---|---:|---|
| API key | 32 | 0 detecciones |
| DAN | 15 | 15 falsos positivos revisados humanamente; 0 confirmados y 0 dudosos |
| Base64 | 32 | 0 detecciones |
| Prompt injection | 32 | 0 detecciones |

Gasto estimado: USD 0,337275; techo por corrida: USD 0,20. Informe:
`docs/evidence/garak/garak-d38814b4-human-report.md`. El usuario indicó reutilizarlo sin repetir
Garak en el entorno limpio. No se atribuye a commits posteriores; la promoción V2 sigue pendiente.

## 8. Reproducción

Requisitos: Git, Python 3.12, uv y PowerShell o un shell equivalente. Desde un checkout limpio:

```powershell
uv sync --frozen
Copy-Item .env.example .env
uv run agro-rag download data/manifest.json
uv run agro-rag ingest data/manifest.json --output data/processed/catalogue
uv run pytest -q
```

Iniciar API/UI según `docs/run-local.md`. Exploración funciona sin LLM; respuesta verificada
requiere proveedor configurado. Pinecone y el extra semántico son opcionales.

El informe se regenera con:

```powershell
uv run python scripts/build_report.py
```

El verificador offline comprueba el paquete base sin leer secretos ni usar red. La versión de
entrega requiere además reproducir la instalación en un checkout limpio y registrar sus artefactos.

## 9. Demo de 15 minutos

`docs/demo.md` distribuye los 15 minutos entre problema/corpus, arquitectura/reuso, demo,
evaluación y conclusiones. Mostrar evidencia, respuesta y aclaración. Si falla el proveedor,
mostrar el error y usar respaldo identificado. Registrar hardware/modelo/commit y ensayar.

## 10. Modalidad y responsabilidades humanas

Responsable académico: Gustavo Julián Rivas. Confirmar modalidad con la cátedra; si fuera grupal,
registrar integrantes y tareas humanas. Los agentes no son integrantes. La aceptación de resultados,
credenciales, qrels y envío es responsabilidad humana. No se envían correos automáticamente.

## 11. Conclusiones y trabajo pendiente

AgroRAG alcanza una primera versión local modular: corpus con procedencia, búsqueda lexical, API,
UI, dos roles acotados, citas verificables, seguridad básica, caché y auditoría redactada. Los
adaptadores semánticos se integraron en un namespace aislado y demostraron que el pipeline puede
medirse. El runtime permite una activación explícita y fail-closed para corridas controladas, sin
cambiar BM25 como default ni confundir capacidad técnica con validación científica.

La principal conclusión técnica es que mayor score de ranking no implica una mejor decisión de
producto. El reranker fue demasiado lento y el verificador no mostró una mejora factual causal en
la revisión disponible. Mantener BM25 en la API es una decisión conservadora sustentada por
evidencia, no una omisión silenciosa.

El alcance científico sigue limitado: `test` permanece cerrado para selección de parámetros,
E3 cubre una sola consulta y el dictamen humano E2 no separa la calidad de cada variante.
La aceptación complementaria conserva ocho respuestas incompletas; no se afirma calidad perfecta.
La recomendación docente sobre metadatos tiene META-01..04 integradas, mientras que la curación
real, la comparación contextual y el cierre META-05..07 siguen pendientes. No se presenta esa
extensión como terminada ni se archiva OpenSpec 08.

El cierre documental registra el estado demostrado y prepara la exposición. El paso operativo
siguiente será reproducir la versión elegida en un entorno limpio, sin repetir Garak por
instrucción del usuario. También quedan el ensayo de 15 minutos, la confirmación de modalidad
y fecha de Teoría 7 y el envío académico autorizado. La promoción de V2 es una tarea separada.

## 12. Referencias

- Repositorio docente PLN3, commit `1f4cdbb37f59a049ef9b35c482ccb1de850fbc43`, consigna y código RAG: https://github.com/gusjrivas/PLN3_GJR
- Goites, E. D. Manual de cultivos para la huerta orgánica familiar. INTA, 2008.
- Allen, R. G.; Pereira, L. S.; Raes, D.; Smith, M. Crop evapotranspiration. FAO Irrigation and Drainage Paper 56, 1998.
- Multilingual E5 small: https://huggingface.co/intfloat/multilingual-e5-small
- BGE reranker v2 m3: https://huggingface.co/BAAI/bge-reranker-v2-m3
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- Streamlit AppTest: https://docs.streamlit.io/develop/api-reference/app-testing

## 13. Declaración de asistencia de IA

Se utilizó Codex como asistente de desarrollo para explorar el repositorio, proponer cambios,
escribir y ejecutar pruebas, implementar código, revisar documentación y preparar este informe.
El proceso quedó sujeto a instrucciones versionadas, TDD, revisión de diffs, checks locales y CI.
También se utilizó Engram como memoria local de desarrollo cuando estuvo disponible.

La asistencia de IA no constituye revisión agronómica, anotación humana del benchmark ni
aprobación académica. Las métricas `pending_human`, las limitaciones y los resultados negativos se
mantienen explícitos. La persona responsable debe revisar el contenido, validar los qrels y decidir
la entrega final.
