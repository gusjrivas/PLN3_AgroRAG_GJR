# OPS-TRACE-01 · Trazas de la demo académica

Rama `feat/academic-opentelemetry`, base `6bea8f249ae1c04c53761ed785fd776af22d900c`.
La implementación se entrega como diff local por decisión del coordinador.

## RED

- `uv run --no-sync pytest -q tests/contract/test_academic_tracing.py --tb=short`
  (código 1, dos fallos). La configuración no tenía el campo y el inicio de las
  aplicaciones habilitadas creó cero exportadores.
- `python -m pytest -q tests/contract/test_academic_tracing.py -k auto_configuration --tb=short`
  (código 1). FastAPI intentó configurar OTLP a partir del entorno, confirmado también
  por el revisor independiente.
- `python -m pytest -q tests/contract/test_academic_tracing.py -k rejects_disabled_sdk --tb=short`
  (código 1). La API inició con el SDK deshabilitado aunque el perfil pedía trazas.

## GREEN y regresión

- `uv sync --locked --extra tracing` y `uv run --no-sync python -c "import opentelemetry.sdk.trace"`
  (código 0). Lockfile con SDK 1.45.1 y convenciones 0.66b1.
- `python -m pytest -q tests/contract/test_academic_tracing.py --tb=short`
  (código 0, cuatro contratos). Exportador en memoria del SDK, modelos y búsqueda dobles.
  Se verificaron jerarquía y estados 200/422/502/503, ausencia de datos centinela,
  aislamiento de dos aplicaciones, cierre y rechazo de configuración incompatible.
- `uv run --no-sync pytest -q --tb=short` con el extra
  (código 0, 346 aprobados, uno omitido por Windows, tres deseleccionados).
- En un entorno limpio con `uv sync --locked`, sin SDK, `python -m pytest -q --cov --tb=short`
  (código 0, 343 aprobados, cuatro omitidos, tres deseleccionados).
  Cobertura total 87,16 %. `coverage report --include='src/agro_rag/domain/*,src/agro_rag/application/*' --fail-under=90`
  (código 0, 96 % mostrado). Un smoke en ese entorno confirmó el error de arranque al habilitar el perfil sin el extra.
- `ruff check .`, `ruff format --check .`, `mypy`, `lint-imports --no-cache`,
  `git diff --check` (código 0). `npx --yes @fission-ai/openspec@1.14.3 validate --all --strict`
  (código 0, diez elementos).
- El coordinador informó un smoke de consola con los cuatro spans esperados. El revisor independiente confirmó las correcciones y reportó 59 pruebas aprobadas.
  El coordinador reportó 347 aprobadas, dos omitidas y una deseleccionada en su suite
  final con Chromium. CI incorpora un paso específico
  para el extra. La comprobación local no realizó llamadas a proveedores.

El span de recuperación incluye el acceso a caché. Los spans de agentes miden cada
llamada al modelo. La salida síncrona está destinada al volumen de una demo local.
