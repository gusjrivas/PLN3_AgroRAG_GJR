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

## ODD y SDD

ODD recibe primero toda solicitud de implementación: autorización, exploración proporcional,
resolución de incertidumbre material, clasificación, implementación y verificación proporcional.
El proyecto usa su camino directo para correcciones localizadas, ajustes de texto/UI o refactors
internos reversibles sin cambio de contrato. La trazabilidad queda en el PR y no se crea OpenSpec,
ADR, Issue ni evidencia separada por rutina.

Se conserva **Spec-Driven Development (SDD)** como adaptación local para capacidades sustanciales o
cambios que afectan API, schemas públicos, arquitectura, persistencia/corpus, seguridad,
infraestructura, evaluación, defaults o coordinación entre varios cortes. SDD mantiene OpenSpec,
propiedad explícita, grafo de dependencias, evidencia y cierre transversal. ODD canónico retiró SDD;
la combinación de ambos es una decisión explícita de este repositorio.

La prueba práctica del camino directo es que el cambio esté entendido, tenga riesgo contenido y
pueda retomarse con el pedido original más `git diff`. El tamaño del diff y la cantidad de archivos
no deciden. Un cambio de una línea en autenticación o en un contrato de datos sigue siendo SDD; un
bug localizado con prueba clara puede ser ODD. Si un corte ODD crece hasta cruzar uno de esos
límites, se pausa y reclasifica antes de continuar.

La delegación tampoco se decide por tamaño. Se trabaja inline por defecto y sólo se delega por una
razón concreta: unidades de comportamiento independientes con superficies disjuntas, exploración
acotada que excede el contexto útil o verificación independiente de un riesgo alto. Código, prueba
y documentación de una misma conducta pertenecen al mismo implementador.

Referencias metodológicas: [reglas oficiales de activación de ODD](https://github.com/Gentleman-Programming/gentle-ai/blob/main/docs/trigger-rules.md),
[release v4.0.0 que retiró SDD](https://github.com/Gentleman-Programming/gentle-ai/releases/tag/v4.0.0)
y [reglas para commits por unidad de trabajo](https://github.com/Gentleman-Programming/gentle-ai/blob/main/internal/assets/skills/work-unit-commits/SKILL.md).

## Handoff SDD

task_id; escenario OpenSpec; branch/worktree; commit base; rutas permitidas; contrato consumido; dependencias; prueba roja; comandos verdes; limitaciones; siguiente paso. No integrar por una afirmación de otro agente sin revisar evidencia.

En ODD alcanza con objetivo observable, archivos cambiados, RED/GREEN cuando corresponda,
regresión ejecutada y limitaciones en el PR.

## Engram

Proyecto lógico único `pln3-agro-rag` en el repositorio independiente. Memorias en español y claves estables: architecture/<adr>, corpus/<source-id>, debugging/<issue>, handoff/<task-id>. Guardar qué, por qué, dónde y aprendizaje, enlazando commit y rutas. No guardar claves ni el corpus completo. Una memoria no cambia la responsabilidad de archivos ni funciona como lock.

Sesiones consultan proyecto actual, contexto y búsqueda focalizada antes de repetir decisiones. Herramientas concretas se descubren según cliente: mem_current_project, mem_context, mem_search, mem_get_observation, mem_save y mem_session_summary cuando estén disponibles. IDs de sesión provienen del host, no se inventan.

Si Engram falla, registrar handoff en el PR y continuar trabajo autorizado desde Git; mantener tarea de integración abierta. Git y la estrategia seleccionada (ODD/SDD) siguen siendo la fuente auditable. Lectura cruzada Codex/Claude sólo se declara después de comprobar que ambos apuntan a la misma instancia y proyecto.

## Separación académica

Los agentes de desarrollo ayudan a construir. Los agentes investigador y verificador del producto satisfacen la consigna. El informe declara herramientas de asistencia utilizadas, autoría humana responsable y verificaciones efectuadas.
