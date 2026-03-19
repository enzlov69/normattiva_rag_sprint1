# FINAL_AB_UNIFIED_COMPLIANCE_MATRIX_v1

| Area di controllo | Presidio | Layer responsabile | Stato | Blocco in caso di violazione | Test di copertura | Note |
| --- | --- | --- | --- | --- | --- | --- |
| Contratti A/B | Forbidden fields | Livello B + Gate A/B | ATTIVO | SI | `tests/test_final_ab_forbidden_fields_registry.py`, `tests/test_final_ab_response_contracts.py` | Nessun campo decisorio o validativo nel Livello B |
| Contratti A/B | Documentary packet minimum | Livello B documentale | ATTIVO | SI | `tests/test_final_ab_minimum_documentary_packet.py` | Supporto solo documentale |
| Boundary | M07 boundary | Livello A governance + Gate A/B | ATTIVO | SI | `tests/test_final_ab_boundary_m07.py` | Supporto documentale non equivale a chiusura M07 |
| Runtime | Block propagation | Runtime bridge + Livello A | ATTIVO | SI | `tests/test_final_ab_runtime_block_registry.py`, `tests/test_final_ab_runtime_end_to_end.py` | I blocchi critici propagano al Livello A |
| Intake | Intake gate | Livello A | ATTIVO | SI | `tests/test_final_ab_level_a_intake_gate.py` | Nessuna response B->A entra senza classificazione |
| Consumption | Consumption rules | Livello A | ATTIVO | SI | `tests/test_final_ab_response_consumption_rules.py` | Distinzione support_only/degraded/quarantine/reject |
| Consumption | Quarantine | Livello A | ATTIVO | SI | `tests/test_final_ab_response_quarantine_registry.py` | Le response contaminate non sono consumate |
| Isolation | Decision isolation | Livello A | ATTIVO | SI | `tests/test_final_ab_decision_isolation.py` | I moduli sensibili restano schermati |
| Audit | Consumption audit trail | Livello A | ATTIVO | SI | `tests/test_final_ab_consumption_traceability.py`, `tests/test_level_a_consumption_audit_trail.py` | Ricostruibilita' ex post del consumo |
| Review | Manual review gate | Livello A | ATTIVO | SI | `tests/test_final_ab_manual_review_gate.py`, `tests/test_level_a_manual_review_gate_policy.py` | Review richiesta prima della chiusura finale |
| Approval | Final human approval trace | Livello A umano | ATTIVO | SI | `tests/test_final_ab_final_human_approval_non_delegability.py`, `tests/test_level_a_final_human_approval_trace.py` | L'approvazione resta distinta dal supporto documentale |

## Copertura Fasi 10-14

- Fase 10: contratti A/B, forbidden fields, documentary packet, boundary M07
- Fase 11: runtime handoff e propagazione blocchi
- Fase 12: intake gate, consumption rules, quarantine
- Fase 13: consumption audit trail, decision isolation
- Fase 14: manual review gate, final human approval trace

## Regola interpretativa

Questa matrice e' un presidio di conformita' tecnica unificata.
Non equivale a decisione amministrativa, non sostituisce Final Compliance Gate e non autorizza output opponibili.
