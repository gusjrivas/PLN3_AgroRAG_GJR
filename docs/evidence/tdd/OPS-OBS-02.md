# OPS-OBS-02. Docker y Grafana local

Implementación delegada en `feat/observability-grafana-docker`, sobre `d0111a3`.
Propiedad de la tarea: Dockerfile, overlay, provisioning y prueba de arquitectura de Compose.

## RED

```powershell
python -m pytest -q tests/architecture/test_compose_contract.py -k observability_overlay
```

Exit 1. Compose no encontró `compose.observability.yaml`. La prueba comprueba el target
opcional de API, el endpoint OTLP interno, el puerto loopback de Grafana y el vínculo entre el
tablero y su proveedor.

## GREEN y regresión

```powershell
python -m pytest -q tests/architecture/test_compose_contract.py tests/architecture/test_container_image_contract.py
python -m pytest -q tests/architecture
ruff check tests/architecture/test_compose_contract.py
ruff format --check tests/architecture/test_compose_contract.py
git diff --check
```

Exit 0 en todos los comandos, 14 pruebas dirigidas y 32 de arquitectura. El target
`api-observability` instala el extra `tracing` con el lockfile. El overlay monta el tablero y el
proveedor de Grafana en modo lectura. El tablero agrupa solicitudes por estado HTTP, resultados de
auditoría y lookups de caché. Calcula el p95 sobre el histograma de duración y consulta las trazas
de `POST /v1/query` en Tempo.

Se verificó el índice multiarch de [Grafana LGTM 0.41.1](https://hub.docker.com/layers/grafana/otel-lgtm/0.41.1/images/sha256-93846d819bb09134ea4160addd08a6d081bdfc5379e80dae081b675257cee568).
La [configuración de Prometheus de LGTM](https://github.com/grafana/docker-otel-lgtm/blob/v0.41.1/docker/prometheus.yaml)
promueve `service.name`. La [traducción de OTLP de Prometheus](https://github.com/prometheus/prometheus/blob/v3.16.0/config/config.go#L259-L265)
usa guiones bajos y sufijos por defecto.

## Ensayo en ejecución

El intento de crear un contenedor dedicado terminó con exit 1 por acceso denegado al pipe
`docker_engine`. En el worktree delegado, el índice Git también quedó fuera de los permisos de
escritura. El coordinador integra el diff y verifica la recepción de señales en el stack.
