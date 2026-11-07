# Tasks: Recuperación sensible a metadatos curados

Estado: plan registrado; ninguna tarea funcional iniciada. Coordinador: Gustavo Julián Rivas.
Rama de planificación: `docs/professor-rag-feedback-draft`. Rama de integración propuesta después
de integrar este plan: `feat/metadata-aware-retrieval`. Base y commit se registran al asignar cada
tarea; no inventarlos por anticipado.

Reglas de coordinación: un solo implementador hasta integrar META-02. Después META-03 y META-04
pueden ejecutarse en paralelo con worktrees/ramas separados. Ningún agente edita archivos propiedad
de otro corte; el coordinador integra en orden. Un revisor distinto revisa cuando esté disponible y,
si no lo está, se registra revisión de la misma sesión.

## Dependencias

```text
PLAN-08
  -> META-01
      -> META-02
          -> META-03 ┐
          -> META-04 ├-> META-05 -> META-06 -> META-07
                     ┘
```

`META-03` y `META-04` son las únicas tareas inicialmente paralelizables. El cierre de 07/Garak no
es dependencia funcional, pero la implementación debe partir de una base Git integrada y limpia.

## PLAN-08 — Contrato y planificación

Responsable: coordinador/arquitecto. Rama: `docs/professor-rag-feedback-draft`. Propiedad:
`openspec/changes/08-metadata-aware-retrieval/**`, `docs/adr/016.md`, índice ADR,
`docs/requirements.md`, `docs/plan.md` y borrador docente. Dependencias: ninguna de código.
Evidencia: `docs/evidence/tdd/PLAN-08.md`; validación OpenSpec y revisión del diff documental. No se
declara ciclo RED de producto para prosa de planificación.

- [x] PLAN-08.1 Registrar alcance, exclusiones, vocabularios iniciales y política de recuperación.
- [x] PLAN-08.2 Crear requisitos, escenarios, test-plan y grafo de dependencias.
- [x] PLAN-08.3 Registrar responsables, ramas propuestas y archivos de propiedad.
- [x] PLAN-08.4 Validar OpenSpec estricto y revisar consistencia documental.
- [x] PLAN-08.5 Integrar la planificación en PR #36 y registrar `eb9122d` como commit base de META-01.

## META-01 — Contrato de corpus y evidencia

Responsable asignado: agente implementador RAG/datos A, coordinado por Gustavo Julián Rivas. Rama:
`feat/meta-01-corpus-contract`. Commit base: `eb9122dc2c61fe0035bf09659662ca4fd6d2cc8c`.
Issue: #40. Dependencias: PLAN-08 integrado mediante PR #36. Propiedad exclusiva:
`src/agro_rag/domain/evidence.py`,
`src/agro_rag/infrastructure/corpus.py`, fixtures propios de corpus,
`tests/integration/test_corpus.py` y `docs/evidence/tdd/META-01-metadata-contract.md`. El manifiesto
real no se cura todavía; usar fixtures mínimos. No editar retrieval, API o Pinecone.

- [ ] META-01.1 Leer ADR-006/016 y registrar handoff; base, rama y propiedad ya fijadas.
- [ ] META-01.2 RED: propagación, vocabularios inválidos, ausencia no inferida y cambio de versión.
- [ ] META-01.3 GREEN: ampliar modelos y propagar metadata con serialización determinista.
- [ ] META-01.4 REFACTOR: idempotencia, snapshot anterior, typing, Ruff y suite de corpus.
- [ ] META-01.5 Registrar comandos/códigos/commit y obtener revisión antes de integrar.

## META-02 — Política común y contrato de retrieval

Responsable propuesto: agente RAG/datos A. Rama: `feat/meta-02-retrieval-policy`. Dependencias:
META-01 integrado. Propiedad exclusiva: `src/agro_rag/application/retrieval.py`,
`src/agro_rag/application/retrieval_pipeline.py`, `src/agro_rag/infrastructure/retrieval.py`,
`src/agro_rag/bootstrap/retrieval.py`, `tests/unit/test_retrieval.py`,
`tests/unit/test_retrieval_pipeline.py`, pruebas runtime focalizadas y
`docs/evidence/tdd/META-02-retrieval-policy.md`. No editar API, caso de uso ni Pinecone.

- [ ] META-02.1 RED: exact/general/unknown/incompatible, cultivo estricto y ausencia de filtros.
- [ ] META-02.2 RED: demostrar paridad de política entre runtime BM25 y pipeline sin cargar semántica.
- [ ] META-02.3 GREEN: introducir `RetrievalFilters` y política pura compartida.
- [ ] META-02.4 GREEN: adaptar puertos/runtimes conservando orden, diversidad y presupuesto.
- [ ] META-02.5 REFACTOR: suite retrieval, typing, arquitectura y evidencia; revisión e integración.

## META-03 — API, contexto, caché y suficiencia

Responsable propuesto: agente backend/agentes B. Rama: `feat/meta-03-query-context`. Dependencias:
META-02 integrado. Propiedad exclusiva: `src/agro_rag/api/schemas.py`,
`src/agro_rag/api/query.py`, `src/agro_rag/application/query.py`, `tests/unit/test_query.py`,
`tests/contract/test_query_api.py`, fixtures de contrato y
`docs/evidence/tdd/META-03-query-context.md`. No editar adaptadores de retrieval o Pinecone.

