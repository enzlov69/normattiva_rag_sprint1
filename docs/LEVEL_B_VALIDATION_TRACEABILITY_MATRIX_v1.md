# LEVEL_B_VALIDATION_TRACEABILITY_MATRIX_v1

## Scopo

Matrice di tracciabilità tra principi fondativi/architetturali del progetto, regole semantiche implementate nel Validation Kit offline del Livello B e casi di test che dimostrano il comportamento atteso.

## Regola di uso

Questa matrice non sostituisce i documenti fondativi. Serve a dimostrare che i vincoli di subordinazione del Livello B sono stati tradotti in controlli tecnici verificabili, senza integrazione runtime.

## Struttura delle colonne

- `rule_id`: identificativo stabile della regola tecnica
- `source_document`: fonte progettuale prevalente
- `source_principle`: principio o vincolo da rendere eseguibile
- `validator_entrypoint`: funzione o entrypoint che presidia la regola
- `semantic_rule`: formulazione tecnica della regola
- `fixture_path`: payload offline di prova
- `test_module`: modulo pytest che esegue la verifica
- `expected_ok`: esito atteso
- `expected_findings_any_of`: finding minimo atteso

## Matrice sintetica

| rule_id | source_document | validator_entrypoint | fixture_path | expected_ok | expected_findings_any_of |
|---|---|---|---|---:|---|
| LBR-001 | 00_Fondativo_Normattiva_RAG_Metodo_Cerda_v2.md | `validators.level_b_semantic_rules.scan_for_forbidden_fields` | `tests/fixtures/level_b_payloads/reject/forbidden_final_decision.json` | false | FORBIDDEN_LEVEL_B_FIELD |
| LBR-002 | 01_architettura_v2.md | `validators.level_b_semantic_rules.scan_for_forbidden_fields` | `tests/fixtures/level_b_payloads/reject/forbidden_text_semantics.json` | false | FORBIDDEN_LEVEL_B_SEMANTICS |
| LBR-003 | MASTER_Normattiva_RAG_Metodo_Cerda_v2.docx | `validators.level_b_semantic_rules.validate_m07_boundaries` | `tests/fixtures/level_b_payloads/reject/m07_closed_true.json` | false | M07_BOUNDARY_VIOLATION, M07_SUPPORT_HUMAN_COMPLETION_REQUIRED |
| LBR-004 | 00_Fondativo_Normattiva_RAG_Metodo_Cerda_v2.md | `validators.level_b_semantic_rules.validate_audit_shadow` | `tests/fixtures/level_b_payloads/reject/missing_audit_shadow.json` | false | AUDIT_SHADOW_REQUIRED |
| LBR-005 | 04_test_v2.md | `validators.level_b_semantic_rules.validate_status_coherence` | `tests/fixtures/level_b_payloads/reject/blocked_without_blocks.json` | false | BLOCKS_REQUIRED_FOR_BLOCKED_STATUS |
| LBR-006 | 04_test_v2.md | `validators.level_b_semantic_rules.validate_status_coherence` | `tests/fixtures/level_b_payloads/reject/critical_block_status_mismatch.json` | false | CRITICAL_BLOCK_STATUS_MISMATCH |
| LBR-007 | 00_Fondativo_Normattiva_RAG_Metodo_Cerda_v2.md | `validators.level_b_semantic_rules.validate_citations` | `tests/fixtures/level_b_payloads/reject/citation_valid_without_uri.json` | false | CITATION_VALID_WITHOUT_URI |
| LBR-008 | 01_architettura_v2.md | `validators.level_b_payload_validator.validate_level_b_payload` | `tests/fixtures/level_b_payloads/degrade/coverage_degraded.json` | true | — |
| LBR-009 | schemas/level_b_status_registry_v1.json | `validators.level_b_semantic_rules.validate_status_coherence` | `tests/fixtures/level_b_payloads/reject/success_with_warnings_without_warnings.json` | false | WARNINGS_REQUIRED_FOR_DEGRADED_STATUS |
| LBR-010 | schemas/level_b_status_registry_v1.json | `validators.level_b_payload_validator.validate_level_b_payload` | `tests/fixtures/level_b_payloads/pass/success_with_warnings_valid.json` | true | — |
| LBR-011 | MASTER_Normattiva_RAG_Metodo_Cerda_v2.docx | `validators.level_b_semantic_rules.validate_m07_boundaries` | `tests/fixtures/level_b_payloads/reject/m07_support_human_completion_missing.json` | false | M07_SUPPORT_HUMAN_COMPLETION_REQUIRED |

## Criteri di lettura

1. Se `expected_ok=false`, il test deve dimostrare che il validator intercetta la violazione senza introdurre logiche decisorie.
2. Se `expected_ok=true`, il test deve dimostrare che il payload resta entro il perimetro documentale consentito al Livello B.
3. Le regole M07, citazioni, audit/SHADOW e blocchi sono trattate come guardrail fondativi, non come opzionali migliorativi.
4. Ogni futura integrazione runtime dovrà prima superare integralmente questa matrice offline.
