# Estado actual y próxima sesión

Actualización: 13/11/2026. La validación complementaria está cerrada y documentada; no hay que
repetir el bootstrap ni interpretar listas históricas como funcionalidades aún inexistentes.

- V1 local: API/UI, corpus piloto de 27 fragmentos, agentes, citas, caché y evaluación implementados.
- Bug #51: corregido por PR #52; regresión verificada con cero llamadas al modelo.
- Aceptación: 19 conformes y 8 incompletos según rúbrica. Ver [evidencia](evidence/acceptance-27/README.md).
- Garak: cobertura completada sin hallazgos confirmados para `d38814b4`. No repetirlo en la próxima
  fase, por instrucción del usuario; conservar su alcance de versión.
- META-01..04: integradas. META-05..07: pendientes; no declararlas terminadas.
- Documentación académica: [informe](report.md), [PDF vigente](../output/pdf/agro-rag-report-2026-11-13.pdf),
  [guion de 15 minutos](demo.md) y [entrega](delivery.md).

## Siguiente paso

Preparar después un entorno limpio para la versión de entrega: checkout y dependencias fijadas,
corpus con hashes, suite offline, arranque API/UI y revisión de la demo. No ejecutar Garak.
Registrar commit, hardware y resultados reales. Esta fase todavía no se realizó.

Antes de entregar faltan ensayo, confirmación de modalidad y fecha calendario de Teoría 7 y
envío autorizado. La promoción formal V2 y la extensión de metadatos tienen seguimiento separado.

## Reglas de continuidad

Conservar cambios locales, `.env` y datos. Seguir [run-local](run-local.md) o
[run-containerized](run-containerized.md) según el entorno. Leer README, requisitos, arquitectura,
ADR aplicables y TDD; usar ODD directo para cambios pequeños y OpenSpec para trabajo contractual.
La planificación original permanece en [plan](plan.md); el estado se decide por evidencia y Git.
