# Requisitos y trazabilidad

## Fuentes normativas

Consigna Clase1_PLN3.pdf pp.4-5 y p.11 del repositorio docente, commit 1f4cdbb. pp.43-44 orientan el ejemplo y evaluación. Instrucciones del usuario: repo independiente, Python, buenas prácticas backend/frontend/arquitectura y TDD transversal.

| ID académico | Exigencia | Cobertura prevista |
|---|---|---|
| CAT-01 | Código funcional modular preproductivo | FND-01/02/03, todos los cambios |
| CAT-02 | API FastAPI preferida o Streamlit | API-01, UI-01 |
| CAT-03 | Dos agentes con comunicación dinámica | AGT-01/02/03 |
| CAT-04 | RAG semántico retriever-ranker y trazabilidad | COR-01/02/03, RET-01/02/03 |
| CAT-05 | Seguridad: acceso, input/output, auditoría | API-01, SEC-01, OPS-01 |
| CAT-06 | Flujo modular desacoplable y monitoreable | FND-02, AGT-03, OPS-01 |
| CAT-07 | Al menos una optimización costo/latencia | OPS-01, RET-03 |
| CAT-08 | Métricas de modelos, agentes y RAG | EVA-01/02 |
| CAT-09 | Informe PDF con objetivo, arquitectura, implementación, evaluación, resultados, conclusiones | DEL-01 |
| CAT-10 | Presentación 15 min, entrega hasta Teoría 7, planificación humana si grupal | DEL-01 |
| USR-01 | Python backend/frontend y arquitectura mantenible | FND-02, UI-01/02 |
| USR-02 | TDD en todo desarrollo | FND-03 y test-plan/tasks de cada cambio |
| USR-03 | Repo separado del material fuente | FND-01 |
| USR-04 | Organización por agentes, Engram, SDD y ADR | MEM-01/02, docs/development-agents.md, docs/adr |

CNN/ViT y acción final externa automática son opcionales en la consigna y quedan fuera del MVP. Kubernetes, porcentaje de cobertura, tamaño del benchmark y metas de latencia son decisiones del proyecto, no imposiciones de la cátedra.

## Matriz de requisitos de implementación

La matriz describe el objetivo completo. La implementación incremental y su evidencia están en
`docs/evidence/tdd`; ver `docs/plan.md` para el estado actual. RET-01/02/03 tienen contratos,
adaptadores, smoke dev y activación runtime explícita según ADR-013, pero BM25 continúa como default
y no se declara evaluación científica completa. Al completar un requisito entero, añadir commit y
ubicación de evidencia; no cambiar sólo la etiqueta de estado.

