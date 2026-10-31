# Libros de evidencia de pruebas

Esta carpeta conserva los cuatro libros Excel producidos durante las pruebas y revisiones humanas.
Los libros preservan la evidencia registrada; el resumen Garak se actualiza al cerrar nuevas
corridas sanitizadas.

| Archivo | Uso | SHA-256 |
|---|---|---|
| `agro-rag-resultados-playwright-60-casos.xlsx` | Resultados del recorrido Playwright de 60 casos. | `3e056815527871fe5603f7f3c028329ab44227d06577410f97ff0031c44918d4` |
| `agro-rag-revision-manual-60-casos.xlsx` | Revisión manual del benchmark de 60 casos. | `30c279830deaa3d90a264581d99d1e3175c43d7b19b756485205d5299ba96a48` |
| `e2-revision-humana-18-pares.xlsx` | Revisión humana E2 de 18 pares; 12 PASS, 6 FAIL, revisor `Gus Rivas` y fecha 29/10/2026 en las 18 filas. | `cc5df046921b63f945b1d8e636da6672d2ff9e3312df1b4fa6d8e06c9701bd53` |
| `garak-d38814b4-revision-humana-dan.xlsx` | Triage humano DAN completo y resumen de cobertura: Base64 32/32 y prompt injection 32/32 con respuestas reales y 0 detecciones. | `758805618ccd5843fc5a99a3b987d38bf514942370beecb394b98600bac508dc` |

Los archivos `~$*.xlsx`, las inspecciones `.ndjson` y las vistas previas PNG son auxiliares locales y
no forman parte de la evidencia versionada.
