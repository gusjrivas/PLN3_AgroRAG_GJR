# CI-V2-04 · Reconstrucción del gateway con x/net corregido

Base `681bc46`. Rama `fix/gateway-xnet-cve`. Implementación y revisión local por la misma
sesión. Propiedad: `Dockerfile`, contrato de imagen, diseño V2 y esta evidencia.

El control de supply chain del PR #54 detectó CVE-2026-78661 en el gateway existente.
La excepción anterior venció. La [base oficial de Caddy](https://hub.docker.com/_/caddy)
seguía en 2.11.9 y el [aviso de Go](https://pkg.go.dev/vuln/GO-2026-6860) fija el
mínimo corregido en `golang.org/x/net v0.62.0`.

Se construye el comando estándar de Caddy 2.11.9 con esa dependencia, usando un builder oficial
fijado por digest y la verificación de módulos de Go. El build inspecciona la dependencia
en el binario resultante. El runtime conserva usuario, Caddyfile, permisos de puerto e identidad
OCI. La política de vulnerabilidades y sus fechas conservan su vigencia.

- RED. `pytest tests/architecture/test_container_image_contract.py -q` terminó con código 1
  (1 fallo, 5 aprobadas). El Dockerfile todavía carecía del builder con la dependencia corregida.
- GREEN. `pytest tests/architecture/test_container_image_contract.py tests/architecture/test_compose_contract.py -q`
  terminó con código 0 y 13 aprobadas. `git diff --check` pasó.
