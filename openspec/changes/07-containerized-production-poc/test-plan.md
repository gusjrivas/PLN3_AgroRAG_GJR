# Test plan: PoC productiva containerizada

## Estrategia

Preservar primero el comportamiento existente con suites de caracterización. Cada capacidad nueva
empieza con un fallo funcional observable. Los tests offline no descargan modelos ni llaman APIs
pagas. Docker/Compose se prueba además de validar sintaxis.

## Escenarios y capas

- CFG-V2: unitarios de settings API/UI, archivos temporales y secretos centinela.
- ARC-V2: import-linter/AST, permisos del catálogo y ausencia de I/O en import.
- IMG-V2: build, inspect, usuario/labels/contenido y smoke de procesos.
- CMP/DAT-V2: config, health, HTTP UI→API, persistencia, read-only e idempotencia.
- SEC/OPS-V2: exposición, secretos, filesystem, logs, recursos, backup y rollback.
- CI/REL-V2: checkout limpio, artefactos por digest, SBOM y promoción sin rebuild.
- GARAK-V2: adaptador/policy con fixtures JSONL; scan real sólo en staging autorizado.

## Regresión

En cada corte ejecutar al menos suite afectada, Ruff, mypy, import-linter y OpenSpec. Antes de la
promoción ejecutar toda la suite offline, AppTest, browser E2E, verificación de entrega y smoke
Compose. Registrar mocks, scans reales, excepciones y ambiente por separado.
