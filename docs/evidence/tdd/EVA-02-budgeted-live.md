# Evidencia TDD y corrida real: EVA-02 con tope de USD 0,50

Fecha: 28/10/2026. Responsable y revisión: coordinador/evaluador, misma sesión. Rama:
`eval/eva02-budgeted-run`. Benchmark congelado:
`b12253c38bec4e2e58b20ddb4ec1303c515a360001db37c56e6e54246bdcba69`, corpus
`e9929440f552b1c7be1349118a1ee98c6cdba41fbd2e2ce05343247c918dfb7d`.

## TDD

RED observados:

- el test del runner E1 falló con `ModuleNotFoundError: scripts.run_e1_retrieval`;
- la ablación E2 falló porque `QueryService` no aceptaba `verifier_enabled`;
- el corte presupuestario E2 falló mientras no existía `scripts.run_e2_budgeted`;
- la prueba del límite refinado falló contra la reserva inicial de USD 0,24 por par.

GREEN/REFACTOR:

```text
pytest tests/unit/test_e1_retrieval_runner.py: 1 passed
pytest tests/unit/test_query.py tests/contract/test_query_api.py: 47 passed
pytest tests/unit/test_e2_budget.py: 1 passed
ruff: All checks passed
mypy src y scripts de evaluación: Success
```

Al incorporar los resultados al informe, la revisión visual detectó una octava página casi vacía.
Se agregó primero el límite observable de siete páginas a
`test_del_01_informe_builds_a_readable_pdf`: RED con `assert 8 <= 7`; después se retiró el salto
forzado anterior a **Reproducción**: GREEN, `1 passed`. El contenido no se redujo ni ocultó para
cumplir la puerta.

Verificación final del corte:

```text
pytest suite afectada: 60 passed
ruff check: All checks passed
ruff format --check: 12 files already formatted
mypy src + runners E1/E2/E3: Success, 39 source files
OpenSpec 06-evaluation-delivery --strict: valid
verify-delivery: 8 artefactos, exit 0
PDF: 7 páginas renderizadas e inspeccionadas sin recortes ni solapamientos
```

Un intento de ampliar mypy a `scripts/build_report.py` expuso deuda previa: faltan stubs de
ReportLab y anotaciones en ese script. El gate versionado no lo incluía; no se ocultó el hallazgo
con `ignore-errors` ni se agregaron dependencias fuera de alcance.

La revisión final del diff fue realizada por la misma sesión coordinadora, porque no había un
revisor distinto disponible. No encontró defectos bloqueantes adicionales. Se conservan como
riesgos explícitos `test` cerrado, E3 limitado a una consulta, el dictamen humano por par y la deuda
de typing del generador PDF.

El modo normal conserva el verificador. La ablación explícita valida la salida del investigador,
hace una sola llamada y publica `verification.decision=not_run`; no simula una aprobación. El
runner reserva el peor costo contractual antes de cada par: cuatro llamadas máximas, 768 tokens de
salida por llamada y 12.000 tokens combinados implican como máximo USD 0,05304 por consulta con la
tarifa de GPT-4o del 28/10/2026.

## E1 real, split dev respondible (n=18)

| Modo | MRR | Recall@5 | nDCG@10 | Recall@20 | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|
| BM25 | 0,7361 | 0,9167 | 0,7429 | 0,9444 | 0,12 | 0,24 |
| Vector | 0,7909 | 0,7037 | 0,7480 | 0,9167 | 202,76 | 252,65 |
| Hybrid RRF | 0,7951 | 0,8611 | 0,7668 | 0,9722 | 181,04 | 215,98 |
| Hybrid + reranker | 0,9259 | 0,9167 | 0,8908 | 0,9722 | 38.023,10 | 47.012,40 |

Resultado negativo conservado: el reranker mejora orden, pero su p95 excede 30 s sólo en
recuperación. Hybrid RRF mantiene el mejor Recall@20 empatado con una latencia mucho menor y se usó
para E2. El tokenizer E5 quedó fijo para seleccionar evidencia en las cuatro variantes; no se lo
presenta como contador de tokens de generación GPT-4o.

Artefacto local ignorado: `output/evaluation/e1-dev-real-2026-10-28.json`, SHA-256
`f4d8f0badbde123ddf31f976408c459e8913ea28d07a73c5771b70c7deac43fd`.

## E2 real pareado, split dev respondible (n=18)

| Variante | Estado correcto | Entrada | Salida | Costo USD | p50 ms | p95 observado ms |
|---|---:|---:|---:|---:|---:|---:|
| Sin verificador | 18/18 | 33.213 | 1.795 | 0,100982 | 1.765,5 | 2.405 |
| Con verificador | 18/18 | 66.736 | 2.197 | 0,188810 | 2.867,5 | 3.405 |

El verificador aprobó 18/18, no solicitó revisiones y cambió el texto en 5/18. Estos números no
demuestran una mejora factual: falta revisar humanamente esas respuestas y sus citas. El costo del
E2 pareado fue USD 0,289792. Sumando el piloto de estimación duplicado de USD 0,010972, el gasto
real total fue USD 0,300764, por debajo del tope autorizado de USD 0,50.

