# Level B Payload Test Cases v1

## 1. Purpose and Hierarchy of the Document

This document defines the governance test cases for Level B payload validation within the controlled bridge between:

- Metodo Cerda / Level A
- Normattiva RAG / Level B

Its purpose is to make the validation layer operationally testable through a stable and reviewable catalogue of cases.

This document is subordinate to:

1. `METODO_CERDA_RAG_BRIDGE_SPEC_v1.md`
2. `METODO_CERDA_RAG_BRIDGE_ACCEPTANCE_MATRIX_v1.md`
3. `LEVEL_B_PAYLOAD_POLICY_v1.md`
4. `LEVEL_B_PAYLOAD_VALIDATION_RULES_v1.md`

If a conflict appears, the stricter rule prevails.

This document does not authorize any expansion of Level B powers.

It only converts the approved governance constraints into a repeatable test set.

---

## 2. Scope of the Test Catalogue

The catalogue covers at least the following control families:

- minimum payload envelope
- required keys
- optional allowed keys
- forbidden keys
- forbidden semantic aliases
- payload status compliance
- M07-LPR boundaries
- audit trail integrity
- SHADOW integrity
- block propagation
- documentary coverage integrity
- vigenza disclosure integrity
- cross-reference disclosure integrity
- support-only nature of the payload

The catalogue is designed for:

- document review
- manual validation
- future automated checks
- regression control after payload-schema updates

---

## 3. Expected Test Outcomes

Allowed test outcomes are the following:

- `PASS`
- `FAIL`
- `PASS_WITH_WARNINGS`
- `REJECT`
- `DEGRADE`

Operational meaning:

- `PASS` = payload complies with the tested rule
- `FAIL` = payload violates the tested rule
- `PASS_WITH_WARNINGS` = payload passes the specific rule but exposes non-critical issues
- `REJECT` = payload must not cross the bridge as a valid support output
- `DEGRADE` = payload may cross only as degraded documentary support, with explicit warnings or blocks

For hard-scope violations, the expected outcome is normally `REJECT`.

---

## 4. Test Case Template

Each test case should be read according to the following template:

- `Test ID`
- `Title`
- `Control family`
- `Scenario`
- `Input condition`
- `Expected outcome`
- `Expected fail code or status effect`
- `Notes`

---

## 5. Test Case Catalogue

### LBP-TC-001 — Valid minimum envelope

- **Control family:** minimum payload envelope
- **Scenario:** payload carries all required envelope fields
- **Input condition:** `request_id`, `case_id`, `trace_id`, `payload_type`, `payload_status`, `source_layer`, `producing_module`, `audit_ref`, `shadow_ref` all present and non-empty
- **Expected outcome:** `PASS`
- **Expected fail code or status effect:** none
- **Notes:** baseline acceptance case for bridge entry

### LBP-TC-002 — Missing `request_id`

- **Control family:** minimum payload envelope
- **Scenario:** one required identifier is missing
- **Input condition:** payload omits `request_id`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_REQUIRED_KEY_MISSING`
- **Notes:** hard failure

### LBP-TC-003 — Empty `trace_id`

- **Control family:** minimum payload envelope
- **Scenario:** required identifier exists but is empty or malformed
- **Input condition:** `trace_id = ""` or structurally invalid
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_REQUIRED_KEY_MISSING`
- **Notes:** traceability cannot be reconstructed

### LBP-TC-004 — Missing `warnings` key

- **Control family:** required keys
- **Scenario:** payload omits technical disclosure array
- **Input condition:** `warnings` absent
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_REQUIRED_KEY_MISSING`
- **Notes:** `warnings` must exist even if empty

### LBP-TC-005 — Missing `errors` key

- **Control family:** required keys
- **Scenario:** payload omits technical disclosure array
- **Input condition:** `errors` absent
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_REQUIRED_KEY_MISSING`
- **Notes:** `errors` must exist even if empty

### LBP-TC-006 — Missing `blocks` key

