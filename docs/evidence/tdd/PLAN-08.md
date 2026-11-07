# Evidencia PLAN-08 — planificación de retrieval sensible a metadata

Fecha: 07/11/2026. Responsable: coordinador/arquitecto, misma sesión. Rama:
`docs/professor-rag-feedback-draft`.

## Alcance

Se registraron proposal, design, spec, test-plan y tasks del cambio
`08-metadata-aware-retrieval`, junto con ADR-016 y trazabilidad en requisitos/plan. Este corte sólo
modifica contratos y planificación; no implementa producto y no declara RED/GREEN funcional.

## Verificación

Primer intento dentro del sandbox:

```text
npx --yes @fission-ai/openspec@latest validate 08-metadata-aware-retrieval --strict
exit code: 1
resultado: EPERM al escribir en el cache npm fuera del workspace; fallo de entorno, no de spec.
```

Repetición autorizada fuera del sandbox:

```text
npx --yes @fission-ai/openspec@latest validate 08-metadata-aware-retrieval --strict
exit code: 0
resultado: Change '08-metadata-aware-retrieval' is valid
```

## Estado

PLAN-08.1..08.5 completos. El PR #36 fue integrado en `main` con commit
`eb9122dc2c61fe0035bf09659662ca4fd6d2cc8c`. La rama `feat/meta-01-corpus-contract` parte de ese
commit y queda asignada al agente implementador RAG/datos A. La implementación funcional aún no se
inició; el Issue #40 registra propiedad y handoff esperado. META-01 debe comenzar con su handoff y
prueba RED observable.
