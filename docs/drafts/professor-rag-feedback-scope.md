# Borrador de alcance: metadatos y suficiencia de contexto en el RAG

Estado: **borrador no normativo; pendiente de recomendación docente**.  
Fecha de registro: 31/10/2026.  
Responsable: Gustavo Julián Rivas, con asistencia de Codex.  
Rama documental: `docs/professor-rag-feedback-draft`.

Este documento conserva el alcance posible derivado del comentario de la profesora. No aprueba una
arquitectura, no modifica requisitos y no autoriza cambios de código, corpus, índice, API, UI ni
evaluación. Cuando llegue la explicación de cómo integrar los metadatos dentro del flujo, se revisará
este borrador y recién entonces se propondrá un delta de ADR/OpenSpec.

## Comentario recibido

La profesora consideró la propuesta alineada con la materia y recomendó explorar, cuando la
documentación lo permita:

- metadatos de tipo de cultivo, etapa de desarrollo, región y fuente asociados a los chunks;
- uso de esos metadatos durante la recuperación para obtener información más específica;
- reconocimiento explícito de los casos donde las condiciones particulares del cultivo no alcanzan
  para producir una recomendación concreta.

La profesora anticipó una explicación posterior sobre la integración de estos metadatos en el flujo.
Esa explicación es una entrada pendiente y puede cambiar las alternativas descritas abajo.

## Capacidades actuales que deben preservarse

- `crop` ya se cura por página, se propaga a cada `Evidence` y filtra tanto el baseline BM25 como el
  ranker Pinecone.
- Cada chunk conserva `source_id`, título, edición, URL, sección y página; la selección limita la
  concentración de pasajes de una misma fuente.
- La API acepta etapa del cultivo, descripción del suelo y medición estructurada como contexto.
- El preflight puede responder `needs_clarification` sin invocar el modelo para ciertas decisiones
  situacionales y `insufficient_evidence` cuando la consulta está fuera de alcance.
- Las respuestas verificadas sólo pueden citar IDs existentes en el catálogo activo.

Referencias actuales:

- `src/agro_rag/infrastructure/corpus.py`
- `src/agro_rag/domain/evidence.py`
- `src/agro_rag/infrastructure/retrieval.py`
- `src/agro_rag/infrastructure/pinecone.py`
- `src/agro_rag/application/query.py`
- `src/agro_rag/api/schemas.py`

## Alcance candidato sujeto a revisión

### 1. Metadatos curados

Evaluar campos opcionales y trazables para:

- etapa o etapas de desarrollo a las que aplica el pasaje;
- región de aplicabilidad agronómica, distinta de la ubicación de publicación o de la región
  técnica del proveedor de infraestructura;
- tipo de fuente, por ejemplo manual técnico, guía institucional o artículo;
- los metadatos actuales de cultivo y fuente.

Un metadato sólo podría cargarse cuando esté declarado o respaldado por la documentación curada.
No se inferirían región, etapa o aplicabilidad a partir del nombre de una institución o de una
suposición del agente.

### 2. Propagación dentro del flujo

La alternativa inicial a contrastar con la explicación docente es:

```text
manifiesto curado
  -> página o selección revisada
  -> chunk / Evidence
  -> snapshot SQLite
  -> metadata del índice semántico
  -> filtros o priorización de recuperación
  -> contexto citado del agente
```

Los campos formarían parte de la identidad del corpus. Cualquier cambio exigiría un snapshot y un
namespace nuevos; no se mutaría el catálogo activo ni se reutilizaría un índice incompatible.

### 3. Recuperación sensible al contexto

Evaluar, sin decidir todavía entre filtro estricto, priorización o combinación:

- coincidencia por cultivo;
- coincidencia por etapa y región cuando el usuario las proporcione;
- conservación controlada de evidencia general sin esos metadatos;
- diversidad por fuente;
- trazabilidad de los filtros aplicados sin registrar preguntas completas ni datos sensibles.

### 4. Suficiencia para recomendaciones concretas

Evaluar un contrato estructurado que distinga una pregunta documental general de una recomendación
operativa para un cultivo particular. Según la pregunta, podrían ser necesarios:

- cultivo y etapa;
- suelo o capacidad de retención;
- región o condiciones ambientales;
- medición actual con valor, unidad y tipo;
- sistema o frecuencia de riego.

Si falta contexto del usuario, el resultado candidato es `needs_clarification` sin llamada al LLM.
Si el contexto está completo pero el corpus no contiene evidencia compatible, el resultado candidato
es `insufficient_evidence`. Ambos casos deben diferenciarse en la API, la UI y la evaluación.

## Validaciones candidatas

Si el alcance es aceptado más adelante, el cambio debería comenzar con pruebas que cubran:

- admisión y propagación de metadatos declarados;
- rechazo de valores no controlados y ausencia de inferencias no respaldadas;
- equivalencia de filtros relevantes entre BM25 y Pinecone;
- fallback explícito a evidencia general, si la estrategia aprobada lo permite;
- aclaración sin llamada al modelo cuando falta contexto;
- abstención cuando no existe evidencia aplicable;
- regresión de Recall@k, citas y estados sobre el benchmark congelado;
- reconstrucción versionada del corpus sin sobrescribir el snapshot activo.

Las pruebas de contrato y recuperación pueden ser offline. No se autoriza una evaluación paga por
este borrador.

## Decisiones pendientes de la explicación docente

1. En qué nivel se espera declarar cada metadato: fuente, página, chunk o varios niveles.
2. Si el uso esperado es filtrado previo, búsqueda con filtros, reordenamiento posterior o una
   combinación.
3. Qué vocabularios o taxonomías recomienda para etapa, región y tipo de fuente.
4. Cómo tratar pasajes generales o documentos sin todos los metadatos.
5. Qué condiciones mínimas espera para considerar suficiente una recomendación de riego.
6. Qué evidencia o métrica espera ver en la entrega académica.

## Condición de activación

Este borrador podrá convertirse en trabajo activo sólo después de:

1. recibir la explicación pendiente de la profesora;
2. reconciliarla con el corpus y los contratos existentes;
3. acordar el alcance con el usuario;
4. registrar un ADR o delta de ADR si cambia la arquitectura;
5. crear proposal/design/spec/tasks OpenSpec y evidencia TDD propia.

Hasta entonces, el comentario docente queda registrado como oportunidad de mejora y no como una
tarea implementada, un requisito aprobado ni un bloqueo de la PoC V2 single-host.
