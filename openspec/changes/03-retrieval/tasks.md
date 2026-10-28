# Tasks: Recuperación híbrida y reranking evaluables

Responsable: RAG/datos. Dependencias: 02-corpus. Primera implementación parcial en PR #4. Evidencia: docs/evidence/tdd/03-05-first-version.md. Mantener casillas abiertas hasta cubrir todos los escenarios, incluidos proveedores reales, índice híbrido y hardening pendientes.

## Corte independiente: contratos offline

Responsable: coordinador/RAG, misma sesión. Rama: feat/03-retrieval-contracts. Propiedad y límites: docs/plan.md y ADR-013. Evidencia: docs/evidence/tdd/03-pipeline.md.

- [x] C.1 Leer contratos/ADR y verificar corpus descargado y base main.
- [x] C.2 RED: cuatro modos, fallo vector, identidad de índice, filtros, diversidad y presupuesto.
- [x] C.3 GREEN/REFACTOR: pipeline por puertos, candidatos lexicales y errores controlados; suite y checks locales.
- [x] C.4 CI remota y revisión del diff; cortes integrados sólo con checks aprobados.
- [x] C.5 Adaptadores reales, tokenizer, prefijos E5, smoke en español y activación configurable por
  bootstrap. La evaluación científica permanece en T.4.

Los checks del corte no cierran los requisitos completos siguientes.

## Corte de adaptador docente Pinecone/E5

Responsable: coordinador/RAG, misma sesión. Rama: `feat/pinecone-adapter`. Base:
`PLN3_GJR/Teoria1/Codigo/RAG` en `1f4cdbb37f59a049ef9b35c482ccb1de850fbc43`.
Propiedad: `src/agro_rag/infrastructure/pinecone.py`,
`src/agro_rag/infrastructure/reranker.py`, `src/agro_rag/bootstrap/cli.py`,
`src/agro_rag/bootstrap/settings.py`, `tests/unit/test_pinecone.py`, pruebas CLI afectadas,
`pyproject.toml`, `uv.lock`, `.env.example`, documentación y evidencia de este corte.
Evidencia: `docs/evidence/tdd/03-pinecone-adapter.md`.

- [x] P.1 Leer README y módulos docentes; mapear `PineconeSearcher` al contrato `CandidateRanker`.
- [x] P.2 RED: prefijos E5, manifiesto de identidad, ranking, filtros e ingesta no destructiva.
- [x] P.3 GREEN: adaptar embeddings/Pinecone sin red, modelos o secretos al importar.
- [x] P.4 Integrar comando administrativo con namespace nuevo; no activar consultas públicas aún.
- [x] P.5 REFACTOR: suite, tipos, arquitectura, validación OpenSpec y evidencia.
- [x] P.6 Ejecutar `integration_live` aislada y benchmark antes de activar hybrid en bootstrap/API.

## Corte de integración real y benchmark dev

Responsable: coordinador/RAG, misma sesión. Rama: `feat/03-retrieval-live-eval`. Dependencia:
PR #7 (`fix/windows-sqlite-snapshot`). Propiedad inicial:
`src/agro_rag/evaluation/`, `data/evaluation/`, `tests/unit/test_retrieval_metrics.py`,
`tests/integration_live/`, bootstrap administrativo y evidencia del corte. La API pública no cambia
en este PR hasta que todos los gates de ADR-013 tengan resultados reproducibles.
Evidencia: `docs/evidence/tdd/03-live-eval.md`.

- [x] L.1 Reconstruir el catálogo fijado y confirmar 12 evidencias/versionado local.
- [x] L.2 RED/GREEN: métricas IR puras y validación estricta de qrels/rankings.
- [x] L.3 Congelar borrador dev trazable, marcado pendiente de revisión humana.
- [x] L.4 Agregar y ejecutar integración Pinecone en namespace aislado; limpiar sólo intentos parciales.
- [x] L.5 Ejecutar BM25/vector/hybrid/rerank, registrar latencia y métricas por consulta.
- [x] L.6 Revisar gates de activación; mantener BM25 público por qrels pendientes y latencia.

## Corte de sincronización con el corpus ampliado

Responsable: coordinador/RAG, misma sesión. Rama: `fix/corpus-runtime-sync`. Propiedad:
`data/evaluation/retrieval-dev-draft.jsonl`, smoke Pinecone, documentación y evidencia del corte.
Evidencia: `docs/evidence/tdd/RET-CORPUS-SYNC.md`.

- [x] R.1 RED: demostrar que los qrels de la versión anterior son rechazados por el catálogo nuevo.
- [x] R.2 GREEN: migrar por correspondencia de pasajes, conservar `pending_human` y fijar el hash.
- [x] R.3 RED/GREEN: medir el desplazamiento de ranking y validar Recall@20 en Pinecone real.
- [x] R.4 REFACTOR: suite, calidad, OpenSpec y evidencia; CI y revisión remota pendientes en el PR.
- [x] R.5 RED/GREEN: ignorar numeración de lista inicial sin eliminar cantidades agronómicas y
  verificar la consulta real en UI/OpenAI. Evidencia: `docs/evidence/tdd/RET-NUMBERED-QUERY.md`.

