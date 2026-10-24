# Evidencia TDD: proveedor OpenAI configurable

Fecha: 24/10/2026. Responsable y revisor disponible: misma sesión Codex; revisión humana
pendiente. Rama: `feat/openai-provider`. Base: commit `a678109` del PR #15. Propiedad:
configuración/bootstrap, contrato compartido, adaptador OpenAI, pruebas, ADR-014 y documentación.

## Contrato

`AGRO_MODEL_PROVIDER=openai` exige `OPENAI_API_KEY` y `AGRO_OPENAI_MODEL`. La configuración
incompleta queda not ready y no activa Ollama como fallback. La key es `SecretStr`, permanece en el
backend y no se registra ni incorpora al prompt. La request usa Responses API, Structured Outputs
estricto, `store=false`, timeout y presupuesto existentes.

La selección de Responses API y `text.format` sigue la documentación oficial de Structured
Outputs: https://developers.openai.com/api/docs/guides/structured-outputs

## RED

Comando focalizado sobre el adaptador y bootstrap:

```text
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --tb=short --basetemp=.tmp\openai-red tests/integration/test_openai_model.py tests/unit/test_model_provider.py
```

Resultado: exit code 1, `7 failed`; no existían `OpenAIModel` ni selección de proveedor.

El cambio posterior del mensaje UI a proveedor neutral tuvo RED independiente: exit code 1,
`1 failed, 2 passed`.

## GREEN

El adaptador usa únicamente `httpx`, separa instrucciones de input no confiable, extrae salida
estructurada y uso, trata refusals/incomplete/HTTP inválido como error operativo redactado y
comprueba readiness mediante metadata del modelo sin generar texto. Ollama comparte exactamente
los mismos prompts y esquemas.

Resultados:

- Suite afectada: exit code 0, `25 passed in 12.50s`.
- Suite completa final: exit code 0, `161 passed, 2 deselected in 10.04s`.
- Ruff check/formato: exit code 0, 149 archivos formateados.
- mypy: exit code 0, 34 archivos sin errores.
- import-linter: exit code 0, 2 contratos mantenidos.
- OpenSpec `04-agents-backend` estricto: válido.

Una corrida intermedia sin elevación terminó `11 failed, 150 passed`: Windows negó lectura a
`data/processed/catalogue/active.json` mientras el backend local estaba activo. La repetición con
acceso al mismo catálogo aprobó completa; no se modificó el dato ni se atribuyó el fallo al código.

## Límite de integración

Durante la implementación inicial `OPENAI_API_KEY` no estaba configurada. Los tests interceptan
HTTP y comprueban destino, autorización, payload, schema, respuesta, uso y redacción; ese GREEN
offline no se presenta como validación real del proveedor.

La activación posterior confirmó autenticación y acceso a metadata de `gpt-4o`, pero la generación
respondió `429` con código redactado `credit_balance_exhausted`. No hubo respuesta de negocio ni
consumo acreditado. El RED focalizado del error tipado falló al importar `ProviderUnavailable`; el
GREEN terminó `9 passed`. Se añadió esa excepción y el error público `MODEL_UNAVAILABLE` para
distinguir cuota/acceso de JSON inválido. Suite final: `164 passed, 2 deselected in 7.11s`. El smoke
real completo continúa pendiente de saldo API.

Commit funcional: `1f2d1d4`. PR apilado sobre #15:
[#16](https://github.com/gusjrivas/PLN3_AgroRAG_GJR/pull/16). CI del commit funcional:
`specs`, `offline` y `browser` aprobados.
