# Evidencia TDD: backup, restore y rollback

Fecha: 30/10/2026. Responsable y revisión: misma sesión coordinadora; revisión humana pendiente en
MR #30. Rama: `feat/v2-container-foundation`. Propiedad: backup/restore de catálogo, CLI, overlay de
operaciones, contratos y runbook.

Commit de implementación: `ea5d87f` (`feat: add verified catalogue rollback`).

## RED

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp/pytest-backup-v2-red tests/integration/test_catalogue_backup.py
```

Resultado: exit 1, `3 failed`: no existía el módulo de backup ni los comandos CLI. El contrato del
overlay produjo otro fallo porque `compose.ops.yaml` no existía.

## GREEN y garantías

- Backup valida primero el catálogo activo y empaqueta sólo puntero+snapshot con hashes, versión,
  conteo, semver, commit e imagen API.
- Restore rechaza entries extra/duplicadas, metadata inválida y alteraciones SHA-256 antes de
  cambiar `active.json`.
- El snapshot se valida como SQLite legible y con conteo/versión correctos; el puntero se activa al
  final de forma atómica. Snapshots anteriores permanecen.
- Jobs Compose sin red separan catálogo RO/RW y backup RW/RO, usan rootfs read-only, límites,
  `cap_drop: ALL` y `no-new-privileges`.

Suite dirigida de implementación y contratos: exit 0, `9 passed`; Ruff y mypy: exit 0.

## Ensayo Docker aislado

Se creó exclusivamente `agrorag_catalogue_v2_rollback_test`, se ingirió el corpus de 27 evidencias,
se generó un ZIP y se reemplazó `active.json` por un valor de candidata fallida. El
job restore recuperó versión
`e9929440f552b1c7be1349118a1ee98c6cdba41fbd2e2ce05343247c918dfb7d`; API quedó healthy y
`/v1/corpus` devolvió 27 evidencias.

En un segundo volumen aislado se restauró el mismo ZIP y se arrancó la imagen anterior local
`agrorag-api:ops-v2-test`. Health/version y corpus aprobaron con la misma versión y 27 evidencias,
demostrando compatibilidad de rollback. Ambos volúmenes de prueba fueron inspeccionados por nombre y
eliminados; no se tocó el volumen por defecto/usuario.

Tras agregar la identidad de imagen al manifiesto se repitió el recorrido con la implementación
final: ZIP de 22.420 bytes, campo `image=agrorag-api:rollback-v2-current`, dos archivos declarados,
restore a un volumen limpio y arranque healthy con la imagen anterior. Los volúmenes exactos
`agrorag_catalogue_v2_rollback_current_source` y `..._target` también fueron inspeccionados y
eliminados.

El ensayo valida mecánica local y compatibilidad, no almacenamiento off-host, registry ni rollback
de staging. Esas evidencias requieren la release publicada y el ambiente autorizado.