- [ ] META-03.1 RED: región/etapa llegan a retrieval y forman parte de la clave de caché.
- [ ] META-03.2 RED: aclaración sin LLM, insuficiencia con contexto completo y pregunta general.
- [ ] META-03.3 GREEN: agregar `region`, construir filtros y enriquecer contexto de agentes.
- [ ] META-03.4 GREEN: preservar schemas públicos, citas, errores tipados y auditoría redactada.
- [ ] META-03.5 REFACTOR: unit/contract, typing, arquitectura, evidencia y revisión.

## META-04 — Metadata Pinecone e identidad remota

Responsable propuesto: agente RAG/datos C. Rama: `feat/meta-04-pinecone-metadata`. Dependencias:
META-02 integrado. Puede correr en paralelo con META-03. Propiedad exclusiva:
`src/agro_rag/infrastructure/pinecone.py`, `tests/unit/test_pinecone.py`, integración live específica
si se autoriza y `docs/evidence/tdd/META-04-pinecone-metadata.md`. No editar API, caso de uso ni
política común.

- [ ] META-04.1 RED: payload seguro, filtros de identidad/cultivo y ausencia de texto/rutas.
- [ ] META-04.2 RED: falla parcial o incompatibilidad no publica manifiesto.
- [ ] META-04.3 GREEN: ampliar metadata remota y consumir filtros compatibles.
- [ ] META-04.4 REFACTOR: verificar batch/namespace/identidad, suite offline y evidencia.
- [ ] META-04.5 LIVE opcional: integración aislada sólo con autorización, namespace fresco y presupuesto.

## META-05 — Curación del corpus real

Responsable propuesto: coordinador + agente RAG/datos A, con revisión humana de Gustavo Julián
Rivas. Rama: `feat/meta-05-corpus-curation`. Dependencias: META-01, META-03 y META-04 integrados.
Propiedad exclusiva: `data/manifest.json`, `docs/evidence/corpus/metadata-review.csv`, documentación
de corpus, fixtures de validación y `docs/evidence/tdd/META-05-corpus-curation.md`. No inferir valores
para completar celdas; registrar `unknown`/vacío y justificación.

- [ ] META-05.1 Revisar las 27 evidencias y vincular cada valor con fuente/página/sección.
- [ ] META-05.2 Registrar revisión humana, vocabulario efectivamente usado y casos desconocidos.
- [ ] META-05.3 Ejecutar validación del manifiesto y corregir sólo errores trazables.
- [ ] META-05.4 Reconstruir dos veces offline y comprobar IDs/version deterministas.
- [ ] META-05.5 Revisar diff de datos y evidencia; no indexar remoto en esta tarea.

## META-06 — Reindexado y evaluación comparativa

Responsable propuesto: agente evaluador/revisor D. Rama: `feat/meta-06-evaluation`. Dependencias:
META-03, META-04 y META-05 integrados. Propiedad exclusiva: `src/agro_rag/evaluation/**`, suplemento
versionado bajo `data/evaluation/`, pruebas de evaluación/reporte y
`docs/evidence/tdd/META-06-evaluation.md`. El benchmark congelado original no se reescribe; el
suplemento contextual tiene identidad propia. Servicios pagos/live requieren autorización explícita.

- [ ] META-06.1 RED: paquete contextual exige corpus, filtros, qrels y hash compatibles.
- [ ] META-06.2 GREEN: ejecutar baseline y variante sobre el mismo catálogo offline.
- [ ] META-06.3 Medir Recall@k, MRR/nDCG, incompatibles top-k, estados, citas y latencia.
- [ ] META-06.4 Reindexar Pinecone sólo si fue autorizado; usar namespace nuevo y conservar anterior.
- [ ] META-06.5 RED/GREEN: el reporte no afirma mejora ni cambia default si el gate no se cumple.
- [ ] META-06.6 Registrar limitaciones, resultados reales/mocks y revisión independiente.

## META-07 — Integración y cierre

Responsable: coordinador/arquitecto. Rama: `feat/metadata-aware-retrieval` o rama de integración que
se registre. Dependencias: META-01..06 integrados. Propiedad: documentación transversal, ADR/spec,
handoffs y resolución de conflictos; no reescribir evidencia de agentes.

- [ ] META-07.1 Revisar contratos cruzados, diff, handoffs y commits de cada tarea.
- [ ] META-07.2 Ejecutar suite afectada, suite completa, Ruff, mypy y límites de arquitectura.
- [ ] META-07.3 Validar OpenSpec estricto, documentación, rollback y modo BM25 sin red/modelos.
- [ ] META-07.4 Registrar revisión independiente o declarar revisión de la misma sesión.
- [ ] META-07.5 Actualizar estado/evidencia; no archivar 08 hasta implementar y verificar todo.

## Plantilla de asignación para cada agente

Antes de iniciar una casilla funcional, el coordinador completa en PR/Issue:

```text
task_id:
escenarios OpenSpec:
responsable:
revisor:
rama/worktree:
commit base:
rutas permitidas:
rutas prohibidas/otro propietario:
dependencias integradas:
comando RED esperado:
evidencia destino:
limitaciones live/secretos:
```

Handoff obligatorio: prueba roja real, comandos verdes, códigos de salida, commit, limitaciones y
siguiente paso. Los agentes no están solos en el repositorio: no revierten cambios ajenos y ajustan
su implementación a contratos ya integrados.
