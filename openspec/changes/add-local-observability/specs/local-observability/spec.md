## ADDED Requirements

### Requirement: Exportación local opcional

La API MUST iniciar un proveedor por ciclo de vida cuando se habilita el trazado. Un origen OTLP configurado explícitamente habilita trazas y métricas por OTLP/HTTP. La configuración previa de consola sigue disponible.

#### Scenario: Consulta en modalidad OTLP

- **WHEN** una consulta ejecuta recuperación y ambos agentes con OTLP habilitado.
- **THEN** el Collector recibe los tres spans de etapa bajo el span HTTP de la consulta y recibe volumen, duración, resultado y estado de caché.

#### Scenario: Consulta rechazada

- **WHEN** HTTP rechaza una consulta antes del servicio.
- **THEN** se registra el estado HTTP y su duración y se omiten las métricas de resultado y caché de esa consulta.

#### Scenario: Collector no disponible

- **WHEN** el Collector está detenido o devuelve errores de transporte.
- **THEN** la API sigue respondiendo con su comportamiento normal y la exportación trabaja con cola y timeout acotados.

### Requirement: Privacidad de la telemetría

La API MUST limitar los spans y métricas a atributos fijos definidos en el diseño. Los datos de entrada, salida, encabezados, query string, excepción y credenciales MUST quedar fuera de la telemetría.

#### Scenario: Consulta con datos sentinela

- **WHEN** el caso usa valores identificables en la pregunta, las cabeceras, el pasaje, la respuesta y la excepción.
- **THEN** los valores no aparecen en los payloads exportados.

### Requirement: Tablero local reproducible

El Compose de demo MUST provisionar un tablero Grafana versionado y exponer su interfaz sólo mediante loopback.

#### Scenario: Arranque del stack de demo

- **WHEN** el operador inicia el overlay y envía una consulta desde Streamlit.
- **THEN** Grafana muestra su traza y métricas sin configurar manualmente el tablero.
