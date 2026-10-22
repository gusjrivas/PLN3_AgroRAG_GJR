# Pruebas de aceptación: 06-evaluation-delivery

Estado: pendientes. Cada caso ejecutable se desarrolla con TDD. Las verificaciones de instalación/publicación manual se documentan con evidencia operacional.

| Escenario | Test previsto | Nivel / evidencia |
|---|---|---|
| EVA-01-split | `test_eva_01_split` | pytest por contrato; log RED/GREEN/REFACTOR |
| EVA-01-sin-soporte | `test_eva_01_sin_soporte` | pytest por contrato; log RED/GREEN/REFACTOR |
| EVA-02-comparacion | `test_eva_02_comparacion` | pytest por contrato; log RED/GREEN/REFACTOR |
| EVA-02-negativo | `test_eva_02_negativo` | pytest por contrato; log RED/GREEN/REFACTOR |
| DEL-01-reproduccion | `test_del_01_reproduccion` | Reproducción limpia y revisión PDF/demo; TDD para automatizaciones |
| DEL-01-informe | `test_del_01_informe` | Reproducción limpia y revisión PDF/demo; TDD para automatizaciones |
