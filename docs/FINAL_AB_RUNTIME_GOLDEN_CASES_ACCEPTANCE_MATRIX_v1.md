# FINAL AB Runtime Golden Cases Acceptance Matrix v1

| Case ID | Cluster | anomaly_code | family | severity | signal | runtime_effect | envelope_status | propagate_to_level_a | level_a_effect | blocks_opponibility |
|---|---|---|---|---|---|---|---|---|---|---|
| GC-01 | WARNING | MISSING_CALLER_MODULE | CONTRACTUAL | MEDIUM | WARNING | PROPAGATE_WARNING | SUCCESS_WITH_WARNINGS | true | REVIEW_REQUIRED | false |
| GC-02 | INTERNAL | TECHNICAL_INTERNAL_SIGNAL | COMPLETENESS | LOW | INTERNAL | INTERNAL_SIGNAL | SUCCESS | false | NONE | false |
| GC-03 | DEGRADED | DOCUMENTARY_PACKET_INCOMPLETE | DOCUMENTARY | HIGH | ERROR | DEGRADE_RESPONSE | DEGRADED | true | SUPPORT_ONLY | true |
| GC-04 | DEGRADED | DOCUMENTARY_PACKET_TRACE_MISSING | TRACEABILITY | HIGH | ERROR | DEGRADE_RESPONSE | DEGRADED | true | SUPPORT_ONLY | true |
| GC-05 | BLOCKED | DOCUMENTARY_PACKET_INTEGRITY_BROKEN | DOCUMENTARY | CRITICAL | BLOCK | BLOCK_RESPONSE | BLOCKED | true | STOP_FLOW | true |
| GC-06 | BLOCKED | AUDIT_INCOMPLETE | TRACEABILITY | CRITICAL | BLOCK | BLOCK_RESPONSE | BLOCKED | true | STOP_FLOW | true |
| GC-07 | REJECTED | FORBIDDEN_FIELD_PRESENT | BOUNDARY | CRITICAL | BLOCK | REJECT_RESPONSE | REJECTED | true | HARD_STOP | true |
| GC-08 | REJECTED | RAG_SCOPE_VIOLATION | BOUNDARY | CRITICAL | BLOCK | REJECT_RESPONSE | REJECTED | true | HARD_STOP | true |
| GC-09 | REJECTED | M07_BOUNDARY_VIOLATION | BOUNDARY | CRITICAL | BLOCK | REJECT_RESPONSE | REJECTED | true | HARD_STOP | true |

## Lettura rapida
- **WARNING**: visibile e propagato, senza blocco opponibilita'.
- **INTERNAL**: segnale tecnico non propagato.
- **DEGRADED**: supporto documentale/tracciabilita' non piena.
- **BLOCKED**: opponibilita' tecnica bloccata.
- **REJECTED**: violazione boundary/non-delega, con hard stop.

## Evidenze speciali
- Casi boundary/M07: `GC-07`, `GC-08`, `GC-09`.
- Casi documentary integrity/opponibilita': `GC-05`, `GC-06`.
- Casi non bloccanti: `GC-01`, `GC-02`, `GC-03`, `GC-04`.
