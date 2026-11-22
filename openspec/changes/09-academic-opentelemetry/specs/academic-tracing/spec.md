## ADDED Requirements

### Requirement: Trazas locales de consulta

La API MUST habilitar trazas de consola sólo por configuración explícita y usar un
proveedor por ciclo de vida. Los spans MUST usar nombres fijos, con sólo el estado HTTP
numérico en el span raíz y un recurso con nombre de servicio fijo.

#### Scenario: Consulta con trazas habilitadas

- **WHEN** una consulta ejecuta recuperación y ambos agentes.
- **THEN** los tres spans son hijos del span HTTP de esa consulta y el proveedor se cierra al terminar la aplicación.

#### Scenario: Consulta rechazada o fallida

- **WHEN** la API rechaza una consulta o falla una etapa.
- **THEN** el span HTTP registra el estado devuelto y se exporta sin entrada, salida, headers, query string ni datos de excepción.

#### Scenario: Demo deshabilitada

- **WHEN** la API inicia con la configuración predeterminada.
- **THEN** funciona sin el SDK opcional y sin exportar spans.

#### Scenario: Configuración incompatible

- **WHEN** se habilitan las trazas y falta el SDK opcional o `OTEL_SDK_DISABLED=true`.
- **THEN** la API MUST informar el conflicto en el arranque.
