# Evidencia: planificación de la PoC productiva containerizada

Fecha: 29/10/2026. Responsable y revisión: misma sesión coordinadora; no hubo un revisor técnico
independiente disponible. Rama: `plan/v2-containerized-poc`. Propiedad:
`docs/plan-v2-production-poc.md`, `docs/adr/015.md`, los índices de plan y ADR, y esta evidencia.

## Alcance y base verificada

`ARC-V2-01` es una tarea de decisión y planificación; no modifica comportamiento ejecutable. Por
eso no se fabricó una fase RED. El TDD observable comenzará con las fitness functions enumeradas en
el plan cuando se implemente la primera fase del refactor.

Se consultó el grafo local de `codebase-memory` y se contrastó con el código fuente porque el índice
reportó metadatos desactualizados y excluye documentación. La inspección confirmó:

- FastAPI y Streamlit son puntos de entrada separados.
- La UI consume el backend únicamente por HTTP.
- El bootstrap compone proveedores en runtime y falla de forma cerrada cuando falta el catálogo.
- No existen Dockerfile, archivos Compose ni infraestructura de gateway en la versión `v0.1.0`.

## Resultado

Los commits `1b72e40` y `4479afa` añaden:

- un plan por fases con tareas, fitness functions, riesgos y criterios de aceptación;
- ADR-015 para un monolito modular desplegado como servicios Compose;
- alcance explícito de PoC productiva en un único host, sin prometer alta disponibilidad;
- separación entre `api`, `ui`, `gateway`, trabajo administrativo de catálogo y proveedor local
  opcional;
- imágenes inmutables, secretos montados, catálogo de sólo lectura, ejecución sin privilegios,
  healthchecks, límites de recursos, observabilidad y rollback por digest/manifiesto.
- un runner garak containerizado y separado que prueba el gateway en staging, con baseline por
  probe/detector, gate de release, triage humano y tratamiento restringido de reportes.

La documentación deja explícito que garak aporta detección y evidencia adversarial, pero no
garantiza seguridad, validez científica, cumplimiento ni cobertura completa de una taxonomía.

No se añadieron imágenes, archivos Compose, dependencias garak ni cambios de runtime. La creación
del cambio OpenSpec y los tests RED de implementación quedan condicionados a la aceptación del ADR.

## Verificación

Comandos ejecutados desde la raíz:

- `git diff --check`: exit 0.
- `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp
  .tmp/pytest-arc-v2-garak tests/unit/test_delivery.py`: exit 0, `3 passed`.
- verificador local de enlaces Markdown relativos: exit 0, `links_ok`.
- `npx --yes @fission-ai/openspec@1.14.3 validate --all --strict`: exit 0, `7 passed, 0 failed`.

Una repetición previa de pytest sin `--basetemp` terminó con exit 1: Windows negó acceso al
directorio temporal global y dos tests no alcanzaron a ejecutarse. La repetición aislada dentro del
workspace aprobó; no hubo una falla de aserción ni un cambio de producto.

La revisión de consistencia del diff fue realizada por la misma sesión. El ADR permanece en estado
`Propuesto` y requiere revisión humana antes de iniciar la implementación.
