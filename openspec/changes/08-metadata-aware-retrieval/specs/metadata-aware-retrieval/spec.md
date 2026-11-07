# Recuperación sensible a metadatos curados

## ADDED Requirements

### Requirement: META-01 Metadata curada y versionada
La ingesta MUST admitir tipo de fuente, etapas de desarrollo, regiones de aplicabilidad y alcance
general/específico/desconocido sólo cuando estén respaldados por el corpus curado, y MUST propagar
esos valores a cada evidencia sin inferencias automáticas.

#### Scenario: META-01-propagacion
- **GIVEN** fuente y selección con metadata válida y revisada.
- **WHEN** se construye el catálogo.
- **THEN** cada evidencia conserva exactamente la metadata aplicable y su procedencia direccionable.

#### Scenario: META-01-rechazo
- **GIVEN** valor fuera del vocabulario o región deducida sin respaldo documental.
- **WHEN** se intenta admitir el manifiesto.
- **THEN** la ingesta falla con diagnóstico y no activa un snapshot parcial.

#### Scenario: META-01-version
- **GIVEN** mismos PDF y chunking pero cambia metadata curada.
- **WHEN** se reconstruye el corpus.
- **THEN** se genera otra versión e IDs deterministas, conservando activa la versión anterior hasta verificación.

### Requirement: META-02 Compatibilidad y priorización comunes
La recuperación MUST excluir candidatos explícitamente incompatibles y MUST priorizar coincidencias
exactas, evidencia general y metadata desconocida en ese orden, con la misma política para BM25 y
modos semánticos.

#### Scenario: META-02-cultivo
- **GIVEN** consulta de tomate, evidencia exclusiva de lechuga y evidencia agronómica general.
- **WHEN** se recupera contexto.
- **THEN** se excluye la evidencia incompatible y se conserva la general.

#### Scenario: META-02-prioridad
- **GIVEN** candidatos con igual compatibilidad de cultivo y distinta coincidencia de etapa o región.
- **WHEN** se priorizan candidatos.
- **THEN** exactos preceden a generales y desconocidos sin alterar el orden del proveedor dentro de cada clase.

#### Scenario: META-02-sin-filtro
- **GIVEN** consulta sin etapa ni región estructuradas.
- **WHEN** se ejecuta retrieval.
- **THEN** esos campos no restringen resultados y el baseline conserva su comportamiento observable.

### Requirement: META-03 Contexto y suficiencia observables
La API MUST propagar filtros estructurados a retrieval, MUST aislar la caché por filtros y MUST
distinguir falta de contexto de falta de evidencia compatible.

#### Scenario: META-03-cache
- **GIVEN** misma pregunta y cultivo con dos regiones o etapas diferentes.
- **WHEN** se realizan ambas consultas.
- **THEN** no comparten una entrada de caché de retrieval.

#### Scenario: META-03-aclaracion
- **GIVEN** recomendación situacional sin el contexto mínimo requerido.
- **WHEN** se consulta.
- **THEN** responde `needs_clarification` sin llamar al LLM.

#### Scenario: META-03-insuficiente
- **GIVEN** contexto requerido completo pero ninguna evidencia compatible.
- **WHEN** se consulta.
- **THEN** responde `insufficient_evidence` sin inventar una recomendación.

#### Scenario: META-03-general
- **GIVEN** pregunta documental general directamente respondible.
- **WHEN** no incluye etapa o región.
- **THEN** continúa al retrieval normal sin exigir contexto situacional innecesario.

### Requirement: META-04 Índice remoto mínimo e inmutable
La indexación semántica MUST guardar metadata mínima sin texto completo, MUST usar un namespace
fresco por versión y MUST publicar identidad sólo después de verificar todos los IDs.

#### Scenario: META-04-payload
- **GIVEN** catálogo con metadata curada.
- **WHEN** se prepara el upsert.
- **THEN** cada vector contiene identidad y filtros admitidos, pero no texto ni rutas locales.

#### Scenario: META-04-fallo
- **GIVEN** falla parcial o índice incompatible.
- **WHEN** se indexa la nueva versión.
- **THEN** no se publica su manifiesto y la versión activa anterior permanece utilizable.

### Requirement: META-05 Evaluación comparativa trazable
El proyecto MUST comparar el baseline vigente y la variante sensible a metadata sobre casos
versionados, y MUST reportar recuperación, compatibilidad, estados, citas y latencia aunque el
resultado no mejore.

#### Scenario: META-05-comparacion
- **GIVEN** benchmark congelado y suplemento de casos con contexto revisado.
- **WHEN** se ejecutan baseline y variante sobre el mismo catálogo.
- **THEN** se registran Recall@k, MRR/nDCG, incompatibles en top-k, estados, citas y latencia.

#### Scenario: META-05-no-mejora
- **GIVEN** métricas iguales o peores que el baseline.
- **WHEN** se revisan resultados.
- **THEN** se conserva el reporte, no se afirma mejora y no se cambia el default sin otra decisión.