Artefactos locales ignorados y SHA-256, en orden de ejecución:

- `e2-budgeted-dev-2026-10-28.json`: `f4a1e1420e8423e6babf9e4eecc0e618c42ac89cb8f7d12d8f75712d69bf54b4`;
- `e2-budgeted-dev-batch2-2026-10-28.json`: `c08e0cd35f0440d7a2d1d8d4bbd120d024960a60960af16b31bcdb7abfdcb874`;
- `e2-budgeted-dev-batch3-2026-10-28.json`: `58c170f122c69e7895d1cf76417d086e8eff55e3bf49858df4ef924f20eeadfa`;
- `e2-budgeted-dev-batch4-2026-10-28.json`: `2a232254bf3ac4c6c09c0426a36cc126a77d7550056b5996a3aef1d0485c5ae2`.

### Revisión documental dirigida de los cinco textos modificados

Esta revisión fue realizada por la misma sesión agente contra referencia, claims requeridos y
pasajes citados; no se presenta como revisión humana independiente.

| query_id | Resultado | Hallazgo |
|---|---|---|
| dev-r-001 | FAIL | Omite que más de 30 °C perjudica germinación y desarrollo. |
| dev-r-009 | FAIL | Define ET, pero omite que evaporación y transpiración ocurren simultáneamente. |
| dev-r-011 | FAIL | Habla de ET y no responde que la pérdida principal ocurre por los estomas. |
| dev-r-016 | PASS | Conserva gravimetría/sensores y tensiómetros/bloques de yeso. |
| dev-r-018 | PASS | Conserva presión osmótica, dificultad de absorción y sequía fisiológica. |

El verificador aprobó también los tres resultados incompletos. Por tanto, no hay evidencia de que
el verificador haya mejorado soporte factual en esta muestra dirigida.

### Revisión humana independiente de los 18 pares

El usuario completó la revisión en la planilla versionada
`docs/evidence/workbooks/e2-revision-humana-18-pares.xlsx` el 29/10/2026. El resumen calculado del
libro quedó `COMPLETA`, con 18 casos, 0 pendientes, 12 PASS y 6 FAIL. Los FAIL fueron
`dev-r-002`, `dev-r-003`, `dev-r-004`, `dev-r-011`, `dev-r-012` y `dev-r-013`; en esas filas la
observación humana registra un fallo en la búsqueda de **Explorar fuentes**. SHA-256 del archivo:
`cc5df046921b63f945b1d8e636da6672d2ff9e3312df1b4fa6d8e06c9701bd53`.

Sobre los cinco textos que el verificador modificó, el dictamen humano fue PASS para `dev-r-001`,
`dev-r-009`, `dev-r-016` y `dev-r-018`, y FAIL para `dev-r-011`. Esto difiere de la revisión
documental dirigida de la sesión agente, que había marcado tres omisiones. Se preservan ambos
registros sin reemplazar el dictamen humano ni ocultar el desacuerdo.

La planilla registra un único dictamen humano por par, no una puntuación independiente para cada
respuesta con/sin verificador. Por ello permite cerrar la revisión de los 18 casos, pero no medir
un delta causal de soporte atribuible al verificador. `Revisado por` y `Fecha` quedaron completos
en las 18 filas por el usuario: `Gus Rivas`, 29/10/2026.

## E3 real presupuestado, una consulta y tres repeticiones

Se usó `dev-r-001`, retrieval hybrid, investigador sin verificador y salida máxima de 256 tokens.
Los tres servicios nuevos produjeron miss; el primer servicio se reutilizó para tres hits. Ambos
lados conservaron modelo, prompt, evidencia y límites.

| Variante | n | Hits | p50 ms | máximo observado ms | Entrada | Salida | Costo USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fría | 3 | 0/3 | 1.562 | 2.156 | 5.487 | 306 | 0,016778 |
| Caliente | 3 | 3/3 | 1.406 | 1.468 | 5.487 | 311 | 0,016828 |

La caché redujo la mediana observada 156 ms, pero no ahorró tokens ni costo de generación porque
la implementación cachea retrieval, no respuestas. Con n=1 y tres repeticiones no se generaliza
capacidad. Artefacto local `e3-budgeted-dev-r-001-2026-10-28.json`, SHA-256
`f3a379461cb4855c3020d5b4f491b6c811efa5eeb289a795d55a2705a239a3f6`.

E3 costó USD 0,033605. El gasto real total de EVA-02, incluido el piloto E2 duplicado, fue
USD 0,334369; quedaron USD 0,165631 sin usar.

## Puertas restantes

- ampliar E3 a más consultas sólo si se necesita generalización; el protocolo mínimo de tres
  repeticiones quedó ejecutado sobre una consulta;
- conservar como limitación que la revisión humana puntúa el par y no cada variante por separado,
  y que la planilla no repite revisor/fecha en todas las filas;
- mantener `test` fuera de ajustes: todas estas corridas usaron únicamente `dev`.
