# Evidencia TDD: Compose local y persistencia del catálogo

Fecha: 29/10/2026. Responsable y revisión: misma sesión coordinadora; revisión humana pendiente en
MR #30. Rama: `feat/v2-container-foundation`. Propiedad: `compose.yaml`, `compose.dev.yaml`,
healthcheck, Dockerfile, pruebas de contrato, runbook, OpenSpec y esta evidencia.

## RED

`tests/architecture/test_compose_contract.py` exige servicios API/UI/admin, DNS interno, perfil,
healthchecks, loopback, volumen read-only para API y read-write para administración.

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp/pytest-compose-v2-red tests/architecture/test_compose_contract.py
```

Resultado: exit 1, `3 failed`: ambos archivos Compose estaban ausentes.

El probe local necesitaba distinguir liveness de readiness sin debilitar el endpoint. El test
`test_liveness_probe_does_not_require_or_send_reader_key` terminó inicialmente con exit 1 porque el
healthcheck sólo aceptaba `ready` y exigía key. GREEN agregó el estado esperado tipado: `ok` no
envía credenciales; `ready` sigue fail-closed y autenticado.

## GREEN y contrato

`compose.yaml` define imágenes/targets, red, healthchecks y volumen; `compose.dev.yaml` agrega sólo
puertos loopback, reader local y el job admin sin red. El primer GREEN reveló que Compose omite
perfiles inactivos en `config`; el test se corrigió para renderizar explícitamente `--profile admin`
sin cambiar el contrato. Resultado dirigido final: exit 0, `7 passed`.

El runtime crea `/var/lib/agrorag/catalogue` con ownership 10001 antes de montar el volumen. API lo
recibe read-only; el job administrativo, read-write, con `./data` read-only y `network_mode: none`.

## Ensayo real

Se usaron puertos `18000/18501`, reader sintética y volúmenes exclusivos de prueba; se confirmó que
no existían antes de crearlos. Docker Compose v5.1.3 ejecutó:

1. Build API/UI/admin: exit 0.
2. Ingesta: exit 0, versión
   `e9929440f552b1c7be1349118a1ee98c6cdba41fbd2e2ce05343247c918dfb7d`, 27 evidencias.
3. `up -d --wait`: API y UI healthy.
4. API `/health/live`: `ok`; `/v1/corpus`: misma versión y 27 evidencias.
5. Preview BM25 real: 4 evidencias para `riego`, cultivo `tomato`.
6. Escritura desde API al catálogo: rechazada por el montaje read-only.
7. `down` y segundo `up --wait`: versión persistió sin reingesta.
8. Dos ingestas consecutivas: misma versión y 27/27 evidencias.

Los contenedores/red se eliminaron y `down -v` se aplicó únicamente a los volúmenes de prueba
`agrorag_catalogue_v2_test` y `agrorag_catalogue_v2_idempotence`, creados por esta sesión. El volumen
local/productivo por defecto no fue tocado.

CMP-V2-02 permanece abierto hasta automatizar browser→UI→API en Compose y CI. El overlay productivo,
backup/rollback y garak tampoco se declaran terminados.

Verificación de cierre del corte: suite offline `236 passed, 2 deselected`; Ruff check/formato,
mypy estricto (37 archivos), 2 contratos import-linter, Compose config y OpenSpec 07 terminaron con
exit 0. La revisión del diff fue realizada por la misma sesión; revisión humana pendiente en MR #30.
Commit funcional: `6bc86b1`.
