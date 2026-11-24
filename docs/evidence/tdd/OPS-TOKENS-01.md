# OPS-TOKENS-01. Tokens y costo estimado en Grafana

Rama `feat/grafana-token-usage`, base `06f8f5a`. La sesión de implementación hizo la revisión local y la prueba en Docker.

## RED y GREEN

- `python -m pytest -q tests/contract/test_academic_tracing.py -k otlp_exports`: exit 1 por ausencia de `agro_rag.llm.tokens` en las tres variantes de transporte.
- `python -m pytest -q tests/contract/test_academic_tracing.py tests/architecture --basetemp .tmp/token-qa`: exit 0, 41 pruebas aprobadas. El contrato comprueba la procedencia del conteo por agente y la conservación de los tokens del investigador si falla el verificador.
- Ruff, mypy, los dos contratos de importación y la validación estricta de OpenSpec terminaron en exit 0.

## Docker local

`docker build --target api-observability -t agrorag-api:observability .` y el arranque de
Compose con `--no-build --wait` terminaron en exit 0. La API se recreó y Grafana conservó
su contenedor y los datos. La copia local del tablero tiene UID `agrorag-tokens-demo`.

Una consulta verificada con GPT-4o tardó 3.328 ms según la respuesta de la API y produjo
4.025 tokens de entrada y 107 de salida. Prometheus devolvió cuatro series de conteos reportados:

| Agente | Entrada | Salida |
| --- | ---: | ---: |
| Investigador | 2.011 | 86 |
| Verificador | 2.014 | 21 |

Con las [tarifas base de GPT-4o](https://developers.openai.com/api/docs/models/gpt-4o)
de USD 2,50 y USD 10,00 por millón, las expresiones del tablero devolvieron
USD 0,01006250 de entrada, USD 0,00107000 de salida y USD 0,01113250 en total.
También se comprobó que la condición de tarifa sin configurar deja las tres consultas
de costo sin resultados. La estimación aplica la tarifa base a todos los tokens.
