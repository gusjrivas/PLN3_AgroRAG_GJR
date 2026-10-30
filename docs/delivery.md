# Entrega académica y demo

Estado técnico al 29/10/2026: informe reproducible, guion y runtime configurable de retrieval
semántico implementados; benchmark de 60 casos congelado; E1/E2 y piloto mínimo E3 ejecutados en
`dev`; revisión humana E2 cerrada con 12 PASS y 6 FAIL. La entrega académica definitiva todavía
requiere revisión final del diff/PDF, ensayo, modalidad y fecha calendario de Teoría 7. No se envió
correo ni se publicó fuera del repositorio.

La cátedra solicita repositorio funcional, informe técnico PDF y exposición final de 15 minutos. Fecha máxima: clase Teoría 7; fecha calendario aún por confirmar. Entrega por correo a ambos docentes cuando el usuario lo autorice. El plan no envía mensajes.

## Informe

1. Objetivo, problema y alcance (tomate/lechuga).
2. Corpus, procedencia, selección y limitaciones.
3. Arquitectura y flujo con dos agentes, diagramas y decisiones relevantes.
4. Implementación Python: reuso del ejemplo y aportes propios, TDD y calidad preproductiva.
5. Evaluación: dataset, protocolo, métricas, configuraciones y resultados reales.
6. Ejemplos: respuesta con evidencia, corrección entre agentes, aclaración/abstención y fallo operativo.
7. Conclusiones, costos, limitaciones y mejoras futuras.
8. Si es grupal: tareas, responsables humanos y estado. Agentes de programación no sustituyen responsables humanos.
9. Referencias y declaración de asistencia de IA utilizada.

La fuente está en `docs/report.md`; `scripts/build_report.py` genera
`output/pdf/agro-rag-report.pdf`. El PDF de 7 páginas fue renderizado e inspeccionado completo. No
se inventó límite de páginas ni se ocultaron resultados pendientes.

## Exposición de 15 minutos

El guion ejecutable está en `docs/demo.md`: 2 min problema/corpus; 3 min arquitectura/reuso; 4 min
demo; 4 min evaluación/costo; 2 min conclusiones/limitaciones. El respaldo debe identificarse como
grabación; no se presentan fixtures como inferencia en vivo.

## Reproducción

README y `docs/run-local.md` contienen requisitos, `uv sync --frozen`, configuración sin secretos,
obtención del corpus, ingesta, arranque API/UI y pruebas. `agro-rag verify-delivery --root .`
comprueba offline ocho artefactos y emite sus hashes. El release tag queda pendiente hasta completar
la evaluación científica; las instrucciones no dependen de rutas absolutas de una notebook.
