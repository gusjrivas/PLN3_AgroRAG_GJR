# Recuperación híbrida y reranking evaluables

## ADDED Requirements

### Requirement: RET-01 Cuatro modos comparables
El sistema MUST ofrecer modos BM25, vectorial, híbrido RRF e híbrido con reranker sobre un corpus y conjunto de chunks comunes.

#### Scenario: RET-01-ranking
- **GIVEN** fixtures y rankings esperados.
- **WHEN** se ejecutan los cuatro modos.
- **THEN** se preservan filtros, IDs y orden determinista donde aplica y se registran scores por etapa.

#### Scenario: RET-01-fallo-vector
- **GIVEN** modo híbrido y Pinecone inaccesible.
- **WHEN** se consulta.
- **THEN** se informa indisponibilidad; no se etiqueta BM25 solo como resultado híbrido.

### Requirement: RET-02 Idioma y compatibilidad del índice
Los embeddings MUST aplicar los prefijos requeridos y verificar modelo, revisión, dimensión y corpus_version; reranker SHALL evaluarse en español antes de selección.

#### Scenario: RET-02-e5
- **GIVEN** modelo multilingual-e5-small.
- **WHEN** se codifica consulta y pasajes.
- **THEN** se usan query: y passage: respectivamente y se registran revisiones.

#### Scenario: RET-02-incompatible
- **GIVEN** índice de otro modelo incluso con igual dimensión.
- **WHEN** se inicia retrieval.
- **THEN** se rechaza incompatibilidad y se exige construir otra versión.

#### Scenario: RET-02-baseline-bilingüe
- **GIVEN** una consulta española y un pasaje FAO inglés con vocabulario agronómico equivalente.
- **WHEN** se ejecuta el baseline BM25.
- **THEN** la normalización lexical versionada permite comparar esos conceptos sin etiquetar el
  resultado como semántico ni realizar traducción remota.

### Requirement: RET-03 Diversidad y contexto
El contexto MUST limitar fragmentos por source_id y tokens reales, y sólo incluir evidencias resolubles de la versión activa.

#### Scenario: RET-03-diversidad
- **GIVEN** varias páginas del mismo PDF y otras fuentes.
- **WHEN** se selecciona contexto.
- **THEN** el cap aplica al archivo fuente y no a cada página.

#### Scenario: RET-03-amplitud-configurable
- **GIVEN** evidencia relevante detrás de candidatos de fuentes diversas.
- **WHEN** el runtime BM25 selecciona contexto.
- **THEN** respeta el máximo configurado y conserva el cap por fuente con un default de seis
  fragmentos.

#### Scenario: RET-03-presupuesto
- **GIVEN** candidatos largos o ID obsoleto.
- **WHEN** se prepara contexto.
- **THEN** se respeta límite real, se excluye evidencia inválida y se informa insuficiencia si falta soporte.
