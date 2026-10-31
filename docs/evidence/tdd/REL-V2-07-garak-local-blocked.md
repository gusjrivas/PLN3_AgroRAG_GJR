# REL-V2-07 — primer scan Garak real local bloqueado

Fecha: 2026-10-31. Responsable y operador autorizado: Gustavo Julián Rivas. Rama documental:
`docs/garak-local-blocked-41ba62f`. Revisión técnica: misma sesión; revisión humana requerida antes
de integrar. Registro inicial: `f68e29f2e0129fc0209f9adce03963b0de4bcabe`. Este documento es
evidencia operacional real, no una fase TDD ni una certificación.

## Alcance autorizado

El usuario autorizó explícitamente un baseline acotado contra `gpt-4o`, con Garak 0.17.0, seed
`1729`, una generación y cap blando de 32 prompts por cada una de cuatro familias: API key,
jailbreak, Base64 y prompt injection. No se amplió ese alcance.

Runner inmutable:

```text
ghcr.io/gusjrivas/pln3_agrorag_gjr/garak-runner@sha256:9a56fcacf404a0668496747820c9529bfb1de880853fe9de2123ff1ea4270e61
```

Target: gateway HTTPS local autenticado de la candidata `41ba62f91d972d839342e0e531fddba16963fb82`.
Antes del scan, un smoke desde el mismo runner validó TLS con la CA de Caddy, autenticación, HTTP
200, commit exacto y catálogo `e9929440f552b1c7be1349118a1ee98c6cdba41fbd2e2ce05343247c918dfb7d`.
Los secretos se copiaron fuera del repositorio a un directorio `0700`, bajo UID/GID `10003:10003`.

## Ejecución observada

Inicio Garak: `2026-10-31T01:33:26Z`. Límite aplicado: 60 minutos, igual al workflow formal.
El runner operó no-root, read-only, sin capabilities, con 2 CPU, 8 GiB y evidencia externa.

La primera familia informó en consola `apikey.GetKey/apikey.ApiKey PASS 32/32`. Ese resultado aislado
no equivale a aprobación de la release. Durante la ejecución, los logs HTTP sanitizados de la API
registraron:

```text
POST /v1/query total: 129
HTTP 200:              39
HTTP 422:              90
HTTP 5xx:               0
```

El cap es blando; Garak efectuó al menos un intento/reintento adicional. Los `422` indican que los
payloads no atravesaron el contrato de entrada, por lo que no se cuentan como ataques evaluados ni
como casos seguros. No se inspeccionaron ni copiaron prompts o respuestas.

## Cierre y evidencia

A los 60 minutos el runner seguía activo y no había producido resumen sanitizado. Se detuvo de
forma controlada y terminó con código no exitoso. Resultado: **BLOCKED** por timeout y cobertura
incompleta; la candidata no queda promovible por este scan.

El artefacto parcial permanece fuera de Git:

```text
release_id: 0.2.0-sha.41ba62f-local-20261031T0117Z
raw JSONL: 77 líneas; 100115 bytes
sha256: c357af938257e48dec8a7a5cce6498c6b9a6302fab88cf88d24ba7385d20872e
summary: ausente
```

Al ser interrumpido antes del postproceso, el JSONL quedó inicialmente `0644`: `run_garak.py`
aplica `0600` sólo después de que termina el subproceso. El archivo estaba dentro de un ancestro
`0700`, pero se corrigió inmediatamente a `0600`, propietario `10003:10003`. Esto queda como deuda
de confidencialidad a resolver con TDD antes del siguiente scan.

Verificación posterior a `2026-10-31T02:34:32Z`: API, UI y gateway continuaron `healthy`. El costo
real del proveedor no fue medido por este harness; 39 respuestas HTTP 200 no prueban igual número
de llamadas ni permiten informar un costo inventado.

## Próximo corte requerido

1. Caracterizar qué límites de `question` causan `422` para cada probe sin debilitar el contrato
   público ni registrar payloads sensibles.
2. Hacer que el raw nazca `0600`, incluso ante señal, timeout o terminación abrupta.
3. Definir timeout por request y cierre global reproducible que produzca resumen bloqueante.
4. Repetir el baseline con presupuesto explícito; sólo un reporte completo admite triage humano.

## Validación del registro

```text
uv run pytest tests/unit/test_garak_policy.py tests/unit/test_garak_adapter.py \
  tests/architecture/test_garak_release_workflows.py \
  tests/architecture/test_garak_container_contract.py -q
exit 0; 14 passed

npx --yes @fission-ai/openspec@1.14.3 validate --all --strict
exit 0; 8 passed, 0 failed

git diff --check
exit 0
```

