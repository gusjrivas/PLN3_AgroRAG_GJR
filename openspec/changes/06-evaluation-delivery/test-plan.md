# Pruebas de aceptación: 06-evaluation-delivery

Estado: escenarios ejecutables implementados; la corrida EVA-02 real y su revisión humana están
documentadas. Las verificaciones de instalación/publicación manual conservan evidencia operacional.

| Escenario | Test previsto | Nivel / evidencia |
|---|---|---|
| EVA-01-split | `test_eva_01_split_and_denominators_are_frozen`, `test_eva_01_rejects_family_leakage_and_unknown_evidence` | pytest por contrato; `docs/evidence/tdd/06-benchmark-contract.md` |
| EVA-01-sin-soporte | `test_eva_01_unanswerable_cases_never_enter_ir_denominator` | pytest por contrato; `docs/evidence/tdd/06-benchmark-contract.md` |
| EVA-02-comparacion | `test_eva_02_comparacion_preserves_provenance_denominators_and_errors`, `test_eva_02_rejects_unpaired_or_mixed_provenance` | pytest por contrato; `docs/evidence/tdd/06-evaluation-report.md`; corrida real en `docs/evidence/tdd/EVA-02-budgeted-live.md` |
| EVA-02-negativo | `test_eva_02_negativo_is_reported_without_cherry_picking` | pytest por contrato y revisión humana 12 PASS/6 FAIL; `docs/evidence/tdd/EVA-02-budgeted-live.md` |
| DEL-01-reproduccion | `test_del_01_reproduccion_validates_required_package_and_commands`, `test_del_01_reproduccion_rejects_incomplete_or_placeholder_package` | pytest, verificador offline y reproducción limpia; `docs/evidence/tdd/06-delivery-package.md` |
| DEL-01-informe | `test_del_01_informe_builds_a_readable_pdf` | pytest, extracción y revisión visual de 7 páginas; `docs/evidence/tdd/06-delivery-package.md` |
