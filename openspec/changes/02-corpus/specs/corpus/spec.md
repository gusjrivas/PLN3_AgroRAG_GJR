# Corpus versionado con evidencia

## ADDED Requirements

### Requirement: COR-01 Admisión con procedencia
La ingesta MUST aceptar sólo fuentes curadas con hash, edición, estado de derechos y páginas seleccionadas verificadas.

#### Scenario: COR-01-valido
- **GIVEN** PDF admitido y manifiesto completo.
- **WHEN** se ingiere.
- **THEN** quedan hash real, texto, página física y etiqueta impresa separadas.

#### Scenario: COR-01-invalido
- **GIVEN** archivo corrupto, escaneado sin texto o manifiesto incompleto.
- **WHEN** se ingiere.
- **THEN** falla con diagnóstico y no activa corpus parcial.

### Requirement: COR-02 Unidades y tablas
La extracción MUST conservar asociación de valores, unidades, cultivo y condiciones en toda tabla usada como evidencia.

#### Scenario: COR-02-tabla
- **GIVEN** fixture tabular con cultivo y unidad.
- **WHEN** se transforma a pasajes.
- **THEN** cada registro mantiene encabezados y fuente/página originales.

#### Scenario: COR-02-ambigua
- **GIVEN** extracción que mezcla columnas.
- **WHEN** se revisa admisión.
- **THEN** se bloquea ese contenido hasta corrección trazable, sin inventar valores.

### Requirement: COR-03 Versionado e idempotencia
El corpus MUST usar IDs inmutables y activación atómica sólo cuando catálogo e índice de la nueva versión estén verificados.

#### Scenario: COR-03-repeticion
- **GIVEN** mismos archivos/config.
- **WHEN** se repite ingesta.
- **THEN** se obtienen mismos IDs/version sin duplicados.

#### Scenario: COR-03-cambio
- **GIVEN** cambia un PDF o extracción.
- **WHEN** se reingiere.
- **THEN** se crea nueva versión; una falla conserva el corpus activo anterior.
