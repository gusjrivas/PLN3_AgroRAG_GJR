# Pruebas de aceptación: 03-retrieval

Estado: escenarios ejecutables implementados con TDD; adaptadores y corrida real `dev` documentados.
BM25 continúa como default y `test` permanece cerrado por decisión metodológica.

| Escenario | Test previsto | Nivel / evidencia |
|---|---|---|
| RET-01-ranking | `test_ret_01_ranking` | pytest por contrato; log RED/GREEN/REFACTOR |
| RET-01-fallo-vector | `test_ret_01_fallo_vector` | pytest por contrato; log RED/GREEN/REFACTOR |
| RET-02-e5 | `test_ret_02_e5` | pytest por contrato; log RED/GREEN/REFACTOR |
| RET-02-incompatible | `test_ret_02_incompatible` | pytest por contrato; log RED/GREEN/REFACTOR |
| RET-03-diversidad | `test_ret_03_diversidad` | pytest por contrato; log RED/GREEN/REFACTOR |
| RET-03-presupuesto | `test_ret_03_presupuesto` | pytest por contrato; log RED/GREEN/REFACTOR |