- **Control family:** required keys
- **Scenario:** payload omits technical disclosure array
- **Input condition:** `blocks` absent
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_REQUIRED_KEY_MISSING`
- **Notes:** `blocks` must exist even if empty

### LBP-TC-007 — Allowed documentary payload

- **Control family:** optional allowed keys
- **Scenario:** payload contains only allowed documentary and technical fields
- **Input condition:** payload includes `activated_corpora`, `citations`, `coverage_notes`, `routing_notes`, `technical_trace`
- **Expected outcome:** `PASS`
- **Expected fail code or status effect:** none
- **Notes:** positive case for documentary package

### LBP-TC-008 — Forbidden key `legal_conclusion`

- **Control family:** forbidden keys
- **Scenario:** payload carries explicit conclusional key
- **Input condition:** `legal_conclusion` present
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_FORBIDDEN_KEY`
- **Notes:** hard compliance failure

### LBP-TC-009 — Forbidden key `output_authorized`

- **Control family:** forbidden keys
- **Scenario:** payload carries authorizing key
- **Input condition:** `output_authorized = true`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_FORBIDDEN_KEY`
- **Notes:** hard compliance failure

### LBP-TC-010 — Forbidden key `m07_completed`

- **Control family:** forbidden keys / M07-LPR boundary
- **Scenario:** payload claims completion of M07
- **Input condition:** `m07_completed = true`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_M07_SCOPE_VIOLATION`
- **Notes:** hard scope violation

### LBP-TC-011 — Semantic alias `ready_for_signature`

- **Control family:** forbidden semantic aliases
- **Scenario:** payload avoids forbidden key list but uses equivalent conclusional meaning
- **Input condition:** `ready_for_signature = true`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_FORBIDDEN_SEMANTIC_ALIAS`
- **Notes:** semantic alias must be blocked

### LBP-TC-012 — Semantic alias nested in summary block

- **Control family:** forbidden semantic aliases
- **Scenario:** forbidden meaning is hidden in nested object
- **Input condition:** nested field such as `summary.final_rule_selected = "TUEL prevails conclusively"`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_FORBIDDEN_SEMANTIC_ALIAS`
- **Notes:** nested placement does not sanitize forbidden meaning

### LBP-TC-013 — Invalid conclusional `payload_status`

- **Control family:** payload status compliance
- **Scenario:** payload status itself carries forbidden semantics
- **Input condition:** `payload_status = "FINAL_DECISION_READY"`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_INVALID_STATUS`
- **Notes:** status labels must remain documentary and technical only

### LBP-TC-014 — Documentary payload with warnings

- **Control family:** payload status compliance
- **Scenario:** payload is valid but not clean
- **Input condition:** `payload_status = "DOCUMENT_PACKAGE_READY_WITH_WARNINGS"` and `warnings` non-empty
- **Expected outcome:** `PASS_WITH_WARNINGS`
- **Expected fail code or status effect:** none
- **Notes:** correct disclosure of partial but usable support

### LBP-TC-015 — Missing `audit_ref` on critical payload

- **Control family:** audit trail integrity
- **Scenario:** payload crosses the bridge without audit traceability
- **Input condition:** critical documentary payload omits `audit_ref`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_AUDIT_MISSING`
- **Notes:** critical payload cannot be accepted without audit reference

### LBP-TC-016 — Missing `shadow_ref` on critical payload

- **Control family:** SHADOW integrity
- **Scenario:** payload crosses the bridge without SHADOW traceability
- **Input condition:** critical documentary payload omits `shadow_ref`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_SHADOW_MISSING`
- **Notes:** critical payload cannot be accepted without SHADOW reference

### LBP-TC-017 — Block opened internally but not exposed

- **Control family:** block propagation
- **Scenario:** internal Level B defect exists but `blocks` is empty
- **Input condition:** internal retrieval has unresolved critical issue, yet payload returns `blocks = []`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_BLOCK_NOT_PROPAGATED`
- **Notes:** no silent masking allowed

### LBP-TC-018 — Critical issue downgraded to warning

