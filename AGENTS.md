# Contrato de trabajo para agentes de desarrollo

## Orden de lectura

README.md → docs/requirements.md → docs/architecture.md → ADR aplicables → proposal/design/spec/tasks del cambio activo → docs/tdd.md.
Las instrucciones explícitas del usuario prevalecen. Engram orienta; ante discrepancias se verifica Git y se actualiza la memoria. Una nota de memoria nunca aprueba un cambio de contrato.

## Flujo obligatorio

1. Seleccionar una tarea sin dependencias abiertas y registrar responsable, rama y archivos de propiedad en el PR/Issue.
2. Leer las memorias relevantes del proyecto confirmado, si Engram está disponible; no inventar herramientas ni sesiones.
3. Escribir primero el test observable del escenario. Ejecutarlo y registrar su fallo esperado (RED).
4. Implementar el mínimo cambio que lo satisface y ejecutar el test (GREEN).
5. Refactorizar, ejecutar suite afectada, revisar contratos, typing y límites de arquitectura (REFACTOR).
6. Registrar comandos, códigos de salida, commit y evidencia en docs/evidence/tdd/<task-id>.md. Nunca fabricar la fase roja de una implementación ya existente.
7. Completar tareas sólo con evidencia. Guardar en Engram decisión/hallazgo y handoff breve con enlaces a archivos y commit.

## Límites técnicos

Python para backend y frontend. UI sólo consume API por HTTP; no importa agentes, índices ni SDK de modelos. Dominio no importa FastAPI, Streamlit, LangGraph ni proveedores. Inyección desde bootstrap. No I/O de red ni carga de modelos al importar módulos.
Preservar Teoria*. Reusar ejemplos con trazabilidad, pruebas de caracterización y adaptación controlada. No descargar pesos ni consultar LLMs en pruebas unitarias.

Un coordinador integra. Se permite delegación de desarrollo por responsabilidades, con worktree/rama por agente y máximo dos implementadores simultáneos mientras los contratos se estabilizan. No editar el mismo archivo desde dos agentes. Un revisor distinto comprueba el cambio antes de integrarlo cuando esté disponible; registrar si la revisión fue realizada por la misma sesión.

No expandir alcance sin actualizar spec/ADR. Documentar limitaciones en vez de ocultarlas con fallbacks. No activar cloud/sync de Engram por defecto. No enviar emails ni publicar resultados académicos sin instrucción explícita.

## Cierre

Cumplir Definition of Done en docs/tdd.md. No archivar cambios OpenSpec antes de implementarlos y verificarlos. No declarar una memoria compartida entre herramientas hasta comprobar lectura cruzada real.
