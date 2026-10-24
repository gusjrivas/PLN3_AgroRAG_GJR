# Contratos funcionales y HTTP propuestos

Estos contratos son especificaciones, no endpoints ya disponibles. Schema Pydantic y OpenAPI se implementarán primero con tests de contrato.

## Endpoints

| Método/ruta | Acceso | Éxito | Fallos |
|---|---|---|---|
| GET /health/live | loopback, sin secreto | 200 estado de proceso | No comprueba servicios facturados |
| GET /health/ready | lector | 200 corpus/modelos listos | 503 estado no disponible, sin revelar secretos |
| POST /v1/query | lector | 200 QueryResponse | 401, 422, 429, 502, 503, 504 |
| GET /v1/evidence/{evidence_id}?corpus_version=... | lector | 200 pasaje y procedencia | 404 si evidencia o versión no existe |
| GET /v1/corpus | lector | 200 manifiesto público del corpus activo | 503 si no hay corpus activo |

Ingesta mediante CLI local administrativa, fuera de la API pública del MVP. No endpoint de descarga de URLs arbitrarias. Roles reader/admin para credenciales de ejecución; la clave admin no se expone en frontend. UI usa una clave reader del lado servidor. Este diseño es local/single-user, no una solución de autenticación pública.

## QueryRequest

`question`: string no vacío tras strip, 1..2000 caracteres; `crop`: tomato|lettuce|null; `context`: objeto opcional con growth_stage, soil_description, measurement (value, unit, measurement_type), cada texto ≤500 caracteres. Rechazar NaN/Infinity, valores sin unidad o mediciones incoherentes mediante 422. `measurement_type` distingue volumetric_water_content, matric_potential y unknown: no convertir automáticamente porcentaje en potencial hídrico. `clarification_context`: pregunta original y hasta tres respuestas previas limitadas; se validan como datos del usuario. Sin memoria global de conversación.

## QueryResponse

Campos: request_id (UUID), status (answered|needs_clarification|insufficient_evidence), answer (string), claims (lista de claim_id, text, evidence_ids), citations (lista de evidence_id, source_id, title, edition, pdf_page, printed_page, section, excerpt, source_url), missing_information (lista), limitations (lista), corpus_version, verification (decision, revision_count, issue_codes), usage (llm_calls, input_tokens, output_tokens, estimated, total_ms, cache_hit).

Invariantes: answered exige claims no vacíos y evidencia por cada claim; IDs se resuelven en catálogo de la misma corpus_version. needs_clarification exige missing_information. insufficient_evidence explica el límite y no añade recomendaciones inventadas. No se expone chain-of-thought. Metadata administrativa como claves, rutas absolutas y stacktraces nunca forma parte de la respuesta.

## ErrorResponse

`error: {code, message, request_id, retryable}`. 401 auth inválida; 422 input; 429 saturación; 502 salida/proveedor inválido; 503 índice/modelo/corpus no disponible; 504 deadline. UI distingue todos estos casos de insufficient_evidence.

Cuando el error ocurre dentro del caso de uso, `request_id` MUST coincidir con el evento de
auditoría de esa ejecución. El mensaje interno y el texto de la excepción no forman parte del
contrato HTTP ni del evento.

## Puertos Python y datos internos

- Retriever.search(query, filters, budget) → list[EvidenceHit]; scores identifican su etapa, nunca se llaman probabilidad de verdad.
- EvidenceCatalog.get(evidence_id, corpus_version) → Evidence o NotFound.
- Researcher.run(question, context, feedback, budget) → Draft|Clarification|NoEvidence.
- Verifier.run(draft, evidence, budget) → VerificationResult.
- ModelGateway.generate(messages, schema, budget) → StructuredGeneration + Usage.
- AuditSink.record(event) → None, sin texto sensible.
- Clock y Budget permiten tests deterministas de deadline y límites.

Los agentes sólo referencian evidencia registrada. El backend construye URLs/citas desde el catálogo, nunca confía en URLs inventadas por el LLM. La UI utiliza GET de evidencia para mostrar la fuente.
