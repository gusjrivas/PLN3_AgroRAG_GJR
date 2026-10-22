# Pruebas de aceptación: 05-frontend-hardening

Estado: pendientes. Cada caso ejecutable se desarrolla con TDD. Las verificaciones de instalación/publicación manual se documentan con evidencia operacional.

| Escenario | Test previsto | Nivel / evidencia |
|---|---|---|
| UI-01-respuesta | `test_ui_01_respuesta` | AppTest; E2E Python para recorrido completo |
| UI-01-aclaracion | `test_ui_01_aclaracion` | AppTest; E2E Python para recorrido completo |
| UI-01-error | `test_ui_01_error` | AppTest; E2E Python para recorrido completo |
| UI-02-rerun | `test_ui_02_rerun` | AppTest; E2E Python para recorrido completo |
| UI-02-sesiones | `test_ui_02_sesiones` | AppTest; E2E Python para recorrido completo |
| SEC-01-sin-clave | `test_sec_01_sin_clave` | pytest por contrato; log RED/GREEN/REFACTOR |
| SEC-01-injection | `test_sec_01_injection` | pytest por contrato; log RED/GREEN/REFACTOR |
| SEC-01-traversal | `test_sec_01_traversal` | pytest por contrato; log RED/GREEN/REFACTOR |
| OPS-01-hit | `test_ops_01_hit` | pytest por contrato; log RED/GREEN/REFACTOR |
| OPS-01-invalidate | `test_ops_01_invalidate` | pytest por contrato; log RED/GREEN/REFACTOR |
| OPS-01-redaccion | `test_ops_01_redaccion` | pytest por contrato; log RED/GREEN/REFACTOR |
