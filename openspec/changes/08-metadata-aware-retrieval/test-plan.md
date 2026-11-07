# Pruebas de aceptación: 08-metadata-aware-retrieval

Estado: plan aprobado por el usuario el 07/11/2026; implementación no iniciada. Todo resultado de
esta tabla permanece pendiente hasta registrar RED/GREEN/REFACTOR real.

| Escenario | Test inicial previsto | Nivel / evidencia |
|---|---|---|
| META-01-propagacion | `test_metadata_is_propagated_to_evidence` | integración corpus / META-01 |
| META-01-rechazo | `test_uncontrolled_or_unsupported_metadata_is_rejected` | integración corpus / META-01 |
| META-01-version | `test_metadata_change_creates_new_version_without_activation_on_failure` | integración corpus / META-01 |
| META-02-cultivo | `test_incompatible_crop_is_excluded_and_general_evidence_survives` | unit application / META-02 |
| META-02-prioridad | `test_exact_metadata_precedes_general_and_unknown` | unit application / META-02 |
| META-02-sin-filtro | `test_absent_stage_and_region_preserve_baseline_order` | unit retrieval / META-02 |
| META-03-cache | `test_retrieval_cache_key_includes_metadata_filters` | unit query / META-03 |
| META-03-aclaracion | `test_missing_situational_context_clarifies_without_model_call` | unit query / META-03 |
| META-03-insuficiente | `test_complete_context_without_compatible_evidence_abstains` | unit + contract / META-03 |
| META-03-general | `test_general_documentary_question_does_not_require_region` | contract API / META-03 |
| META-04-payload | `test_index_payload_contains_safe_metadata_without_text` | unit Pinecone / META-04 |
| META-04-fallo | `test_partial_metadata_index_does_not_publish_manifest` | unit Pinecone / META-04 |
| META-05-comparacion | `test_metadata_evaluation_packet_is_version_bound` | unit evaluation + corrida / META-06 |
| META-05-no-mejora | `test_report_does_not_claim_improvement_without_gate` | unit report / META-06 |

Comandos exactos, códigos de salida y logs se fijarán en cada evidencia. Las pruebas offline no
autorizan red, modelos o servicios pagos. Pinecone real y cualquier generación real requieren
autorización y se registran por separado.
