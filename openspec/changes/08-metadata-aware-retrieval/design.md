# Design: Recuperación sensible a metadatos curados

## Context

El manifiesto actual ya declara procedencia y `crop`; `Evidence` conserva fuente, título, edición,
página, sección y cultivo. BM25 usa sección+texto y tanto BM25 como Pinecone filtran cultivo. La API
acepta `growth_stage`, pero `QueryService` llama a retrieval sólo con pregunta y cultivo. Pinecone
guarda metadata mínima de identidad y cultivo. Este cambio extiende el flujo existente en vez de
crear otro índice o agente.

## Goals / Non-Goals

Goals:

- Curar metadata con procedencia verificable y vocabularios controlados.
- Aplicar la misma semántica de compatibilidad en BM25, vector, hybrid y hybrid_rerank.
- Conservar evidencia general cuando no haya coincidencia específica.
- Diferenciar falta de contexto del usuario de falta de evidencia aplicable.
- Medir el efecto antes de adoptar la variante.

Non-goals:

- Inferir automáticamente etapa, región o aplicabilidad.
- Agregar búsqueda web, sensores, automatización de riego o una taxonomía científica universal.
- Convertir metadata del sistema de archivos en señal de ranking.
- Cambiar BM25 como modo público por defecto en este cambio.

## Data contract

Nivel fuente:

- `source_type`: `technical_manual`, `technical_guide` o `institutional_fact_sheet`.

Nivel página/selección, propagado a cada `Evidence`:

- `growth_stages`: lista ordenada sin duplicados con valores iniciales
  `establishment`, `vegetative_growth`, `flowering`, `fruit_set`, `fruit_development` y
  `pre_harvest`.
- `applicable_regions`: identificadores controlados documentados; inicialmente
  `ar-mendoza-oasis-norte` cuando la fuente lo declara. Lista vacía no afirma región.
- `applicability`: `general`, `specific` o `unknown`.

Se conserva `crop` como campo singular compatible con el contrato actual. Un campo sólo se completa
si el documento o la selección curada lo respalda. `unknown` y ausencia no equivalen a
incompatibilidad. Todo cambio del manifiesto participa en `corpus_version`, genera snapshot nuevo y
no reutiliza IDs ni namespaces.

## Retrieval contract

`Retriever.search` y los rankers reciben un valor inmutable `RetrievalFilters` con `crop`,
`growth_stage` y `region`. Los filtros provienen exclusivamente del request estructurado.

Una política pura y compartida clasifica cada candidato:

1. `exact`: coincide con todos los filtros específicos declarados.
2. `general`: declara aplicabilidad general y no contradice filtros.
3. `unknown`: carece de metadata suficiente y no contradice filtros.
4. `incompatible`: contradice cultivo u otra restricción explícita.

Se excluye `incompatible` y se conserva el orden del proveedor dentro de cada clase. Luego aplican
diversidad por `source_id`, presupuesto y límites actuales. Cultivo incompatible es filtro estricto;
etapa y región se usan inicialmente para priorizar, no para vaciar el resultado. La política común
vive en application y no se duplica en SDKs.

BM25 mantiene sección+texto como contenido lexical y no requiere tokenizer semántico, embeddings o
red. Pinecone puede empujar filtros seguros de identidad/cultivo, pero la clasificación autoritativa
se resuelve contra el catálogo local. El texto completo nunca se almacena en metadata remota.

## Query and sufficiency

`Context` agrega `region`. `QueryService` construye `RetrievalFilters`; la clave de caché incluye sus
campos. El contexto entregado a investigador/verificador incluye metadata relevante junto con ID y
texto, sin convertir metadata en prueba factual.

Una recomendación situacional que requiera datos ausentes termina en `needs_clarification` antes del
LLM. Si el contexto requerido está presente pero retrieval no obtiene evidencia compatible, termina
en `insufficient_evidence`. Las preguntas documentales generales no exigirán región o etapa.

## Delivery sequence and ownership

Los contratos se estabilizan secuencialmente con META-01 y META-02. Después pueden trabajar como
máximo dos implementadores: META-03 (backend/API) y META-04 (Pinecone), con archivos disjuntos. La
curación, reindexado y evaluación comienzan sólo después de integrar esos contratos. El coordinador
integra; un revisor distinto revisa cuando esté disponible.

## TDD and evidence

Cada corte escribe primero su escenario observable, registra RED funcional, implementa GREEN y
ejecuta REFACTOR con suite afectada, Ruff, mypy, límites de arquitectura y OpenSpec. La curación
manual no inventa una fase roja; sus validaciones ejecutables sí siguen TDD. Evidencia en
`docs/evidence/tdd/META-*.md`, con comandos, códigos, commit, limitaciones y distinción offline/live.

## Rollout and rollback

La ingesta local crea un snapshot nuevo. La indexación semántica administrativa usa namespace
fresco y publica su manifiesto al final. Una falla conserva catálogo y namespace activos anteriores.
La variante no cambia el default hasta completar comparación y decisión explícita. Rollback reactiva
la versión anterior; nunca limpia recursos activos para ocultar un resultado.

## Risks / trade-offs

- El corpus de 27 fragmentos puede ser demasiado pequeño para demostrar mejora; se reportará.
- Filtros estrictos de etapa/región reducirían recall; por eso comienzan como priorización.
- Una taxonomía demasiado detallada induciría inferencias no respaldadas; se mantiene mínima.
- Agregar metadata cambia IDs y qrels; la migración exige correspondencia de pasajes y revisión
  humana, no reemplazos por posición.
