# Base independiente Python y TDD

## ADDED Requirements

### Requirement: FND-01 Repositorio autónomo y procedencia
El proyecto MUST inicializarse como repositorio independiente PLN3_AgroRAG_GJR y documentar el código docente incorporado sin modificar PLN3_GJR.

#### Scenario: FND-01-independiente
- **GIVEN** un directorio nuevo y el paquete documental.
- **WHEN** se inicializa el proyecto.
- **THEN** la raíz tiene su propio Git, README, AGENTS y referencias al commit docente sin historial compartido.

#### Scenario: FND-01-existente
- **GIVEN** archivos locales previos en el destino.
- **WHEN** se prepara el proyecto.
- **THEN** se inspeccionan y preservan; no se sobrescribe contenido sin reconciliar.

### Requirement: FND-02 Inyección y límites de arquitectura
El backend MUST separar dominio, aplicación, infraestructura, API y bootstrap; el frontend SHALL depender exclusivamente del contrato HTTP.

#### Scenario: FND-02-imports
- **GIVEN** una implementación mínima de salud.
- **WHEN** se ejecuta la prueba de dependencias.
- **THEN** no hay imports de frameworks/proveedores en dominio ni de backend en UI.

#### Scenario: FND-02-sin-red
- **GIVEN** providers fake y sin credenciales.
- **WHEN** se importa el paquete y consulta salud.
- **THEN** no se inicia I/O externo ni carga de modelos.

### Requirement: FND-03 Ciclo TDD y entorno reproducible
Todo cambio de comportamiento MUST tener test rojo previo, verde y refactor documentados; dependencias SHALL fijarse con uv.lock y checks automáticos.

#### Scenario: FND-03-ciclo
- **GIVEN** un escenario nuevo.
- **WHEN** se desarrolla la tarea.
- **THEN** se registran fallo funcional inicial, éxito posterior y regresión del refactor.

#### Scenario: FND-03-clean
- **GIVEN** checkout limpio y lockfile.
- **WHEN** se instala y ejecuta CI offline.
- **THEN** la suite no requiere credenciales, no omite tests críticos y reporta checks reales.
