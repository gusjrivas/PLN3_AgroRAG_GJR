# Evidencia TDD: CI-V2-03 remediación de imágenes

Fecha: 2026-11-07/08 (America/Buenos_Aires). Rama: `fix/ci-v2-03-image-cves`.
Base: `eb9122dc2c61fe0035bf09659662ca4fd6d2cc8c`. Issue: #42. PR draft: #43.
Responsable de implementación: agente de supply chain; revisión independiente pendiente.

## Incidente y caracterización

El artefacto real `supply-chain-5724515a3fd7d989eacc6e3a5794621a44c2ed79`
(run `42423957412`, artifact `13594447007`) confirmó:

- API/UI: `CVE-2026-109518` en `apt` y `libapt-pkg6.0`, instalados `2.6.1`,
  corregidos en `2.6.2`;
- gateway: `CVE-2026-78661` en `golang.org/x/net`, instalado `v0.59.0`,
  corregido en `0.62.0`.

Los manifests oficiales se resolvieron sin inventar digests:

- `python:3.12.16-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df`;
- `caddy:2.11.9-alpine@sha256:0bbb055bda6793c999bde78b1b5ce3e89f829fb031af2cf50056ea1246559fee`.

## RED

Se agregó primero
`test_ci_v2_03_pins_refreshed_official_base_images`, que exige el Python corregido y el último
Caddy oficial disponible, y prohíbe volver a los dos digests anteriores.

```text
python -m pytest tests/architecture/test_container_image_contract.py -q
# exit 1: 1 failed, 4 passed
# fallo esperado: Dockerfile todavía fijaba Python/Caddy anteriores.
```

## GREEN

Se cambiaron únicamente los dos argumentos de imagen base en `Dockerfile`.

```text
python -m pytest tests/architecture/test_container_image_contract.py -q
# exit 0: 5 passed
```

Los tres targets construyeron localmente con los nuevos manifests:

- API: imagen local `agrorag-api:ci-v2-03`, ID `0bff9c5fd3dd`;
- UI: build exit 0, manifest list local `9e90bd812d48`;
- gateway: build exit 0, manifest list local `ade7c6ea572e`.

El build de gateway actualizó además Alpine `zlib 1.3.2-r1 -> 1.4-r0` mediante el
`apk upgrade --no-cache` ya existente.

## Scans reales y excepción temporal autorizada

Trivy oficial `0.76.1`, con la misma configuración de CI, produjo
`api-remediated-trivy.json` y `ui-remediated-trivy.json`: ambos quedaron con
0 HIGH/CRITICAL y sin `CVE-2026-109518`. El reporte actualizado de gateway redujo
`golang.org/x/net` de `v0.59.0` a `v0.60.0`, pero Trivy todavía exige `0.62.0` y conservó
un único HIGH: `CVE-2026-78661`.

RED real del gate, antes de tocar excepciones:

```text
python scripts/check_vulnerability_policy.py \
  --report api=%TEMP%\agrorag-ci-v2-03-run40\api-remediated-trivy.json \
  --report ui=%TEMP%\agrorag-ci-v2-03-run40\ui-remediated-trivy.json \
  --report gateway=%TEMP%\agrorag-ci-v2-03-run40\gateway-remediated-trivy.json \
  --exceptions configs/security/vulnerability-exceptions.json --today 2026-11-08
# exit 1
# {"accepted_high": [], "blocked": ["gateway:CVE-2026-78661:HIGH"], "status": "blocked"}
```

El usuario autorizó explícitamente una excepción temporal hasta 2026-11-15. Se registró sólo ese
hallazgo, con riesgo preciso: DoS en `x/net/html`; el Caddyfile desplegado sólo usa `reverse_proxy`
y no habilita `templates` ni `file_server`. El owner es Gustavo Julián Rivas y el tracking es issue
#42, con obligación de actualizar al primer Caddy oficial que incluya `x/net >=0.62.0`.

GREEN del mismo gate:

```text
# mismo comando y reportes
# exit 0
# {"accepted_high": ["gateway:CVE-2026-78661"], "blocked": [], "status": "approved"}
```

No se relajaron severidades, Trivy ni la regla que impide exceptuar CRITICAL/secretos.
Una ejecución de control con `--today 2026-11-16` terminó con exit code `1` y volvió a bloquear
`gateway:CVE-2026-78661:HIGH`, demostrando que la aceptación caduca.

## REFACTOR y verificación local

El coordinador repitió la suite focalizada de contratos de imagen, CI y política: exit code `0`,
`12 passed`. Ruff check/format, `git diff --check` y OpenSpec 07 estricto terminaron con exit
code `0`.

La inspección local de los targets confirmó:

- API/UI: usuario `10001:10001`;
- gateway: usuario `10002:10002`;
- los tres targets: label OCI `revision=11abe204c67a1fd335b005b208d09501f5390b21` y
  `version=ci-v2-03`.

La revisión independiente detectó inicialmente que el nombre del test y la evidencia llamaban
"remediado" al pin de Caddy aunque `x/net` continuaba vulnerable. Se corrigió el lenguaje, se
vinculó el riesgo al Caddyfile realmente desplegado y el mismo revisor confirmó que no quedan
bloqueantes.

Quedan pendientes antes del cierre remoto:

- commit/push del coordinador;
- CI remoto `quality` y `container-supply-chain` sobre el commit publicado.

Los reportes reales y el ZIP del artifact permanecen sólo en `%TEMP%`; no se versionan SBOM ni
reportes Trivy completos. Commit y push quedan pendientes del coordinador.
