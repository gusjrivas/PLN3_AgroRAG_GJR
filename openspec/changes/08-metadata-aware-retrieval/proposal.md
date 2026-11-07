# Proposal: Recuperación sensible a metadatos curados

## Why

La devolución docente recomendó asociar cultivo, etapa de desarrollo, región y fuente a los chunks
y usar esos datos para recuperar evidencia más específica. El producto ya conserva procedencia y
`crop`, pero la etapa y la región sólo llegan como contexto del agente y no gobiernan retrieval. El
cambio cierra esa brecha sin reemplazar la arquitectura RAG, sin inferir aplicabilidad con un LLM y
sin presentar como mejora un resultado que todavía no fue medido.

## What Changes

- El corpus MUST admitir metadatos curados y trazables de tipo de fuente, etapa de desarrollo,
  región de aplicabilidad y alcance general/específico/desconocido.
- La recuperación MUST excluir incompatibilidades explícitas por cultivo y priorizar coincidencias
  de etapa/región por delante de evidencia general y metadata desconocida.
- BM25 y los modos semánticos MUST aplicar una política común sin cargar modelos ni red en el modo
  lexical.
- La API MUST propagar filtros estructurados a retrieval, separar aclaración de insuficiencia y
  aislar la caché por filtros.
- Pinecone MUST almacenar sólo metadata mínima, en un namespace nuevo ligado a la nueva versión de
  corpus; el catálogo local continúa siendo la autoridad para texto y procedencia.
- El benchmark MUST comparar baseline y variante sensible a metadata y reportar el resultado aunque
  no exista mejora.

## Capabilities

### New Capabilities

- `metadata-aware-retrieval`: metadata curada, recuperación contextual y suficiencia observable.

### Modified Capabilities

- `corpus`: amplía la evidencia direccionable sin mutar snapshots existentes.
- `retrieval`: amplía filtros y priorización conservando los cuatro modos actuales.
- `agents-backend`: propaga contexto estructurado y preserva estados públicos existentes.
- `evaluation-delivery`: incorpora una comparación nueva sin modificar el benchmark congelado.

## Impact

Propietario: coordinador con cortes RAG/datos, backend/agentes y evaluación. Dependencias:
capacidades implementadas de 02-corpus, 03-retrieval, 04-agents-backend y el benchmark estable de
06-evaluation-delivery. El trabajo es independiente del cierre Garak de 07, pero debe partir de una
base integrada y limpia.

Rutas principales: `data/manifest.json`, dominio de evidencia, ingesta, contratos y adaptadores de
retrieval, API/caso de uso, Pinecone, benchmark y pruebas afectadas. Decisiones: ADR-005, ADR-006,
ADR-010, ADR-013 y ADR-016.

No se extrae metadata mediante LLM, no se toma `mtime`/nombre local como señal agronómica, no se
infiere región por institución, no se sobrescribe el catálogo activo y no se activa por defecto un
modo semántico.
