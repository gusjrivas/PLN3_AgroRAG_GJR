# Tasks: Corpus versionado con evidencia

Responsable: RAG/datos. Dependencias: 00-foundation y 01-engram; puede continuar desde Git si memoria tiene bloqueo documentado. Implementación piloto y evidencia en docs/evidence/tdd/02-corpus.md. Admisión, tablas revisadas, catálogo local y ampliación institucional implementados. COR-03 remoto permanece pendiente; no archivar.

## Corte COR-EXP-01: ampliación institucional

Responsable: coordinador/RAG, misma sesión. Rama: `feat/corpus-expansion`. Propiedad:
`data/manifest.json`, admisión/ingesta de corpus, pruebas de integración y documentación/evidencia
del corte. Se agregan tres publicaciones oficiales de INTA sin redistribuir los PDF.
Evidencia: `docs/evidence/tdd/COR-EXP-01.md`.

- [x] E.1 RED: rechazar inicialmente el host institucional nuevo y exigir cobertura curada.
- [x] E.2 GREEN: admitir el repositorio INTA y construir 27 evidencias desde cinco fuentes.
- [x] E.3 RED/GREEN: reproducir y corregir la pérdida de marcadores UTF-8 en Windows.
- [x] E.4 REFACTOR: suite completa, calidad, OpenSpec, evidencia y revisión de la misma sesión; revisión remota pendiente en el PR.

## Corte de portabilidad Windows para snapshots SQLite

Responsable: coordinador/RAG, misma sesión. Rama: `fix/windows-sqlite-snapshot`.
Propiedad: `src/agro_rag/infrastructure/corpus.py`, pruebas de integración de corpus,
`tests/contract/test_health.py`, documentación y evidencia del corte. Motivo: desbloquear la
reconstrucción y los gates locales en Windows requeridos por `03-retrieval/P.6`, sin cambiar el
contrato inmutable de ADR-006 ni la semántica de liveness.
Evidencia: `docs/evidence/tdd/WIN-SQLITE-SNAPSHOT.md`.

- [x] W.1 RED: reproducir `WinError 32` al activar el snapshot desde el CLI.
- [x] W.2 GREEN: cerrar explícitamente conexiones SQLite antes de mover o eliminar archivos.
- [x] W.2b RED: reproducir el falso positivo de red al bloquear el socket interno de AnyIO.
- [x] W.2c GREEN: interceptar sólo el transporte HTTP de proveedores en el test de liveness.
- [x] W.3 REFACTOR: suite completa, calidad, evidencia y validación local; CI/revisión remota en PR.

## 1. Preparación

- [ ] 1.1 Leer ADR aplicables, fijar archivos de propiedad y comprobar dependencias.
- [ ] 1.2 Preparar fixtures/contratos sin servicios pagos; identificar qué checks requieren integración real.

## 2. Implementación mediante TDD

- [ ] 2.1.1 RED: escribir y ejecutar pruebas de los escenarios de COR-01; guardar fallo funcional esperado.
- [ ] 2.1.2 GREEN: implementar mínimo comportamiento de COR-01 y ejecutar las mismas pruebas.
- [ ] 2.1.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de COR-01.
- [ ] 2.2.1 RED: escribir y ejecutar pruebas de los escenarios de COR-02; guardar fallo funcional esperado.
- [ ] 2.2.2 GREEN: implementar mínimo comportamiento de COR-02 y ejecutar las mismas pruebas.
- [ ] 2.2.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de COR-02.
- [ ] 2.3.1 RED: escribir y ejecutar pruebas de los escenarios de COR-03; guardar fallo funcional esperado.
- [ ] 2.3.2 GREEN: implementar mínimo comportamiento de COR-03 y ejecutar las mismas pruebas.
- [ ] 2.3.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia de COR-03.

## 3. Cierre

- [ ] 3.1 Ejecutar tests de integración/seguridad pertinentes y checks estáticos; distinguir mocks de proveedores reales.
- [ ] 3.2 Actualizar documentación, trazabilidad y handoff; enlazar evidencia y commit.
- [ ] 3.3 Revisión del diff por revisor disponible, registrar autor y riesgos; integrar cuando Definition of Done esté satisfecha.
- [ ] 3.4 Archivar el cambio y promover deltas a specs sólo después de verificar implementación real.
