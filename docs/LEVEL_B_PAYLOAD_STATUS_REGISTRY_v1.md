# Level B Payload Status Registry v1

## 1. Purpose and Hierarchy of the Document

This document defines the controlled registry of allowed values for `payload_status` in Level B payloads crossing the bridge toward Level A.

Its purpose is to:

- eliminate semantic drift in Level B status values;
- prevent conclusional or validative wording from entering the bridge;
- make validation rules and test cases deterministic;
- align payload transport semantics with the governance perimeter of Metodo Cerda.

This document is subordinate to:

1. `METODO_CERDA_RAG_BRIDGE_SPEC_v1.md`
2. `METODO_CERDA_RAG_BRIDGE_ACCEPTANCE_MATRIX_v1.md`
3. `LEVEL_B_PAYLOAD_POLICY_v1.md`
4. `LEVEL_B_PAYLOAD_VALIDATION_RULES_v1.md`

If a conflict appears, the stricter rule prevails.

This document does not expand Level B powers.

It only defines the finite set of status values that Level B may emit in a compliant payload.

---

## 2. Registry Rule

`payload_status` is a controlled field.

It must use only values explicitly listed in this registry.

Any status value outside this registry is non-compliant and must be rejected or degraded according to bridge validation rules.

`payload_status` may describe only:

- documentary readiness;
- documentary degradation;
- documentary blockage;
- technical rejection;
- documentary M07 support state.

`payload_status` must never express:

- final legal conclusion;
- final applicability;
- final validation;
- final authorization;
- closure of PPAV;
- closure, completion, or certification of M07;
- readiness to sign or issue an act.

---

## 3. Closed Set of Allowed Values

The allowed registry is the following closed set.

### 3.1 General Documentary Package Statuses

- `DOCUMENT_PACKAGE_READY`
- `DOCUMENT_PACKAGE_READY_WITH_WARNINGS`
- `DOCUMENT_PACKAGE_DEGRADED`
- `DOCUMENT_PACKAGE_BLOCKED`
- `DOCUMENT_PACKAGE_REJECTED_BY_BRIDGE_GATE`

### 3.2 M07 Documentary Support Statuses

- `M07_SUPPORT_PREPARED`
- `M07_SUPPORT_PARTIAL`
- `M07_SUPPORT_DEGRADED`
- `M07_SUPPORT_BLOCKED`

No other `payload_status` values are allowed unless this registry is formally updated.

---

## 4. Semantic Meaning of Allowed Values

### 4.1 `DOCUMENT_PACKAGE_READY`

Meaning:

- the Level B payload contains a documentary support package;
- the package is technically valid for bridge crossing;
- no critical documentary defect is currently open inside the package.

This value does **not** mean:

- the case is legally resolved;
- the act is valid;
- the output is authorized;
- Level A may skip governance.

### 4.2 `DOCUMENT_PACKAGE_READY_WITH_WARNINGS`

Meaning:

- the documentary package is technically crossable;
- one or more non-critical warnings are present and explicitly exposed.

This value does **not** mean:

- the warnings are irrelevant;
- the package is fully complete;
- the case is decision-ready.

### 4.3 `DOCUMENT_PACKAGE_DEGRADED`

Meaning:

- the payload remains documentary and transportable;
- one or more significant documentary limitations are present;
- the limitations do not permit clean treatment as fully ready;
- Level A must resume governance with the degradation exposed.

Typical causes include:

- partial coverage;
- uncertain vigenza declared but not fully resolved;
- incomplete secondary corpus support;
- partially reconstructed cross-references.

### 4.4 `DOCUMENT_PACKAGE_BLOCKED`

Meaning:

- Level B encountered one or more explicit documentary blocks;
- the block condition is exposed in `blocks`;
- the package may still be returned for governance purposes, but not as a clean support package.

Typical causes include:

- unresolved rinvio;
- missing official source;
- critical coverage defect;
- M07 documentary perimeter not reconstructible;
- traceability failure that does not yet require full technical rejection.

### 4.5 `DOCUMENT_PACKAGE_REJECTED_BY_BRIDGE_GATE`

Meaning:

- the payload failed bridge validation requirements;
- the payload is not acceptable as a compliant Level B bridge payload.

Typical causes include:

