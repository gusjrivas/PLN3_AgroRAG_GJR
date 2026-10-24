# Evidencia TDD: paquete DEL-01

Fecha: 24/10/2026. Responsable y revisor disponible: misma sesión Codex; revisión humana
pendiente. Rama: `feat/06-delivery-package`. Propiedad: verificador, builder/fuente PDF, guion,
runbook y trazabilidad DEL-01.

## Alcance

Se incorporan un informe técnico reproducible, guion cronometrado de 15 minutos, generador PDF y
validación offline de ocho artefactos. El informe separa verificación de ingeniería, smoke real
preliminar y resultados científicos aún inexistentes. No se inventan qrels, revisión agronómica,
modalidad, fecha académica ni resultados E1/E2/E3.

## RED

Comando:
`.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.tmp\delivery-red tests\unit\test_delivery.py`.

Resultado: exit code 1, `3 failed`; no existían `agro_rag.evaluation.delivery` ni
`scripts.build_report`.

Un segundo RED agregó el comando público de verificación. El test focalizado falló con exit 1
porque argparse rechazó `verify-delivery` como opción inexistente.

## GREEN

Se agregaron `validate_delivery`, `agro-rag verify-delivery`, `build_report.py`, la fuente del
informe y el guion. El primer GREEN detectó un falso positivo: la subcadena `TODO` dentro de
“Metodología”. Se corrigió la regla para aceptar sólo marcadores como palabras completas.

Resultado focalizado final: exit 0, `3 passed in 1.18s`; Ruff, formato y mypy focalizados aprobados.
El verificador real informó ocho artefactos con SHA-256 y no imprimió variables ni secretos.

## PDF y revisión visual

La creación se registró con el marcador obligatorio de la skill PDF. Poppler no estaba disponible;
se instaló PyMuPDF sólo en el entorno local de trabajo para renderizar, sin modificar dependencias
versionadas. Se inspeccionaron todas las páginas como PNG.

La primera versión tenía 14 páginas correctas pero demasiado espacio en blanco. La segunda redujo
a 8 y reveló una frase huérfana. El ajuste final produjo 7 páginas: portada, encabezados/pies,
tablas, código y referencias legibles, sin superposición, recorte ni glifos rotos.

## REFACTOR y cierre

- Suite completa: exit 0, `144 passed, 2 deselected in 5.86s`.
- Ruff check/formato: exit 0, 141 archivos formateados.
- mypy: exit 0, 32 archivos sin errores.
- import-linter: exit 0, 2 contratos mantenidos.
- OpenSpec estricto completo: exit 0, 7 cambios válidos.
- Instalación limpia y CI: pendientes de registrar.
- Revisión del diff y PDF: misma sesión; revisión humana pendiente.

## Limitaciones abiertas

- El benchmark de 60 casos y las corridas reales E1/E2/E3 siguen pendientes.
- Modalidad individual/grupal y fecha calendario de Teoría 7 requieren confirmación humana.
- La entrega no se envió por correo y no se creó release tag.
