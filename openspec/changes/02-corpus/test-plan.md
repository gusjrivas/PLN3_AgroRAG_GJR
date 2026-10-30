# Pruebas de aceptación: 02-corpus

Estado: COR-01, COR-02 y la parte local de COR-03 implementadas con TDD. La activación atómica con
índice remoto permanece abierta y se documenta como límite operacional.

| Escenario | Test previsto | Nivel / evidencia |
|---|---|---|
| COR-01-valido | `test_cor_01_valido` | pytest por contrato; log RED/GREEN/REFACTOR |
| COR-01-invalido | `test_cor_01_invalido` | pytest por contrato; log RED/GREEN/REFACTOR |
| COR-02-tabla | `test_cor_02_tabla` | pytest por contrato; log RED/GREEN/REFACTOR |
| COR-02-ambigua | `test_cor_02_ambigua` | pytest por contrato; log RED/GREEN/REFACTOR |
| COR-03-repeticion | `test_cor_03_repeticion` | pytest por contrato; log RED/GREEN/REFACTOR |
| COR-03-cambio | `test_cor_03_cambio` | pytest por contrato; log RED/GREEN/REFACTOR |