| ID | Requisito | Cambio/spec | Escenarios | Evidencia prevista |
|---|---|---|---|---|
| FND-01 | Repositorio autónomo y procedencia | [00-foundation](../openspec/changes/00-foundation/specs/foundation/spec.md) | FND-01-independiente, FND-01-existente | test-plan del cambio + docs/evidence/tdd/FND-01.md |
| FND-02 | Inyección y límites de arquitectura | [00-foundation](../openspec/changes/00-foundation/specs/foundation/spec.md) | FND-02-imports, FND-02-sin-red | test-plan del cambio + docs/evidence/tdd/FND-02.md |
| FND-03 | Ciclo TDD y entorno reproducible | [00-foundation](../openspec/changes/00-foundation/specs/foundation/spec.md) | FND-03-ciclo, FND-03-clean | test-plan del cambio + docs/evidence/tdd/FND-03.md |
| MEM-01 | Proyecto e integración verificables | [01-engram](../openspec/changes/01-engram/specs/engram/spec.md) | MEM-01-persistencia, MEM-01-cruzada | test-plan del cambio + docs/evidence/tdd/MEM-01.md |
| MEM-02 | Independencia y autoridad | [01-engram](../openspec/changes/01-engram/specs/engram/spec.md) | MEM-02-apagado, MEM-02-conflicto | test-plan del cambio + docs/evidence/tdd/MEM-02.md |
| COR-01 | Admisión con procedencia | [02-corpus](../openspec/changes/02-corpus/specs/corpus/spec.md) | COR-01-valido, COR-01-invalido | test-plan del cambio + docs/evidence/tdd/COR-01.md |
| COR-02 | Unidades y tablas | [02-corpus](../openspec/changes/02-corpus/specs/corpus/spec.md) | COR-02-tabla, COR-02-ambigua | test-plan del cambio + docs/evidence/tdd/COR-02.md |
| COR-03 | Versionado e idempotencia | [02-corpus](../openspec/changes/02-corpus/specs/corpus/spec.md) | COR-03-repeticion, COR-03-cambio | test-plan del cambio + docs/evidence/tdd/COR-03.md |
| RET-01 | Cuatro modos comparables | [03-retrieval](../openspec/changes/03-retrieval/specs/retrieval/spec.md) | RET-01-ranking, RET-01-fallo-vector | test-plan del cambio + docs/evidence/tdd/RET-01.md |
| RET-02 | Idioma y compatibilidad del índice | [03-retrieval](../openspec/changes/03-retrieval/specs/retrieval/spec.md) | RET-02-e5, RET-02-incompatible | test-plan del cambio + docs/evidence/tdd/RET-02.md |
| RET-03 | Diversidad y contexto | [03-retrieval](../openspec/changes/03-retrieval/specs/retrieval/spec.md) | RET-03-diversidad, RET-03-presupuesto | test-plan del cambio + docs/evidence/tdd/RET-03.md |
| API-01 | Contrato de consulta | [04-agents-backend](../openspec/changes/04-agents-backend/specs/agents-backend/spec.md) | API-01-valida, API-01-invalida | test-plan del cambio + docs/evidence/tdd/API-01.md |
| AGT-01 | Investigación y verificación dinámicas | [04-agents-backend](../openspec/changes/04-agents-backend/specs/agents-backend/spec.md) | AGT-01-revision, AGT-01-limite | test-plan del cambio + docs/evidence/tdd/AGT-01.md |
| AGT-02 | Citas y abstención | [04-agents-backend](../openspec/changes/04-agents-backend/specs/agents-backend/spec.md) | AGT-02-citas, AGT-02-faltantes, AGT-02-inventada | test-plan del cambio + docs/evidence/tdd/AGT-02.md |
| AGT-03 | Presupuesto y errores | [04-agents-backend](../openspec/changes/04-agents-backend/specs/agents-backend/spec.md) | AGT-03-agotado, AGT-03-schema | test-plan del cambio + docs/evidence/tdd/AGT-03.md |
| UI-01 | Experiencia de consulta y fuentes | [05-frontend-hardening](../openspec/changes/05-frontend-hardening/specs/frontend-hardening/spec.md) | UI-01-respuesta, UI-01-aclaracion, UI-01-error | test-plan del cambio + docs/evidence/tdd/UI-01.md |
| UI-02 | Estado aislado y sin duplicación | [05-frontend-hardening](../openspec/changes/05-frontend-hardening/specs/frontend-hardening/spec.md) | UI-02-rerun, UI-02-sesiones | test-plan del cambio + docs/evidence/tdd/UI-02.md |
| SEC-01 | Acceso y entradas no confiables | [05-frontend-hardening](../openspec/changes/05-frontend-hardening/specs/frontend-hardening/spec.md) | SEC-01-sin-clave, SEC-01-injection, SEC-01-traversal | test-plan del cambio + docs/evidence/tdd/SEC-01.md |
| OPS-01 | Caché y trazas | [05-frontend-hardening](../openspec/changes/05-frontend-hardening/specs/frontend-hardening/spec.md) | OPS-01-hit, OPS-01-invalidate, OPS-01-redaccion | test-plan del cambio + docs/evidence/tdd/OPS-01.md |
| EVA-01 | Benchmark congelado | [06-evaluation-delivery](../openspec/changes/06-evaluation-delivery/specs/evaluation-delivery/spec.md) | EVA-01-split, EVA-01-sin-soporte | [contrato](evidence/tdd/06-benchmark-contract.md) + [cierre humano](evidence/tdd/EVA-01-human-review-freeze.md) |
| EVA-02 | Métricas y ablaciones reales | [06-evaluation-delivery](../openspec/changes/06-evaluation-delivery/specs/evaluation-delivery/spec.md) | EVA-02-comparacion, EVA-02-negativo | test-plan del cambio + docs/evidence/tdd/EVA-02-budgeted-live.md |
| DEL-01 | Entrega preproductiva | [06-evaluation-delivery](../openspec/changes/06-evaluation-delivery/specs/evaluation-delivery/spec.md) | DEL-01-reproduccion, DEL-01-informe | test-plan del cambio + docs/evidence/tdd/DEL-01.md |

## Prioridades

Must: requisitos anteriores. Should: segundo anotador humano y revisión independiente de PR. Could: métricas opcionales adicionales y más documentos después del MVP. No reducir alcance Must sin registrar desvío frente a consigna/usuario.

## Estado pendiente de confirmación

Fecha calendario Teoría 7; modalidad individual/grupal y responsables humanos; credenciales/proveedor LLM; hardware real de ejecución; acceso/licencia de cada fuente; versiones compatibles resueltas en uv.lock. Son verificaciones de inicio, no motivos para inventar resultados ni para cambiar el stack confirmado.
