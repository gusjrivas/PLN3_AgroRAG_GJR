# TDD y calidad transversal

Requisito del usuario aplicable a todo comportamiento nuevo o corregido: backend, frontend, agentes, RAG, scripts de ingesta/evaluación y contratos de arquitectura. No presentar porcentaje de cobertura como prueba de TDD.

## Ciclo verificable

1. Escenario identificado en OpenSpec y test de comportamiento que falla por la capacidad ausente.
2. RED: ejecutar el test, registrar comando, exit code y fallo esperado. Un error de credenciales/entorno no sustituye un fallo funcional.
3. GREEN: implementación mínima; ejecutar el mismo test y guardar resultado.
4. REFACTOR: mejorar estructura sin cambiar contrato, volver a ejecutar suite afectada y controles estáticos.
5. Registrar evidencia en docs/evidence/tdd/<task-id>.md con hashes/commits. No es obligatorio publicar commits rotos en main: puede preservarse un patch del test y log del rojo antes de un commit verde.

Para código heredado: primero tests de caracterización verdes sobre lo existente; para cada diferencia nueva, test rojo antes de adaptar. No fabricar historia roja retroactiva. Si ya se implementó algo fuera de TDD, explicitar deuda y cubrir el riesgo; no declarar que se cumplió el proceso.

## Capas de pruebas

| Capa | Herramienta / aislamiento | Casos obligatorios |
|---|---|---|
| Dominio | pytest, Hypothesis, puertos fake | IDs estables, límites, presupuesto, evidencia vacía, reglas de estados |
| Arquitectura | import-linter o AST bajo pytest | UI sin import backend; dominio sin frameworks; application sin infrastructure |
| API/contrato | TestClient/httpx y overrides | schemas, auth, errores, timeout, invariantes de citas |
| Retrieval | fixtures pequeñas + adaptadores fake | ranking, fusión, diversidad por source_id, filtros, incompatibilidad de versión |
| Agentes | respuestas estructuradas guionadas | aprobar, revisar una vez, aclarar, abstenerse, salida inválida, presupuesto agotado |
| Frontend | Streamlit AppTest + cliente HTTP fake | consulta, error, espera, citas, aclaración, rerun sin duplicar pedido |
| Integración real | marca integration_live | Pinecone/LLM con corpus y namespace aislados; requiere secretos locales |
| E2E | Playwright Python | browser → Streamlit → API real local → adaptadores fake; smoke real separado |
| Evaluación científica | benchmark fijo y anotación | recuperación, soporte factual, efecto del verificador, latencia/tokens |

## Calidad propuesta

pytest-cov con branch coverage global ≥85% y ≥90% en domain/application como puertas iniciales del proyecto, no exigencias numéricas de la cátedra. Todo flujo crítico descrito debe tener prueba aunque se alcance la cobertura. No excluir código para inflar métricas. Objetivos se modifican con justificación versionada, nunca para esconder fallos.

Ruff lint/formato, mypy sobre src, contratos de importación, tests deterministas y validación OpenSpec son checks de PR. Dependencies con uv.lock y auditoría de vulnerabilidades con política de severidad documentada. Las versiones se resuelven en 00; este plan no asegura compatibilidad sin ejecutarlas.

CI rápida no llama a servicios pagos, no descarga modelos grandes y no exige secretos. Job integration_live manual usa namespace efímero y presupuesto; nunca usa producción. CI de frontend incluye AppTest; E2E smoke se ejecuta con stack local reproducible. Cambios en Docker/config se validan con pruebas de arranque o config, no se afirma TDD para prosa de ADR.

## Definition of Done por tarea

- Escenario satisfecho, test rojo/verde/refactor trazable y review del diff.
- Tests de regresión relevantes, lint, tipos y límites de arquitectura correctos.
- Manejo de errores, seguridad y logs de la funcionalidad cubiertos.
- Spec/ADR/documentación sincronizados y evidencia enlazada desde tasks.
- Resultados reales separados de mocks y estimaciones.
- Sin secretos, dependencias innecesarias ni cambios a Teoria*.

## Definition of Done de release

Todas las puertas anteriores, instalación limpia reproducida, integración real verificada, corpus y benchmark congelados, evaluación reportada aunque no muestre mejora, PDF final y demo de 15 minutos. Reviewer registra riesgos restantes. Ningún artefacto de planificación cuenta como funcionalidad terminada.
