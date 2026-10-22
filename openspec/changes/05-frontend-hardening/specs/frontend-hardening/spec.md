# Interfaz Python, seguridad y optimización

## ADDED Requirements

### Requirement: UI-01 Experiencia de consulta y fuentes
La UI Streamlit MUST consumir sólo HTTP y mostrar estados de negocio, errores y evidencia de forma accesible.

#### Scenario: UI-01-respuesta
- **GIVEN** API devuelve respuesta con citas.
- **WHEN** usuario consulta.
- **THEN** ve texto, limitaciones y fuentes expandibles con página/edición.

#### Scenario: UI-01-aclaracion
- **GIVEN** API solicita contexto.
- **WHEN** usuario completa lo faltante.
- **THEN** se preserva consulta original y se envía contexto explícito.

#### Scenario: UI-01-error
- **GIVEN** API devuelve 503.
- **WHEN** se renderiza pantalla.
- **THEN** se muestra indisponibilidad y no se interpreta como ausencia de evidencia agronómica.

### Requirement: UI-02 Estado aislado y sin duplicación
La UI MUST aislar sesiones y ejecutar una llamada por envío, sin repetir inferencia en reruns.

#### Scenario: UI-02-rerun
- **GIVEN** respuesta existente.
- **WHEN** usuario expande una cita.
- **THEN** no se dispara una segunda consulta ni consumo adicional.

#### Scenario: UI-02-sesiones
- **GIVEN** dos sesiones con contexto distinto.
- **WHEN** ambas consultan.
- **THEN** no comparten borradores ni datos de contexto.

### Requirement: SEC-01 Acceso y entradas no confiables
El producto MUST aplicar controles de acceso, herramientas permitidas y validación de evidencia sin ejecutar instrucciones del corpus.

#### Scenario: SEC-01-sin-clave
- **GIVEN** request sin reader válido.
- **WHEN** se consulta endpoint protegido.
- **THEN** devuelve 401 sin llamar modelos.

#### Scenario: SEC-01-injection
- **GIVEN** pasaje ordena revelar secreto o ejecutar shell.
- **WHEN** se recupera.
- **THEN** la salida y herramientas no exponen secreto ni ejecutan acciones no permitidas.

#### Scenario: SEC-01-traversal
- **GIVEN** evidence_id con traversal.
- **WHEN** se consulta evidencia.
- **THEN** se rechaza sin acceder al filesystem arbitrario.

### Requirement: OPS-01 Caché y trazas
Retrieval MUST cachear con identidad de corpus/modelo/config y registrar tiempos, uso y decisiones sin secretos.

#### Scenario: OPS-01-hit
- **GIVEN** misma consulta/filtros/versión.
- **WHEN** se repite retrieval.
- **THEN** cache hit evita nueva búsqueda vectorial y registra ahorro real.

#### Scenario: OPS-01-invalidate
- **GIVEN** cambia corpus o filtros.
- **WHEN** se repite consulta.
- **THEN** hay miss; no se devuelve evidencia obsoleta.

#### Scenario: OPS-01-redaccion
- **GIVEN** error con clave centinela.
- **WHEN** se loguea y responde.
- **THEN** la clave no aparece en logs ni respuesta.
