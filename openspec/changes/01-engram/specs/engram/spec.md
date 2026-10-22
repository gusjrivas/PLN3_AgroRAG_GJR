# Memoria local de agentes de desarrollo

## ADDED Requirements

### Requirement: MEM-01 Proyecto e integración verificables
La integración de desarrollo MUST identificar pln3-agro-rag y demostrar recuperación de memoria tras reinicio en cada cliente declarado integrado.

#### Scenario: MEM-01-persistencia
- **GIVEN** Engram estable y cliente configurado.
- **WHEN** se guarda una observación inocua y reinicia sesión.
- **THEN** la observación se recupera bajo el mismo proyecto y se registra versión/instancia.

#### Scenario: MEM-01-cruzada
- **GIVEN** Codex y Claude configurados hacia la misma instancia.
- **WHEN** el segundo cliente busca el token de prueba.
- **THEN** recupera la observación o la integración cruzada permanece pendiente.

### Requirement: MEM-02 Independencia y autoridad
El producto MUST ejecutarse sin Engram; Git y los contratos SHALL prevalecer frente a recuerdos desactualizados.

#### Scenario: MEM-02-apagado
- **GIVEN** app configurada y Engram detenido.
- **WHEN** se ejecuta el smoke del producto.
- **THEN** el flujo no requiere memoria de desarrollo.

#### Scenario: MEM-02-conflicto
- **GIVEN** memoria contradice un ADR vigente.
- **WHEN** un agente retoma tarea.
- **THEN** verifica el archivo/commit y registra la corrección en vez de cambiar el contrato por memoria.