- **Control family:** block propagation
- **Scenario:** critical defect appears only in warnings
- **Input condition:** unresolved citation or vigenza defect disclosed only in `warnings`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_BLOCK_NOT_PROPAGATED`
- **Notes:** critical defects cannot be softened in transit

### LBP-TC-019 — Coverage partial but declared

- **Control family:** documentary coverage integrity
- **Scenario:** documentary perimeter is incomplete but honestly declared
- **Input condition:** payload includes `coverage_status = "partial"` and explicit `coverage_notes`
- **Expected outcome:** `DEGRADE`
- **Expected fail code or status effect:** none
- **Notes:** degraded support is admissible only if transparent

### LBP-TC-020 — Coverage inadequate but undeclared

- **Control family:** documentary coverage integrity
- **Scenario:** incomplete coverage is hidden
- **Input condition:** secondary necessary corpus missing, no `coverage_notes`, no `blocks`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_COVERAGE_UNDECLARED`
- **Notes:** hidden insufficiency invalidates the payload

### LBP-TC-021 — Uncertain vigenza declared

- **Control family:** vigenza disclosure integrity
- **Scenario:** vigenza is not resolved but explicitly disclosed
- **Input condition:** payload includes `vigenza_status = "uncertain"` and related notes
- **Expected outcome:** `DEGRADE`
- **Expected fail code or status effect:** none
- **Notes:** transparent uncertainty may pass only as degraded support

### LBP-TC-022 — Uncertain vigenza undeclared

- **Control family:** vigenza disclosure integrity
- **Scenario:** vigenza issue exists but is omitted
- **Input condition:** known uncertainty not exposed in `vigenza_notes`, `warnings`, or `blocks`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_VIGENZA_UNCERTAIN_UNDECLARED`
- **Notes:** non-disclosure is unacceptable

### LBP-TC-023 — Unresolved cross-reference declared

- **Control family:** cross-reference disclosure integrity
- **Scenario:** rinvio remains unresolved but is exposed
- **Input condition:** `crossref_status = "unresolved"` and explicit notes present
- **Expected outcome:** `DEGRADE`
- **Expected fail code or status effect:** none
- **Notes:** degraded documentary support may still be returned

### LBP-TC-024 — Unresolved cross-reference undeclared

- **Control family:** cross-reference disclosure integrity
- **Scenario:** unresolved rinvio is hidden
- **Input condition:** cross-reference remains unresolved and payload presents itself as complete
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_CROSSREF_UNRESOLVED_UNDECLARED`
- **Notes:** silent gap invalidates bridge return

### LBP-TC-025 — M07 documentary support only

- **Control family:** M07-LPR boundary
- **Scenario:** payload supports M07 in documentary form only
- **Input condition:** `m07_support_status = "support_partial"`, missing annexes exposed, no closure semantics
- **Expected outcome:** `PASS_WITH_WARNINGS`
- **Expected fail code or status effect:** none
- **Notes:** correct M07 support behavior

### LBP-TC-026 — M07 certification semantics in human-readable field

- **Control family:** M07-LPR boundary / forbidden semantic aliases
- **Scenario:** forbidden meaning appears in summary text rather than key name
- **Input condition:** summary field says `M07 fully satisfied and certified`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_M07_SCOPE_VIOLATION`
- **Notes:** human-readable text is still subject to validation

### LBP-TC-027 — Source layer not identified as Level B

- **Control family:** required keys / envelope integrity
- **Scenario:** payload omits or misstates its origin layer
- **Input condition:** `source_layer = "LEVEL_A"` or missing
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_REQUIRED_KEY_MISSING`
- **Notes:** bridge validator must know provenance

### LBP-TC-028 — Clean payload with documentary trace

- **Control family:** support-only nature of payload
- **Scenario:** fully compliant documentary response with no defects
- **Input condition:** payload contains only allowed fields, empty warnings/errors/blocks, valid audit and SHADOW refs, documentary status
- **Expected outcome:** `PASS`
- **Expected fail code or status effect:** none
- **Notes:** ideal acceptance case

