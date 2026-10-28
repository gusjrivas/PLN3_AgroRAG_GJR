# API y colaboración de dos agentes

## ADDED Requirements

### Requirement: API-01 Contrato de consulta
La API MUST validar QueryRequest y devolver QueryResponse o ErrorResponse según docs/contracts.md, sin mezclar fallos operativos con estados de negocio.

#### Scenario: API-01-valida
- **GIVEN** request autenticado válido y providers fake.
- **WHEN** se consulta.
- **THEN** se obtiene 200 con request_id, versión y estado coherente.

#### Scenario: API-01-invalida
- **GIVEN** texto vacío, excesivo o unidad faltante.
- **WHEN** se consulta.
- **THEN** se devuelve 422 antes de ejecutar modelos.

### Requirement: AGT-01 Investigación y verificación dinámicas
El investigador y verificador MUST intercambiar resultados estructurados y permitir una ronda de corrección basada en evidencias.

#### Scenario: AGT-01-revision
- **GIVEN** borrador con claim no respaldado y evidencia adicional disponible.
- **WHEN** el verificador solicita revisión.
- **THEN** el investigador busca/corrige y el verificador revisa nuevamente dentro del límite.

#### Scenario: AGT-01-limite
- **GIVEN** segunda revisión todavía insuficiente.
- **WHEN** el flujo decide.
- **THEN** termina en abstención o aclaración; no se abre tercera pasada.

### Requirement: AGT-02 Citas y abstención
Una respuesta answered MUST respaldar cada claim con evidence_ids válidos; falta de datos SHALL producir aclaración y falta de soporte SHALL producir abstención.

#### Scenario: AGT-02-citas
- **GIVEN** draft con IDs reales.
- **WHEN** se valida salida.
- **THEN** citas se resuelven en catálogo de la versión y se entregan pasajes originales.

#### Scenario: AGT-02-faltantes
- **GIVEN** pregunta sobre cuánto regar sólo con porcentaje de humedad.
- **WHEN** se analiza sin datos suficientes.
- **THEN** solicita información pertinente y no inventa litros.

#### Scenario: AGT-02-inventada
- **GIVEN** LLM devuelve evidence_id inexistente.
- **WHEN** se verifica.
- **THEN** se rechaza la cita y no se presenta el draft como verificado.

#### Scenario: AGT-02-contexto-situacional
- **GIVEN** una recomendación situacional sobre cambiar riego, frecuencia o humedad actual sin
  etapa y condiciones del suelo.
- **WHEN** se analiza la consulta.
- **THEN** se solicita contexto pertinente antes de llamar a los agentes y no se asume una
  situación agronómica.

#### Scenario: AGT-02-fuera-de-corpus
- **GIVEN** una consulta sobre herbicidas, costos o precios futuros fuera del alcance documental.
- **WHEN** se analiza la consulta.
- **THEN** se devuelve evidencia insuficiente sin convertir la ausencia de corpus en una pregunta
  aclaratoria ni llamar a los agentes.

### Requirement: AGT-03 Presupuesto y errores
La orquestación MUST respetar límites globales de llamadas, búsquedas, tokens y deadline, incluidos reintentos.

#### Scenario: AGT-03-agotado
- **GIVEN** proveedor lento o repetición de herramientas.
- **WHEN** se consume presupuesto.
- **THEN** se corta en el límite con motivo trazable y error operacional cuando corresponda.

#### Scenario: AGT-03-schema
- **GIVEN** proveedor devuelve JSON inválido.
- **WHEN** se procesa salida.
- **THEN** se aplica como máximo reparación permitida dentro de presupuesto o 502, sin filtrar stacktrace.

### Requirement: AGT-04 Selección explícita de proveedor
El backend MUST seleccionar OpenAI u Ollama por configuración completa, mantener el mismo contrato
estructurado y no degradar silenciosamente entre proveedores.

#### Scenario: AGT-04-openai
- **GIVEN** proveedor OpenAI, key y modelo configurados.
- **WHEN** investigador o verificador genera una salida.
- **THEN** usa Responses API con JSON Schema estricto, `store=false` y métricas de tokens.

#### Scenario: AGT-04-incompleto
- **GIVEN** proveedor seleccionado sin key o modelo.
- **WHEN** se construye el backend.
- **THEN** generación queda no disponible y no usa Ollama como fallback.