## Corte de hardening: límite async entre API y retrieval

Responsable: coordinador/backend, misma sesión. Rama: `feat/03-retrieval-api-activation`.
Propiedad: `src/agro_rag/application/query.py`, `src/agro_rag/api/query.py`, pruebas afectadas,
ADR-013 y evidencia `docs/evidence/tdd/03-retrieval-async-boundary.md`. Este corte prepara la
activación sin cambiar el modo público BM25.

- [x] A.1 RED: demostrar que retrieval bloquea el event loop, el deadline no lo interrumpe y su
  indisponibilidad llega como 500.
- [x] A.2 GREEN: ejecutar retrieval síncrono en worker y traducir fallos tipados a 502/503 sin
  exponer el mensaje interno.
- [x] A.3 REFACTOR: suite completa, tipos, arquitectura, OpenSpec, revisión del diff y CI remota.

## Corte de seguridad local: credencial Pinecone

Responsable: coordinador/RAG, misma sesión. Rama: `fix/pinecone-secret-config`. Propiedad:
`src/agro_rag/bootstrap/settings.py`, `tests/unit/test_settings.py`, `.env.example`,
`docs/run-local.md`, `docs/sources.md`, este registro y
`docs/evidence/tdd/RET-PINECONE-SECRET.md`. Alcance: preparar
la inyección segura de la credencial local; no activa el adaptador ni declara RET-01/02 completo.

- [x] S.1 Revisar archivos versionados, entorno local e historial sin imprimir valores secretos.
- [x] S.2 RED: comprobar carga, precedencia y redacción de `PINECONE_API_KEY`.
- [x] S.3 GREEN: tipar la credencial como `SecretStr`, ignorar vacíos y mantener `.env` fuera de Git.
- [x] S.4 REFACTOR: ejecutar suite afectada, controles estáticos y revisión final del diff.
- [x] S.5 Registrar evidencia y riesgos restantes.

## Corte de activación runtime explícita

Responsable: coordinador/RAG, misma sesión. Rama: `feat/semantic-runtime-activation`.
Propiedad: `src/agro_rag/bootstrap/retrieval.py`, tokenizer/configuración/ensamblado afectados,
pruebas focalizadas, documentación y evidencia `docs/evidence/tdd/03-semantic-runtime-activation.md`.
No cambia BM25 como default ni acredita evaluación humana.

- [x] T.1 RED: exigir composición semántica fail-closed, tokenizer fijado, modo observable y cierre.
- [x] T.2 GREEN: conectar los cuatro modos al bootstrap sin I/O de proveedor en modo BM25.
- [x] T.3 REFACTOR: suite completa, calidad, OpenSpec, evidencia y revisión del diff.
- [ ] T.4 LIVE: activar con namespace/modelos reales y repetir E1/E2/E3 tras qrels humanos.

## 1. Preparación

- [ ] 1.1 Leer ADR aplicables, fijar archivos de propiedad y comprobar dependencias.
- [ ] 1.2 Preparar fixtures/contratos sin servicios pagos; identificar qué checks requieren integración real.

## 2. Implementación mediante TDD

- [ ] 2.1.1 RED: escribir y ejecutar pruebas de los escenarios de RET-01; guardar fallo funcional esperado.
- [ ] 2.1.2 GREEN: implementar mínimo comportamiento de RET-01 y ejecutar las mismas pruebas.
- [ ] 2.1.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de RET-01.
- [ ] 2.2.1 RED: escribir y ejecutar pruebas de los escenarios de RET-02; guardar fallo funcional esperado.
- [ ] 2.2.2 GREEN: implementar mínimo comportamiento de RET-02 y ejecutar las mismas pruebas.
- [ ] 2.2.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de RET-02.
- [ ] 2.3.1 RED: escribir y ejecutar pruebas de los escenarios de RET-03; guardar fallo funcional esperado.
- [ ] 2.3.2 GREEN: implementar mínimo comportamiento de RET-03 y ejecutar las mismas pruebas.
- [ ] 2.3.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de RET-03.

## 3. Cierre

- [ ] 3.1 Ejecutar tests de integración/seguridad pertinentes y checks estáticos; distinguir mocks de proveedores reales.
- [ ] 3.2 Actualizar documentación, trazabilidad y handoff; enlazar evidencia y commit.
- [ ] 3.3 Revisión del diff por revisor disponible, registrar autor y riesgos; integrar cuando Definition of Done esté satisfecha.
- [ ] 3.4 Archivar el cambio y promover deltas a specs sólo después de verificar implementación real.
