# Level B Payload Validation Rules v1

## 1. Purpose and Hierarchy of the Document

This document defines the formal validation rules for Level B payloads within the controlled bridge between:

- Metodo Cerda / Level A
- Normattiva RAG / Level B

Its purpose is to make Level B payload compliance testable, rejectable, and auditable.

This document is subordinate to:

1. Metodo Cerda RAG Bridge Spec v1
2. Metodo Cerda RAG Bridge Acceptance Matrix v1
3. Level B Payload Policy v1

If a conflict appears, the stricter rule prevails.

This document does not expand Level B powers.

It only defines how Level B payloads must be validated before they can cross the bridge toward Level A.

## 2. Minimum Required Payload Envelope

Every Level B payload must be wrapped in a minimum technical envelope.

The envelope must make the payload:

- attributable
- traceable
- classifiable
- rejectable
- auditable

Minimum required envelope:

- `request_id`
- `case_id`
- `trace_id`
- `payload_type`
- `payload_status`
- `source_layer`
- `producing_module`
- `audit_ref`
- `shadow_ref`

The envelope must identify:

- which request generated the payload
- which case it belongs to
- which trace produced it
- which module emitted it
- what type of payload it is
- what technical status it has

## 3. Required Keys

The following keys are mandatory in every Level B payload envelope.

- `request_id`
- `case_id`
- `trace_id`
- `payload_type`
- `payload_status`
- `source_layer`
- `producing_module`
- `warnings`
- `errors`
- `blocks`
- `audit_ref`
- `shadow_ref`

Required constraints:

- `source_layer` must identify Level B
- `warnings` must always exist, even if empty
- `errors` must always exist, even if empty
- `blocks` must always exist, even if empty
- `audit_ref` must point to the corresponding audit trail segment
- `shadow_ref` must point to the corresponding SHADOW trace segment

## 4. Optional Allowed Keys

The following keys are allowed when relevant to the request and the payload type.

- `activated_corpora`
- `relevant_source_list`
- `source_versions`
- `norm_units`
- `citations`
- `citation_ids`
- `blocked_citations`
- `coverage_notes`
- `coverage_status`
- `coverage_ref_id`
- `vigenza_notes`
- `vigenza_status`
- `cross_reference_notes`
- `crossref_status`
- `routing_notes`
- `documentary_confidence`
- `annex_notes`
- `m07_support_status`
- `m07_evidence_pack_ref`
- `technical_trace`
- `document_ids`
- `collection_ids`
- `query_metadata`

Allowed optional keys remain documentary and technical only.

Their presence does not authorize Level B to infer or emit final legal meaning.

## 5. Forbidden Keys

The following keys are forbidden in Level B payloads.

- `final_decision`
- `decision`
- `legal_conclusion`
- `final_applicability`
- `applicability_final`
- `motivazione_finale`
- `motivational_frame`
- `output_authorized`
- `final_authorization`
- `go`
- `go_finale`
- `no_go`
- `case_resolved`
- `final_decision_ready`
- `validation_finale`
- `validazione_finale`
- `atto_firmabile`
- `provvedimento_autorizzabile`
- `norma_prevalente_finale`
- `rac_generated`
- `ppav_closed`
- `m07_closed`
- `m07_completed`
- `m07_done`
- `m07_certified`

Presence of a forbidden key is a hard compliance failure.

## 6. Forbidden Semantic Aliases and Equivalent Conclusional/Validative Semantics

Validation must reject not only exact forbidden keys, but also semantic equivalents.

The following semantic families are forbidden even if expressed with different naming:

- final legal conclusion
- final applicability judgment
- final balancing between competing rules
- final motivation
- final validation of the act
- final authorization of output
- closure of PPAV
- closure, completion, or certification of M07
- conclusive “ready to sign” or “ready to issue” semantics
- conclusive “GO” semantics

Examples of forbidden semantic aliases:

- `ready_for_signature`
- `sufficient_for_decision`
- `final_rule_selected`
- `lawfulness_validated`
- `case_closed`
- `m07_ok`
- `m07_satisfied`
- `decision_supported_final`
- `authorizable_output`
- `compliance_final_pass`

Equivalent semantics must be rejected even if embedded:

- inside nested objects
- inside status labels
- inside booleans
- inside enums
- inside human-readable summary fields

## 7. Rejection Conditions

A Level B payload must be rejected if one or more of the following conditions occur.

1. missing required envelope key
2. malformed or empty `request_id`, `case_id`, or `trace_id`
3. missing `warnings`, `errors`, or `blocks`
4. forbidden key present
5. forbidden semantic equivalent present
6. conclusional or validative status in `payload_status`
7. M07 closure or certification semantics present
8. missing audit reference on a critical payload
9. missing SHADOW reference on a critical payload
10. block emitted internally but not exposed in `blocks`
11. unresolved critical issue masked as warning-only
12. routing notes or coverage notes used to imply final legal resolution

Rejected payloads must not pass the bridge as valid support outputs.

## 8. Fail Codes and Error Classes

Minimum fail codes:

