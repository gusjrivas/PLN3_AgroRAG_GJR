# Evidencia TDD RET - tres FAIL respondibles del benchmark

Fecha: 2026-10-28. Responsable y revisor: misma sesión; no hubo revisor independiente disponible.
Rama: `fix/benchmark-status-gate`.
Commit de implementación: `0ae744e`.

## Diagnóstico observable

- `dev-r-005`: el pasaje INTA con la recomendación del 70 % quedó en posición 5.
- `test-r-006`: el pasaje FAO con más de 90 % de ET quedó en posición 7.
- `dev-r-011`: el pasaje FAO inglés sobre pérdida de agua por estomas no ingresó al ranking de la
  consulta española.

El runtime BM25 seleccionaba cuatro fragmentos y no recibía el máximo configurado por bootstrap.
La diferencia de idioma tampoco tenía normalización lexical común.

## RED

```text
.venv\Scripts\python.exe -m pytest tests/unit/test_retrieval.py tests/unit/test_retrieval_runtime.py -q
exit code: 1
3 failed, 10 passed
```

## GREEN

```text
.venv\Scripts\python.exe -m pytest tests/unit/test_retrieval.py tests/unit/test_retrieval_runtime.py -q
exit code: 0
13 passed
```

La normalización versiona equivalencias agronómicas español/inglés sin red ni modelos. El runtime
BM25 aplica `retrieval_source_cap` y `retrieval_max_items`; el nuevo default es seis. Sobre el
catálogo real, el pasaje de estomas subió a posición 2 y el pasaje de ET a posición 1; la
recomendación del 70 % subió de posición 5 a posición 1 tras normalizar
`recomendación/ideal` y `humedad/retención`.

Los tres casos respondibles pasaron una corrida Playwright dirigida. En regresiones completas,
dos permanecieron estables y el caso del 70 % varió una vez antes de la mejora lexical final; luego
volvió a pasar dirigido. La variación general del proveedor se documenta por separado y no se
atribuye a retrieval.

## REFACTOR y controles

La suite compartida de cierre quedó en `210 passed, 2 deselected`; Ruff, Ruff format, mypy y los
dos contratos de importación finalizaron con código 0. `git diff --check` no informó errores. La
revisión fue realizada por la misma sesión; no hubo revisor independiente disponible.
