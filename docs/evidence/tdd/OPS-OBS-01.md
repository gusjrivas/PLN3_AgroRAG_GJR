# OPS-OBS-01. Exportación OTLP y métricas

Rama `feat/observability-grafana`, base `d0111a3`. Prueba en
`tests/contract/test_academic_tracing.py`. La versión opcional del SDK y el exportador
OTLP/HTTP se fijan en `uv.lock` con uv 0.13.5.

## RED

```powershell
python -m pytest -q tests/contract/test_academic_tracing.py -k origin_rejects
python -m pytest -q tests/contract/test_academic_tracing.py -k otlp_exports
```

Ambos comandos terminaron en exit 1. Los orígenes con credenciales o ruta eran aceptados
porque el ajuste no existía. Las consultas seguían exportando sólo a consola, así que
el transporte OTLP de la prueba no recibió paquetes.

## GREEN y regresión dirigida

```powershell
python -m pytest -q tests/contract/test_academic_tracing.py tests/architecture
ruff check src tests
ruff format --check src tests
mypy
lint-imports --config pyproject.toml --no-cache
npx --yes @fission-ai/openspec@1.14.3 validate add-local-observability --strict
```

Exit 0 en las pruebas dirigidas, 41 aprobadas, y en los controles estáticos y de especificación.
Las pruebas reemplazan el transporte HTTP hacia el Collector y decodifican los protobuf reales.
Comprueban jerarquía de spans, estados HTTP 200/422/502, conteo de caché, resultado de consulta,
exclusión de los valores sentinela y continuidad ante error HTTP y desconexión.