- `PAYLOAD_ENVELOPE_MISSING`
- `PAYLOAD_REQUIRED_KEY_MISSING`
- `PAYLOAD_FORBIDDEN_KEY`
- `PAYLOAD_FORBIDDEN_SEMANTIC_ALIAS`
- `PAYLOAD_INVALID_STATUS`
- `PAYLOAD_M07_SCOPE_VIOLATION`
- `PAYLOAD_AUDIT_MISSING`
- `PAYLOAD_SHADOW_MISSING`
- `PAYLOAD_BLOCK_NOT_PROPAGATED`
- `PAYLOAD_COVERAGE_UNDECLARED`
- `PAYLOAD_VIGENZA_UNCERTAIN_UNDECLARED`
- `PAYLOAD_CROSSREF_UNRESOLVED_UNDECLARED`
- `PAYLOAD_REJECTED_BY_BRIDGE_GATE`

Minimum error classes:

- `ContractError`
- `SemanticScopeError`
- `AuditIntegrityError`
- `ShadowIntegrityError`
- `M07BoundaryError`
- `BlockPropagationError`
- `CoverageIntegrityError`

## 9. M07-LPR-Specific Validation Rules

Level B may support M07-LPR only in documentary form.

Allowed M07-LPR payload semantics:

- support prepared
- support partial
- support degraded
- support blocked
- human completion required

Required M07-LPR constraints:

- no Level B payload may state or imply that M07 is closed, completed, or certified
- any M07-related payload must remain documentary
- if relevant, the payload must expose missing annexes, unresolved rinvii, omitted last comma issues, or incomplete documentary perimeter
- `human_completion_required = true` or equivalent documentary constraint is allowed only if it does not imply closure by Level B

Forbidden M07-LPR semantics:

- `M07 completed`
- `M07 closed`
- `M07 certified`
- `M07 sufficient`
- `full reading satisfied`

## 10. Audit Trail / SHADOW Validation Rules

Audit trail and SHADOW are mandatory across the bridge.

Validation rules:

1. every Level B payload crossing toward Level A must carry `audit_ref`
2. every Level B payload crossing toward Level A must carry `shadow_ref`
3. critical payloads must expose enough traceability to reconstruct:
   - modules activated
   - corpora activated
   - documents seen
   - citations produced or blocked
   - warnings
   - errors
   - blocks
4. audit trail and SHADOW must never be treated as substitutes for methodological reasoning
5. missing audit or SHADOW on a critical payload causes rejection or degradation according to bridge rules

## 11. Block Propagation Rules from Level B to Level A

If a block is opened in Level B, the payload must expose it explicitly.

Minimum propagation rules:

1. internal Level B blocks must appear in `blocks`
2. critical blocks must not be downgraded to warnings in transit
3. a payload with critical unresolved documentary defects must not be marked as clean
4. Level A must receive enough block information to resume governance under Metodo Cerda

Relevant block families include at least:

- scope violation
- citation incomplete
- vigenza uncertain
- cross-reference unresolved
- coverage inadequate
- audit incomplete
- M07 required
- output not opponible

## 12. Compliant / Non-Compliant Examples

### 12.1 Compliant Example

```json
{
  "request_id": "req_001",
  "case_id": "case_001",
  "trace_id": "trace_001",
  "payload_type": "document_package",
  "payload_status": "DOCUMENT_PACKAGE_READY_WITH_WARNINGS",
  "source_layer": "LEVEL_B",
  "producing_module": "BridgeReturnGate",
  "warnings": ["coverage partial on secondary corpus"],
  "errors": [],
  "blocks": [],
  "activated_corpora": ["tuel", "dlgs36"],
  "citations": ["D.Lgs. 267/2000, art. 49", "D.Lgs. 36/2023, art. 36"],
  "coverage_notes": ["secondary procedural support not activated"],
  "routing_notes": ["TUEL-first municipal procurement framing applied"],
  "documentary_confidence": "medium",
  "audit_ref": "audit_bridge_001",
  "shadow_ref": "shadow_bridge_001",
  "technical_trace": {
    "collections_seen": ["normattiva_tuel_267_2000", "normattiva_dlgs36_2023_articles"]
  }
}
```

Why compliant:

- required envelope present
- documentary payload only
- warnings exposed
- no forbidden conclusional semantics
- audit and SHADOW present

### 12.2 Non-Compliant Example

```json
{
  "request_id": "req_002",
  "case_id": "case_002",
  "trace_id": "trace_002",
  "payload_type": "document_package",
  "payload_status": "FINAL_DECISION_READY",
  "source_layer": "LEVEL_B",
  "producing_module": "Retriever",
  "warnings": [],
  "errors": [],
  "blocks": [],
  "legal_conclusion": "the act is valid",
  "m07_completed": true,
  "output_authorized": true,
  "audit_ref": "audit_bridge_002",
  "shadow_ref": "shadow_bridge_002"
}
```

Why non-compliant:

- forbidden status
- forbidden keys
- impermissible conclusional semantics
- impermissible M07 completion semantics
- impermissible authorization semantics

## 13. Minimum Acceptance Checklist

A Level B payload is minimally acceptable only if all checks below pass.

- envelope present
- all required keys present
- `warnings`, `errors`, `blocks` always present
- no forbidden key
- no forbidden semantic alias
- no conclusional `payload_status`
- no validative or authorizing semantics
- M07 support remains documentary only
- audit reference present
- SHADOW reference present
- blocks propagated when relevant
- unresolved critical issues not hidden
- payload remains support-only and non-conclusive

This document is a governance and validation artifact only.

It defines payload validation requirements and does not authorize any expansion of Level B powers.
