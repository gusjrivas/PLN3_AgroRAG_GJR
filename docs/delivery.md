# Entrega académica y demo

Estado documental al 13/11/2026: informe y guion actualizados con EVA-02, aceptación complementaria
y cierre de cobertura Garak. La campaña de 27 casos queda cerrada con 19 conformes y 8 respuestas
incompletas según la rúbrica; no se ocultan ni se presentan como corregidas. La evidencia está en
[acceptance-27](evidence/acceptance-27/README.md). Las evaluaciones tienen poblaciones y revisores
distintos y no se agregan en un único porcentaje.

La cobertura Garak ya se completó: API key, Base64 y prompt injection obtuvieron 32 respuestas
reales por familia sin detecciones; DAN cerró 15 falsos positivos, 0 confirmados y 0 dudosos.
El usuario indicó reutilizar esta evidencia y **no repetir Garak** en el siguiente entorno limpio.
Corresponde a la candidata `d38814b4`; la promoción formal V2 permanece pendiente.

La preparación documental no declara finalizado el producto completo: META-05..07 siguen abiertas.
El checkout limpio reprodujo la instalación, la ingesta, la API y el navegador. Se restauró la
compatibilidad del benchmark y se verificó una consulta con `hybrid_rerank` en un arnés local.
Quedan verificar el paquete final sobre su commit de entrega y ensayar la exposición.
No se envió correo ni se realizó una publicación académica.

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

La fuente está en `docs/report.md`; el PDF vigente es
[`agro-rag-report-2026-11-22.pdf`](../output/pdf/agro-rag-report-2026-11-22.pdf). Tiene siete páginas
e incluye el diagrama de flujo de consulta en la sección de arquitectura.
El archivo sin fecha conserva el cierre de octubre porque no se pudo sobrescribir en esta sesión.
Para regenerar el informe vigente, usar
`uv run python scripts/build_report.py --output output/pdf/agro-rag-report-2026-11-22.pdf`.
El test del repositorio exige de seis a siete páginas; es una restricción técnica local, no una
exigencia de la cátedra. La versión vigente fue renderizada y revisada completa.

## Exposición de 15 minutos

El guion ejecutable está en `docs/demo.md`: 2 min problema/corpus; 3 min arquitectura/reuso; 4 min
demo; 4 min evaluación/costo; 2 min conclusiones/limitaciones. El respaldo debe identificarse como
grabación; no se presentan fixtures como inferencia en vivo.

Se prepararon [nueve diapositivas editables](../output/presentations/agro-rag-catedra.pptx),
[copia PDF](../output/pdf/agro-rag-catedra.pdf) y [notas con tiempos y fuentes](presentation.md).
La validación estructural y de geometría no tuvo hallazgos; las nueve diapositivas se renderizaron
y revisaron. No se verificó la ejecución nativa en PowerPoint.

## Reproducción

README y `docs/run-local.md` contienen requisitos, `uv sync --frozen`, configuración sin secretos,
obtención del corpus, ingesta, arranque API/UI y pruebas. `agro-rag verify-delivery --root .`
comprueba offline ocho artefactos y emite sus hashes. `v0.1.0` identifica el cierre técnico; no
implica que se haya realizado el ensayo ni el envío académico. Las instrucciones no dependen de
rutas absolutas de una notebook.

El verificador comprueba el paquete base. El manifiesto
`docs/evidence/academic-closeout-2026-11-13.json` registra los hashes del cierre histórico,
incluidos su PDF fechado, las diapositivas y la evidencia de aceptación. El PDF del 22/11
se valida con la prueba de generación del informe y la revisión del renderizado.

## Próxima verificación en entorno limpio

1. Elegir y registrar el commit de entrega una vez integrado el cierre documental.
2. Preparar checkout, Python 3.12 y dependencias desde `uv.lock`; registrar SO y hardware.
3. Obtener corpus por el procedimiento con hashes y construir el catálogo sin copiar secretos.
4. Ejecutar suite offline y controles de calidad; verificar los artefactos de entrega.
5. Arrancar API/UI, verificar salud, fuentes y navegación. Una consulta real sólo si se decide
   comprobar el proveedor configurado; conservar su resultado sin repetir toda la campaña.
6. Reutilizar el informe Garak existente. No lanzar un nuevo scan.
7. Registrar resultados y ensayo; confirmar modalidad y fecha de entrega con la cátedra.

Este checklist es el trabajo posterior autorizado como siguiente fase, no evidencia de que ya
se haya realizado. La promoción productiva no se infiere de un arranque local.
