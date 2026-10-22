# Organización del desarrollo por agentes

## Roles

| Rol | Propiedad inicial | Entrega |
|---|---|---|
| Coordinador/arquitecto | contratos, ADR, configuración, lockfile e integración | tareas delimitadas y decisiones coherentes |
| RAG/datos | ingesta, catálogo, índices y retrieval | evidencia reproducible y medición de recuperación |
| Backend/agentes | casos de uso, orquestación, API | respuestas verificadas y errores tipados |
| Frontend | src/agro_rag_ui, tests/ui y E2E | estados claros, cliente API desacoplado |
| Evaluador/revisor | benchmark, métricas y revisión | resultados independientes y hallazgos |

Son roles de trabajo, no cinco procesos que deban correr permanentemente. Máximo dos implementadores paralelos inicialmente, con tareas disjuntas. Tests de cada función los escribe su implementador antes del código; el evaluador no recibe al final la responsabilidad de inventar tests para todo.

## Handoff obligatorio

task_id; escenario OpenSpec; branch/worktree; commit base; rutas permitidas; contrato consumido; dependencias; prueba roja; comandos verdes; limitaciones; siguiente paso. No integrar por una afirmación de otro agente sin revisar evidencia.

## Engram

Proyecto lógico único `pln3-agro-rag` en el repositorio independiente. Memorias en español y claves estables: architecture/<adr>, corpus/<source-id>, debugging/<issue>, handoff/<task-id>. Guardar qué, por qué, dónde y aprendizaje, enlazando commit y rutas. No guardar claves ni el corpus completo. Una memoria no cambia la responsabilidad de archivos ni funciona como lock.

Sesiones consultan proyecto actual, contexto y búsqueda focalizada antes de repetir decisiones. Herramientas concretas se descubren según cliente: mem_current_project, mem_context, mem_search, mem_get_observation, mem_save y mem_session_summary cuando estén disponibles. IDs de sesión provienen del host, no se inventan.

Si Engram falla, registrar handoff en el PR y continuar trabajo autorizado desde Git; mantener tarea de integración abierta. Git/SDD sigue siendo la fuente auditable. Lectura cruzada Codex/Claude sólo se declara después de comprobar que ambos apuntan a la misma instancia y proyecto.

## Separación académica

Los agentes de desarrollo ayudan a construir. Los agentes investigador y verificador del producto satisfacen la consigna. El informe declara herramientas de asistencia utilizadas, autoría humana responsable y verificaciones efectuadas.