- missing required envelope key;
- forbidden key present;
- forbidden semantic equivalent present;
- invalid `payload_status` value;
- missing mandatory audit or SHADOW reference on a critical payload.

### 4.6 `M07_SUPPORT_PREPARED`

Meaning:

- Level B produced documentary support relevant to M07-LPR;
- the support package is technically prepared for Level A consumption.

This value does **not** mean:

- M07 is completed;
- M07 is certified;
- reading obligations are exhausted.

### 4.7 `M07_SUPPORT_PARTIAL`

Meaning:

- Level B prepared only partial documentary support for M07-LPR;
- additional human completion and methodological work remain necessary.

### 4.8 `M07_SUPPORT_DEGRADED`

Meaning:

- M07 documentary support exists but contains significant limitations;
- the limitations are exposed and must be resumed by Level A.

### 4.9 `M07_SUPPORT_BLOCKED`

Meaning:

- M07 documentary support cannot be treated as usable without explicit block handling by Level A;
- the blocking condition must be exposed in `blocks` and reflected in related notes.

---

## 5. Effect Mapping

Each allowed value must map to an operational effect.

| payload_status | Bridge meaning | Minimum effect |
|---|---|---|
| `DOCUMENT_PACKAGE_READY` | clean documentary package | return to Level A as support-only |
| `DOCUMENT_PACKAGE_READY_WITH_WARNINGS` | transportable with exposed warnings | return to Level A with warnings |
| `DOCUMENT_PACKAGE_DEGRADED` | transportable but materially limited | return to Level A with degradation notes |
| `DOCUMENT_PACKAGE_BLOCKED` | explicit documentary block present | return to Level A with blocks |
| `DOCUMENT_PACKAGE_REJECTED_BY_BRIDGE_GATE` | payload contract failure | reject payload at bridge gate |
| `M07_SUPPORT_PREPARED` | usable documentary M07 support | return to Level A as M07 support only |
| `M07_SUPPORT_PARTIAL` | partial documentary M07 support | return to Level A with human completion required |
| `M07_SUPPORT_DEGRADED` | materially limited M07 support | return to Level A with degradation notes |
| `M07_SUPPORT_BLOCKED` | blocked M07 support | return to Level A with blocks |

No mapping may convert these statuses into:

- GO;
- NO_GO;
- final approval;
- final authorization;
- signability;
- full procedural closure.

---

## 6. Forbidden Status Values and Status Families

The following status values are forbidden.

### 6.1 Explicitly Forbidden Examples

- `FINAL_DECISION_READY`
- `FINAL_VALIDATION_READY`
- `OUTPUT_AUTHORIZED`
- `GO`
- `GO_FINAL`
- `NO_GO_FINAL`
- `ACT_READY_FOR_SIGNATURE`
- `READY_TO_SIGN`
- `READY_TO_ISSUE`
- `CASE_CLOSED`
- `PPAV_CLOSED`
- `M07_COMPLETED`
- `M07_CLOSED`
- `M07_CERTIFIED`
- `LAWFULNESS_VALIDATED`
- `FINAL_RULE_SELECTED`

### 6.2 Forbidden Semantic Families

Validation must reject status values that semantically express:

- final legal conclusion;
- final applicability judgment;
- final motivation;
- final validation;
- final authorization;
- final compliance pass;
- closure or completion of PPAV;
- closure, completion, sufficiency, or certification of M07;
- readiness for signature, issuance, or adoption.

Semantic equivalence prevails over literal naming.

---

## 7. Syntax and Formatting Constraints

`payload_status` must comply with all the following:

1. uppercase snake case only;
2. one scalar value only;
3. value must belong to the closed set in section 3;
4. no free-text sentence allowed in place of status;
5. no nested status object may replace the official scalar field;
6. no secondary hidden status field may carry forbidden semantics.

Examples of non-compliant formatting:

- `document package ready`
- `ReadyToSign`
- `{ "status": "DOCUMENT_PACKAGE_READY" }`
- `payload_ok_for_decision`

---

## 8. Coordination with Warnings / Errors / Blocks

`payload_status` must be coherent with `warnings`, `errors`, and `blocks`.

Minimum coherence rules:

