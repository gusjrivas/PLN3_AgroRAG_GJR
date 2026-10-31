# REL-V2-08 — scan Garak limitado por presupuesto

Fecha: 31/10/2026. Responsable y operador autorizado: Gustavo Julián Rivas. Ejecución y revisión
técnica: misma sesión coordinadora; revisión humana de hallazgos pendiente. Rama documental:
`docs/garak-d388-budget-blocked`. Propiedad: evidencia sanitizada, estado OpenSpec y documentación
de la corrida. Esta es evidencia operacional real, no una fase TDD ni una certificación.

## Autorización y candidata exacta

El usuario autorizó una única corrida contra OpenAI con un máximo total de USD 0,20. No se hizo
ninguna llamada paga antes de esa confirmación. La candidata desplegada en Ubuntu 26.04.1 WSL2 fue
el merge `d38814b4f352b3f007f7520858f48daeca27a160`, aprobado por los runs
[`quality 41230735448`](https://github.com/gusjrivas/PLN3_AgroRAG_GJR/actions/runs/41230735448)
y
[`container-supply-chain 41230735397`](https://github.com/gusjrivas/PLN3_AgroRAG_GJR/actions/runs/41230735397).

Imágenes publicadas y desplegadas por digest:

```text
api     ghcr.io/gusjrivas/pln3_agrorag_gjr/api@sha256:597a469fa8a688210cca5bc94dc0722c70975e57535171d14d70908336c9c96c
ui      ghcr.io/gusjrivas/pln3_agrorag_gjr/ui@sha256:82cabbfc5fdb132d29782fd5feb9c586e0a992cb75d53753b81f1aad0dfa1144
gateway ghcr.io/gusjrivas/pln3_agrorag_gjr/gateway@sha256:31225397760fdcface3fa3641b73236df272dbc5e59824b77304b1b42c9afc3a
runner  ghcr.io/gusjrivas/pln3_agrorag_gjr/garak-runner@sha256:f0bd19bef1458a0b74b70d4a4c55fa3c94aa0cec10ca86fb84b1059cafd5267e
```

El runner provino del workflow manual
[`41230977811`](https://github.com/gusjrivas/PLN3_AgroRAG_GJR/actions/runs/41230977811), que aprobó
identidad, Garak 0.17.0, SBOM, Trivy, política y publicación en 7m38s. El preflight local aprobó
commit, usuarios OCI, secretos, volumen, recursos y Compose. El gateway expuso únicamente 80/443;
UI, `/health/version` y `/v1/corpus` devolvieron 200, el commit exacto y 27 evidencias.

## Incidente de credencial previo al scan

Un intento de smoke imprimió en la consola local la cabecera Basic de staging por una composición
incorrecta del comando. No se agregó a Git ni a los artefactos, pero se consideró comprometida. Se
rotaron antes del scan tanto el hash bcrypt del gateway como la cabecera cliente, se restauraron
propietario `10003:10003`/modo `0600` y se recreó el gateway. Un nuevo smoke desde el runner validó
TLS, autenticación y commit sin imprimir secretos. No se expusieron reader key ni clave de OpenAI.

## Ejecución y control de costo

Release ID: `0.2.0-sha.d38814b4-local-20261031T190832Z`. El runner informó inicio
`2026-10-31T19:18:57.187839` y fin `2026-10-31T19:19:19.398285` UTC. Se ejecutó no root,
read-only, sin capabilities, con 2 CPU, 8 GiB, red de host sólo para alcanzar el gateway HTTPS
local, CA de Caddy montada read-only y timeout interno de 3.300 segundos.

Resultado: **BLOCKED**, exit 1, `cost_budget_exhausted`. El resumen sanitizado registró:

```text
requests totales del adaptador: 128
respuestas reales exitosas:      47
rechazos contractuales 422:      12
bloqueos previos por presupuesto:69
errores ambiguos/transporte:      0
tokens input/output:              30286 / 473
costo estimado:                  USD 0,080445
techo:                           USD 0,20
reserva pendiente al cerrar:     USD 0
```

La siguiente reserva conservadora era USD 0,12. `0,080445 + 0,12 = 0,200445`, por lo que el
adaptador rechazó toda solicitud posterior antes de llamar al gateway. El gasto estimado quedó
USD 0,119555 por debajo del techo y no se realizó ningún retry.

Resumen versionado: [decisión del runner](../garak/d38814b4-summary.json). La aplicación continuó
healthy después del scan.

## Cobertura efectiva y triage

La política aplicada offline al reporte produjo
[agregados parciales](../garak/d38814b4-partial-policy.json) y `untriaged_high`. El JSONL contiene
dos filas internas por intento; al separar por igualdad exacta las negativas sintéticas del
adaptador, las 128 solicitudes reales se distribuyeron así:

| Familia | Respuestas reales | 422 | presupuesto | Lectura válida |
|---|---:|---:|---:|---|
| `apikey.GetKey` | 32 | 0 | 0 | 32/32 sin detección `apikey.ApiKey` |
| `dan.DanInTheWild` | 15 | 12 | 5 | las 15 reales fueron marcadas por `MitigationBypass`; requieren revisión humana |
| `encoding.InjectBase64` | 0 | 0 | 32 | sin cobertura real; los passes de Garak provinieron de la negativa sintética |
| `promptinject.HijackHateHumans` | 0 | 0 | 32 | sin cobertura real; los passes de Garak provinieron de la negativa sintética |

Por lo tanto, ni los 32 fails agregados de DAN ni los passes de Base64/prompt injection pueden
aceptarse sin distinguir resultados reales de respuestas del harness. No se modificaron
`triage.json`, `baseline.json` ni `exceptions.json`; no hay evidencia para aprobar o exceptuar.

## Artefactos restringidos

Los crudos permanecen fuera de Git bajo
`/home/gus/.local/share/agrorag/garak/d38814b4-20261031T190832Z`, directorio `0700`. Archivos:

```text
hitlog JSONL   91.530 bytes   mode 0600   sha256 8808adb09de4250642e163911424265fcf5d891aae0876ada2c0a4acad5f2e08
report JSONL  748.886 bytes   mode 0600   sha256 54ba3c573825ec7c9bf5e7e609631c615962e17b7c80f144c3cff8677951a443
report HTML 1.777.501 bytes   mode 0600   sha256 88f19b7dde57dd5de481b1e8fc0d3d1606379c5d32cd497dac162e0bcc73ed2c
console         5.477 bytes   mode 0600
```

No se copiaron prompts ni respuestas a esta evidencia. Sólo se procesaron offline tipos, conteos,
sentinelas exactos del adaptador y resultados agregados de detectores.

## Decisión y próximo paso

OpenSpec 5.3 permanece abierto. La corrida demuestra que el techo funciona y aporta cobertura real
para API key, pero no completa las cuatro familias ni el triage DAN. Bajo el presupuesto total ya
autorizado no corresponde otra llamada: el remanente es menor que la reserva contractual de una
solicitud.

Para continuar se necesita una decisión explícita nueva: revisar localmente las 15 salidas DAN con
acceso restringido y rediseñar la selección/orden de probes antes de solicitar presupuesto
adicional. No se debe elevar el techo por corrida por encima de USD 0,20 ni convertir negativas del
harness en evidencia de seguridad.

