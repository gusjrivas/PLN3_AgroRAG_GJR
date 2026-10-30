# OpenSpec y SDD del TP

SDD es el método; OpenSpec organiza su documentación. Se usa schema `spec-driven`. Cada cambio contiene proposal.md, design.md, tasks.md y specs/<capability>/spec.md, con metadata .openspec.yaml.

El comportamiento todavía no implementado vive en changes/. `specs/` queda sin capacidades hasta que se implementen, verifiquen y archiven los cambios. No copiar propuestas a specs actuales para aparentar avance. Los ADR están en docs/adr y las pruebas de aceptación enlazan escenarios por ID.

Orden: 00-foundation → 01-engram → 02-corpus → 03-retrieval → 04-agents-backend →
05-frontend-hardening → 06-evaluation-delivery. El cambio 06 está archivado y su contrato estable
vive en `openspec/specs/evaluation-delivery/spec.md`; 00–05 conservan su historial activo hasta una
auditoría de archivo específica. docs/plan.md mantiene el mapa de dependencias.

Desde la raíz del nuevo repositorio: `openspec validate --all --strict`. La validez de formato no demuestra ejecución, corrección ni cumplimiento de TDD. Integrar únicamente cambios verificados. Para tareas posteriores, modificar el delta vigente o abrir uno nuevo si cambia capacidad ya archivada.
