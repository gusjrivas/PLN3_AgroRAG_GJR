# Evidencia TDD: runner y gate Garak offline

Fecha: 30/10/2026. Responsable y revisión técnica: misma sesión coordinadora. MR #30 integrado por
`gusjrivas` sin una review formal registrada en GitHub. Rama de implementación:
`feat/v2-container-foundation`. Propiedad: `Dockerfile.garak`, perfil security, adaptador/gate,
configuración, gateway, pruebas, runbook y esta evidencia.

Commit de implementación: `42d6817` (`feat: add isolated garak release gate`).

## RED

Se escribieron primero los contratos de adaptador, política y arquitectura. Pytest detuvo la
colección con dos `ModuleNotFoundError` para `scripts.garak_adapter` y
`scripts.check_garak_policy`; el runner, perfil, config y Dockerfile tampoco existían. Este RED
demostró que no había forma reproducible de evaluar `/v1/query` ni sanitizar un JSONL.

## GREEN

- Adaptador loopback al gateway HTTPS, dos secretos por archivo, request `/v1/query` y errores sin
  cuerpo, prompt ni credenciales.
- Garak 0.17.0, seed 1729, una generación, cap 32 y probes exactos de injection, jailbreak, Base64 y
  credenciales aparentes.
- Gate agregado por probe/detector: HIGH no triagado bloquea; confirmado exige excepción completa y
  vigente; regresión y detector ausente bloquean. El resumen nunca copia attempts/prompts/outputs.
- Perfil one-shot no-root UID 10003, sin puertos/capabilities, filesystem read-only y sin secretos de
  proveedor. Los crudos están ignorados por Git y se ajustan a modo `0600`.
- Gateway Caddy mantiene Basic auth global y enruta `/v1/*` a API; UI continúa como fallback.

Resultados: tests focalizados `10 passed`; suite offline completa `260 passed, 3 deselected`; Ruff,
format, mypy (38 archivos), dos contratos de importación, OpenSpec y `git diff --check`, exit 0; Compose
security `config --quiet`, exit 0; Caddy 2.11.7 `Valid configuration`. La imagen construyó en 397 s,
reportó Garak `v0.17.0`, usuario `10003:10003`, entrypoint separado y tamaño 3.292.465.354 bytes.

El primer scan Trivy 0.76.1 fue otro RED útil: 7 CRITICAL y 34 HIGH, sin secretos. Los CRITICAL
eran paquetes corregibles de la base Debian fijada; no se exceptuaron. Se cambió al mismo digest
Python ya aprobado por API/UI, se aplicó `apt-get upgrade` y se fijó `filelock` corregido. El conteo
final posterior a la reconstrucción fue 0 CRITICAL, 1 HIGH y 0 secretos. El HIGH restante,
CVE-2026-104851 en `fsspec`, requiere abrir un Kerchunk/reference no confiable; esa API no se usa
en los probes seleccionados ni acepta input del target. `datasets 3.6` bloquea la versión corregida.
Se aceptó temporalmente sólo para `garak-runner`, con owner/tracking/riesgo y vencimiento 15/11/2026
en un archivo separado de las excepciones del producto. Fuente primaria:
https://github.com/fsspec/filesystem_spec/security/advisories/GHSA-27vj-qcqg-25rc.
La política ejecutable devolvió `approved` con ese único HIGH aceptado y ningún bloqueo.

## Límites honestos

No se ejecutó un scan real: faltan staging autorizado, dominio/TLS, credenciales de ensayo y
presupuesto/proveedor. `baseline.json` declara `pending-first-authorized-scan`; triage y excepciones
están vacíos. El peso de la distribución oficial (197 paquetes y dependencias PyTorch/CUDA) exige
cache/publicación separada. Garak es un detector heurístico, no una certificación de seguridad.

Dos resoluciones consecutivas mostraron drift en dependencias transitivas. Se congeló el inventario
aprobado en `infra/garak/requirements.lock` (197 paquetes exactos) y el build ahora verifica
`garak==0.17.0`. Como ese lock incluye wheels CUDA, el runner falla cerrado fuera de `linux/amd64`;
una imagen ARM64 requiere su propio lock, build y scan.

## Publicación inmutable post-merge

Se ejecutó manualmente `garak-runner-supply-chain` con reconocimiento explícito del build grande
sobre el commit integrado `5a11a29a8e0e8b3ce4c1dce9e5ecf7a221d24af6`. El
[run 41062609444](https://github.com/gusjrivas/PLN3_AgroRAG_GJR/actions/runs/41062609444)
terminó `success`: build único, Garak 0.17.0, UID 10003, label OCI, SBOM, Trivy, política, upload de
evidencia, login, publicación y manifiesto aprobaron.

El artefacto `garak-runner-manifest-5a11a29a8e0e8b3ce4c1dce9e5ecf7a221d24af6` declaró:

```text
ghcr.io/gusjrivas/pln3_agrorag_gjr/garak-runner@sha256:9a56fcacf404a0668496747820c9529bfb1de880853fe9de2123ff1ea4270e61
```

`docker buildx imagetools inspect` resolvió esa referencia desde esta máquina, devolvió exit 0 y
confirmó el digest exacto. Esto completa la publicación del runner, no el primer scan autorizado:
el baseline, triage y dictamen siguen pendientes de staging real.
