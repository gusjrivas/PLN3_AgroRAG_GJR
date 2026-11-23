## 1. API y telemetría

- [x] 1.1 OPS-OBS-01. Coordinador, `feat/observability-grafana`, base `d0111a3`. Propiedad: aplicación, bootstrap, infraestructura, dependencias y pruebas de contrato. [Evidencia TDD](../../../docs/evidence/tdd/OPS-OBS-01.md).

## 2. Docker y Grafana

- [x] 2.1 OPS-OBS-02. Subagente Docker/Grafana, `feat/observability-grafana-docker`, base `d0111a3`. Propiedad: Dockerfile, overlay y provisioning. Configuración y recepción de señales verificadas en el ensayo aislado. [Evidencia TDD](../../../docs/evidence/tdd/OPS-OBS-02.md) y [ensayo](../../../docs/evidence/tdd/OPS-OBS-03.md).

## 3. Integración y cierre técnico

- [ ] 3.1 OPS-OBS-03. Coordinador, `feat/observability-grafana`. Propiedad: pruebas integradas, runbook y evidencia. Flujo Streamlit, métricas y recuperación del Collector verificados en Docker aislado. Quedan pendientes Compose con navegador, commit y CI antes de integrar a main. [Evidencia](../../../docs/evidence/tdd/OPS-OBS-03.md).