### LBP-TC-029 — Routing notes imply final legal resolution

- **Control family:** support-only nature of payload / forbidden semantics
- **Scenario:** routing notes exceed documentary scope
- **Input condition:** `routing_notes = ["TUEL definitively governs the case and resolves applicability"]`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_FORBIDDEN_SEMANTIC_ALIAS`
- **Notes:** routing may orient, not conclude

### LBP-TC-030 — Coverage notes imply final legal resolution

- **Control family:** support-only nature of payload / forbidden semantics
- **Scenario:** coverage commentary becomes legal conclusion
- **Input condition:** `coverage_notes = ["sources are sufficient to authorize the act"]`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_FORBIDDEN_SEMANTIC_ALIAS`
- **Notes:** documentary sufficiency must not become authorization

### LBP-TC-031 — Forbidden semantic alias inside enum

- **Control family:** forbidden semantic aliases
- **Scenario:** equivalent finality is hidden in a coded value
- **Input condition:** `decision_state = "LAWFULNESS_VALIDATED"`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_FORBIDDEN_SEMANTIC_ALIAS`
- **Notes:** enums are not exempt from semantic control

### LBP-TC-032 — Documentary confidence properly bounded

- **Control family:** optional allowed keys / support-only nature of payload
- **Scenario:** payload uses confidence field correctly
- **Input condition:** `documentary_confidence = "medium"` and no reference to legal outcome
- **Expected outcome:** `PASS`
- **Expected fail code or status effect:** none
- **Notes:** confidence may concern documentary sufficiency only

### LBP-TC-033 — Documentary confidence misused as legal confidence

- **Control family:** support-only nature of payload / forbidden semantics
- **Scenario:** confidence field becomes conclusive legal assessment
- **Input condition:** `documentary_confidence = "high act lawfulness confirmed"`
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_FORBIDDEN_SEMANTIC_ALIAS`
- **Notes:** confidence must remain technical-documentary

### LBP-TC-034 — Technical trace present when blocks exist

- **Control family:** audit trail / SHADOW / block propagation
- **Scenario:** blocked payload exposes enough technical trace for governance resumption
- **Input condition:** `blocks` non-empty and `technical_trace` shows relevant modules, corpora, and blocked citations
- **Expected outcome:** `DEGRADE`
- **Expected fail code or status effect:** none
- **Notes:** degraded but usable support for Level A resumption

### LBP-TC-035 — Critical blocked payload without technical trace

- **Control family:** audit trail / SHADOW / block propagation
- **Scenario:** payload discloses a critical block but does not permit reconstruction
- **Input condition:** `blocks` non-empty, yet no usable `technical_trace` and no adequate audit linkage
- **Expected outcome:** `REJECT`
- **Expected fail code or status effect:** `PAYLOAD_REJECTED_BY_BRIDGE_GATE`
- **Notes:** bridge return is not sufficiently auditable

---

## 6. Minimum Regression Set

The following cases should always be included in any minimum regression cycle:

- `LBP-TC-001`
- `LBP-TC-004`
- `LBP-TC-008`
- `LBP-TC-010`
- `LBP-TC-013`
- `LBP-TC-015`
- `LBP-TC-017`
- `LBP-TC-020`
- `LBP-TC-022`
- `LBP-TC-024`
- `LBP-TC-026`
- `LBP-TC-029`

This minimum regression set protects the most sensitive boundaries of the bridge.

---

## 7. Minimum Acceptance Condition for the Catalogue

The Level B validation layer is minimally acceptable only if:

- all hard-failure cases above are rejected as expected
- degraded-support cases are not promoted to clean pass
- documentary-support cases do not drift into conclusional semantics
- M07 support remains documentary only
- audit trail and SHADOW remain mandatory
- critical blocks are always propagated to Level A

---

## 8. Non-Production Statement

This document is a governance and testing artifact only.

It defines the approved catalogue of validation test cases and does not by itself implement executable test logic.
