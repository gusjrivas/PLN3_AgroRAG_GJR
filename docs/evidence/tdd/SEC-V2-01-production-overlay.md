# Evidencia TDD: overlay productivo y gateway

Fecha: 29/10/2026. Responsable y revisión: misma sesión coordinadora; revisión humana pendiente en
MR #30. Rama: `feat/v2-container-foundation`. Propiedad: overlay productivo, gateway Caddy,
Dockerfile, contratos, runbook, plan y esta evidencia.

Commit de implementación: `61ffbe9` (`feat: harden production compose gateway`).

## RED

Se añadieron dos escenarios al contrato Compose: imágenes inmutables/gateway único y
secretos/privilegios mínimos.

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .tmp/pytest-prod-v2-red tests/architecture/test_compose_contract.py -k production
```

Resultado: exit 1, `2 failed`: `compose.production.yaml` no existía.

## GREEN

El overlay exige imágenes API/UI/gateway por digest y elimina builds del contrato base; sólo dev
los agrega. API recibe reader+OpenAI, UI sólo reader y gateway sólo auth. Los contenidos se montan
como secrets y no aparecen en `docker compose config`. API/UI no publican puertos. Todos usan
filesystem read-only, tmpfs, capabilities eliminadas, no-new-privileges y límites; gateway recupera
únicamente `NET_BIND_SERVICE`.

El gateway es un target no root (UID 10002) basado actualmente en Caddy 2.11.7 fijado al digest
`sha256:eb4d35b7452d1ab6171fbdbe8d9275b2301dad6dad92115d91e19fb9b24d510f`. Incluye configuración
versionada para TLS automático, basic auth importado desde secret, headers, reverse proxy a UI,
health y logs JSON.

Durante CI-V2-01 el scan detectó deuda corregible en la base anterior. La actualización a 2.11.7
y `apk upgrade --no-cache` eliminó los hallazgos Alpine CRITICAL/HIGH. Los HIGH del binario Caddy
quedan controlados por excepciones explícitas, cortas y bloqueantes al vencer; ver CI-V2-01.

Resultado contractual: exit 0, `2 passed` para producción; suite dirigida completa de contenedores,
Compose y healthcheck: `12 passed`.

## Ensayo de gateway

- `docker build --target gateway -t agrorag-gateway:v2-test .`: exit 0.
- `caddy validate` dentro de la imagen con auth bcrypt sintética montada read-only: exit 0,
  `Valid configuration`.
- `id -u` dentro de la imagen: `10002`.
- El archivo temporal de auth sintética se eliminó después del ensayo.

No se solicitó certificado ni se desplegó contra un dominio real: dominio/DNS, registry e IdP son
decisiones externas todavía abiertas. Esta evidencia valida el artefacto y el contrato, no declara
staging o producción ejecutados.

Referencias de implementación: imagen oficial Caddy y documentación oficial de reverse proxy;
Compose secrets se montan por servicio en `/run/secrets` según Docker Docs.
