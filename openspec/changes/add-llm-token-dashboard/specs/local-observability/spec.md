## ADDED Requirements

### Requirement: Consumo de tokens de los agentes

La API con OTLP MUST contar los tokens de entrada y salida de cada llamada con uso válido. Las etiquetas serán rol, dirección y procedencia del conteo. La instrumentación MUST exportar sólo cantidades y valores de un conjunto cerrado.

#### Scenario: Respuesta con conteo informado o estimado

- **WHEN** el proveedor devuelve un conteo válido para investigador o verificador.
- **THEN** Prometheus recibe ambos valores con las etiquetas del rol y su procedencia.

#### Scenario: Llamada sin información de uso

- **WHEN** una llamada falla sin devolver cantidades válidas.
- **THEN** la llamada no suma tokens y se conservan los conteos válidos recibidos antes del fallo.

### Requirement: Costo estimado en Grafana

El tablero MUST calcular en USD el costo acumulado desde el arranque de la API multiplicando cada dirección por la tarifa correspondiente. Ambas tarifas serán configurables en USD por millón de tokens.

#### Scenario: Estimación con tarifas configuradas

- **WHEN** el operador carga tarifas válidas para el modelo utilizado por la API.
- **THEN** Grafana presenta el costo estimado de entrada, salida y total.

#### Scenario: Tarifas sin configurar

- **WHEN** falta alguna tarifa.
- **THEN** el tablero omite la estimación de costo y sigue mostrando los tokens.
