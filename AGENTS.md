# Contrato de trabajo para agentes de desarrollo

## Orden de lectura

README.md → docs/requirements.md → docs/architecture.md → ADR aplicables → docs/tdd.md. Leer
proposal/design/spec/tasks de OpenSpec sólo cuando el cambio se clasifica como SDD.
Las instrucciones explícitas del usuario prevalecen. Engram orienta; ante discrepancias se verifica Git y se actualiza la memoria. Una nota de memoria nunca aprueba un cambio de contrato.

## Selección de estrategia

ODD es la puerta de entrada de toda implementación: confirmar que el pedido autoriza cambios,
explorar sólo lo necesario, resolver únicamente incertidumbres que cambien alcance o riesgo y
elegir el camino mínimo verificable. Este repositorio adopta deliberadamente una variante híbrida:
el camino directo de ODD se usa para cambios pequeños y SDD/OpenSpec se conserva para el trabajo
sustancial. La implementación canónica de ODD no conserva SDD; esta excepción es política local.

Un cambio puede seguir el camino ODD directo sólo si está entendido, tiene riesgo contenido y se
puede retomar con el pedido original más `git diff`. No crean por rutina OpenSpec, ADR, Issue ni un
archivo de evidencia separado los cambios localizados y reversibles que no alteran contratos
públicos, límites de arquitectura, modelos o migraciones de datos, seguridad, despliegue, protocolo
de evaluación ni decisiones científicas.

Usar SDD cuando falla esa prueba de reanudación o el cambio es contractual o de alto riesgo:
nuevas capacidades, varios pasos significativos, API/schema público, arquitectura, datos/corpus,
seguridad, infraestructura, evaluación, defaults científicos o trabajo que necesita varios PR. El
número de archivos o líneas no decide la clasificación. Ante duda material sobre alcance o riesgo,
resolverla antes de escribir; si persiste, clasificar como SDD.

## Flujo ODD para cambios pequeños

1. Confirmar el resultado autorizado y explorar la superficie afectada.
2. Preguntar sólo si la respuesta cambia alcance, impacto irreversible, permisos/seguridad, costo
   de verificación, efectos externos, riesgo residual aceptado o forma de entrega.
3. Aplicar la prueba de camino directo: entendido, riesgo contenido y reanudable desde pedido más
   `git diff`. Si falla, pasar a SDD antes de escribir código.
4. Para comportamiento nuevo o corregido, escribir primero la prueba focal y observar RED.
5. Implementar el mínimo cambio, obtener GREEN y ejecutar la regresión afectada.
6. Revisar typing, lint y límites sólo en la superficie alcanzada; ampliar si aparece riesgo.
7. Registrar comandos y resultado en el PR. Issue y archivo `docs/evidence/tdd/*` son opcionales.
8. Integrar con CI verde. Si el alcance crece o aparece alto riesgo, detener y reclasificar.

## Flujo SDD para cambios grandes

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

En SDD, no expandir alcance sin actualizar spec/ADR. En ODD, no cruzar límites contractuales sin
reclasificar. Documentar limitaciones en vez de ocultarlas con fallbacks. No activar cloud/sync de
Engram por defecto. No enviar emails ni publicar resultados académicos sin instrucción explícita.

## Cierre

Cumplir la Definition of Done proporcional de `docs/tdd.md`. No archivar cambios OpenSpec antes de
implementarlos y verificarlos. No declarar una memoria compartida entre herramientas hasta
comprobar lectura cruzada real.