1. `DOCUMENT_PACKAGE_READY` requires no critical block;
2. `DOCUMENT_PACKAGE_READY_WITH_WARNINGS` requires at least one warning and no critical block;
3. `DOCUMENT_PACKAGE_DEGRADED` requires at least one declared limitation in warnings, errors, or notes;
4. `DOCUMENT_PACKAGE_BLOCKED` requires at least one explicit block entry;
5. `DOCUMENT_PACKAGE_REJECTED_BY_BRIDGE_GATE` requires at least one rejection reason or fail code;
6. `M07_SUPPORT_BLOCKED` requires at least one explicit block entry;
7. `M07_SUPPORT_PARTIAL` or `M07_SUPPORT_DEGRADED` must not coexist with semantics implying full sufficiency.

A payload is non-compliant if status says “ready” while blocks indicate a critical unresolved documentary defect.

---

## 9. Coordination with Audit Trail and SHADOW

Every allowed `payload_status` value remains subordinate to traceability obligations.

Rules:

1. no status value cures a missing `audit_ref` or `shadow_ref`;
2. a payload with missing mandatory audit or SHADOW trace on a critical package must be rejected or degraded according to validation rules;
3. `DOCUMENT_PACKAGE_READY` must not be used to mask traceability defects;
4. M07 support statuses must remain traceable to the documentary support segment produced by Level B.

---

## 10. Coordination with M07-LPR

M07-related statuses are documentary support statuses only.

Therefore:

- they must never imply that reading is complete;
- they must never imply that the last-comma check is satisfied by Level B;
- they must never imply closure of the methodological gate;
- they must remain compatible with explicit human completion requirements.

Allowed M07 support statuses are limited to section 3.2.

Any other M07 status is forbidden.

---

## 11. Validation Rule

A payload must fail validation if:

1. `payload_status` is missing;
2. `payload_status` is not in the registry;
3. `payload_status` is semantically forbidden;
4. `payload_status` conflicts with `warnings`, `errors`, or `blocks`;
5. `payload_status` implies Level B closure, authorization, or validation;
6. `payload_status` implies M07 closure or certification.

Recommended fail codes:

- `PAYLOAD_STATUS_MISSING`
- `PAYLOAD_STATUS_NOT_REGISTERED`
- `PAYLOAD_STATUS_FORBIDDEN`
- `PAYLOAD_STATUS_SEMANTIC_SCOPE_VIOLATION`
- `PAYLOAD_STATUS_BLOCK_COHERENCE_FAILURE`
- `PAYLOAD_STATUS_M07_SCOPE_VIOLATION`

---

## 12. Compliant / Non-Compliant Examples

### 12.1 Compliant Examples

- `DOCUMENT_PACKAGE_READY`
- `DOCUMENT_PACKAGE_READY_WITH_WARNINGS`
- `DOCUMENT_PACKAGE_DEGRADED`
- `DOCUMENT_PACKAGE_BLOCKED`
- `DOCUMENT_PACKAGE_REJECTED_BY_BRIDGE_GATE`
- `M07_SUPPORT_PREPARED`
- `M07_SUPPORT_PARTIAL`
- `M07_SUPPORT_DEGRADED`
- `M07_SUPPORT_BLOCKED`

### 12.2 Non-Compliant Examples

- `FINAL_DECISION_READY`
- `OUTPUT_AUTHORIZED`
- `READY_TO_SIGN`
- `CASE_CLOSED`
- `GO_FINAL`
- `M07_COMPLETED`
- `M07_OK`
- `LAWFULNESS_VALIDATED`

---

## 13. Minimum Acceptance Checklist

A `payload_status` value is minimally acceptable only if all checks below pass.

- field present;
- scalar uppercase snake case;
- value in the closed registry;
- no forbidden literal status;
- no forbidden semantic equivalent;
- coherent with warnings/errors/blocks;
- does not imply final decision;
- does not imply validation;
- does not imply authorization;
- does not imply PPAV closure;
- does not imply M07 closure/completion/certification;
- remains support-only and documentary.

---

## 14. Non-Expansion Clause

This registry is a control artifact only.

It defines allowed Level B status values and their documentary meaning.

It does not authorize any expansion of Level B powers, and it cannot be interpreted as permitting conclusional, decisional, validative, or authorizing semantics inside the bridge.
