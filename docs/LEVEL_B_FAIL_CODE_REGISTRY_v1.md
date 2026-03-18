# Level B Fail Code Registry v1

## 1. Purpose and Hierarchy of the Document

This document defines the controlled registry of fail codes used for Level B payload validation, bridge-gate rejection, degradation, and block propagation.

Its function is to ensure that compliance failures are:

- named consistently;
- classified consistently;
- mapped to deterministic operational effects;
- auditable across the bridge between Level B and Level A.

This document is subordinate to:

1. `METODO_CERDA_RAG_BRIDGE_SPEC_v1.md`
2. `METODO_CERDA_RAG_BRIDGE_ACCEPTANCE_MATRIX_v1.md`
3. `LEVEL_B_PAYLOAD_POLICY_v1.md`
4. `LEVEL_B_PAYLOAD_VALIDATION_RULES_v1.md`
5. `LEVEL_B_PAYLOAD_STATUS_REGISTRY_v1.md`

If a conflict appears, the stricter rule prevails.

This registry does not expand Level B powers.

It only standardizes failure signaling and operational consequences inside the controlled bridge.

---

## 2. Registry Principles

Every fail code must satisfy all of the following:

- unique identifier;
- stable semantic meaning;
- one primary error class;
- one primary activation condition;
- one primary default effect;
- explicit Level A propagation requirement;
- audit and SHADOW traceability.

A fail code must never be used to hide a conclusional act by Level B.

A fail code may signal:

- technical invalidity;
- documentary insufficiency;
- bridge-scope violation;
- missing traceability;
- M07 boundary violation;
- status-registry violation;
- propagation failure.

---

## 3. Error Classes

The minimum controlled error classes are:

- `ContractError`
- `SemanticScopeError`
- `AuditIntegrityError`
- `ShadowIntegrityError`
- `M07BoundaryError`
- `BlockPropagationError`
- `CoverageIntegrityError`
- `StatusRegistryError`
- `BridgeGateError`

Error classes may be extended only through a controlled update of this registry.

---

## 4. Operational Effects

Each fail code must map to one primary operational effect.

Allowed effects:

- `REJECT`
- `DEGRADE`
- `RETURN_WITH_BLOCKS`

### 4.1 Meaning of the Effects

**REJECT**

The payload does not validly cross the bridge.

Consequences:

- the payload is not acceptable as a valid support packet;
- Level A must receive the rejection condition;
- the failure must be audit-traceable;
- the bridge must not silently sanitize the issue.

**DEGRADE**

The payload may cross only as degraded documentary support.

Consequences:

- the defect remains exposed;
- the payload must not be represented as clean or complete;
- Level A must receive the degradation condition explicitly.

**RETURN_WITH_BLOCKS**

The payload may cross only with explicit blocks.

Consequences:

- blocks must be surfaced in the payload envelope;
- Level A must receive enough detail to resume governance;
- critical defects must not be downgraded to warnings.

---

## 5. Fail Code Registry

## 5.1 Contract and Envelope Failures

### `PAYLOAD_ENVELOPE_MISSING`

- **Class:** `ContractError`
- **Condition:** the minimum payload envelope is absent or structurally unusable.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** audit + SHADOW references to rejection event

### `PAYLOAD_REQUIRED_KEY_MISSING`

- **Class:** `ContractError`
- **Condition:** one or more required keys are absent.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** identify missing keys in technical trace

### `PAYLOAD_INVALID_SOURCE_LAYER`

- **Class:** `ContractError`
- **Condition:** `source_layer` is missing, malformed, or not consistent with Level B.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** trace emitted source inconsistency

### `PAYLOAD_INVALID_PAYLOAD_TYPE`

- **Class:** `ContractError`
- **Condition:** `payload_type` is absent, malformed, or outside the allowed technical families.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** trace invalid payload type

---

## 5.2 Forbidden Key and Semantic Scope Failures

### `PAYLOAD_FORBIDDEN_KEY`

- **Class:** `SemanticScopeError`
- **Condition:** one or more forbidden keys are present.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** identify forbidden key names

### `PAYLOAD_FORBIDDEN_SEMANTIC_ALIAS`

- **Class:** `SemanticScopeError`
- **Condition:** a semantic equivalent of a forbidden conclusional or validative meaning is present.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** identify semantic alias family

### `PAYLOAD_CONCLUSIONAL_ENDPOINT_EXPOSED`

- **Class:** `SemanticScopeError`
- **Condition:** Level B exposes a conclusional, decisional, validative, or authorizing endpoint or equivalent interface path.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record interface violation

### `PAYLOAD_AUTHORIZING_SEMANTICS`

- **Class:** `SemanticScopeError`
- **Condition:** the payload states or implies that an act/output is authorized, signable, issuable, or finally compliant.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record authorizing semantic family

---

## 5.3 Status Registry Failures

### `PAYLOAD_INVALID_STATUS`

- **Class:** `StatusRegistryError`
- **Condition:** `payload_status` is absent, malformed, or outside the approved status registry.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record raw status value

### `PAYLOAD_CONCLUSIONAL_STATUS`

- **Class:** `StatusRegistryError`
- **Condition:** `payload_status` contains conclusional, validative, authorizing, or “ready to sign/issue” semantics.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record forbidden status family

### `PAYLOAD_STATUS_EFFECT_MISMATCH`

- **Class:** `StatusRegistryError`
- **Condition:** the declared status conflicts with warnings/errors/blocks or with the documentary condition actually present.
- **Default effect:** `DEGRADE`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record mismatch details

---

## 5.4 M07-LPR Boundary Failures

### `PAYLOAD_M07_SCOPE_VIOLATION`

- **Class:** `M07BoundaryError`
- **Condition:** Level B crosses from documentary support into closure, completion, certification, or sufficiency semantics for M07.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record M07 semantic violation

### `PAYLOAD_M07_EVIDENCE_INCOMPLETE_UNDECLARED`

- **Class:** `M07BoundaryError`
- **Condition:** documentary incompleteness relevant to M07 exists but is not declared.
- **Default effect:** `RETURN_WITH_BLOCKS`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** expose missing documentary perimeter

### `PAYLOAD_M07_HUMAN_COMPLETION_MASKED`

- **Class:** `M07BoundaryError`
- **Condition:** human completion remains necessary but the payload masks this condition.
- **Default effect:** `RETURN_WITH_BLOCKS`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record human completion requirement

---

## 5.5 Audit and SHADOW Integrity Failures

### `PAYLOAD_AUDIT_MISSING`

- **Class:** `AuditIntegrityError`
- **Condition:** `audit_ref` is missing on a payload that crosses the bridge.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** rejection event must still be logged in audit infrastructure if possible

### `PAYLOAD_AUDIT_INCONSISTENT`

- **Class:** `AuditIntegrityError`
- **Condition:** `audit_ref` exists but is malformed, dangling, or inconsistent with the payload.
- **Default effect:** `RETURN_WITH_BLOCKS`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record inconsistency details

### `PAYLOAD_SHADOW_MISSING`

- **Class:** `ShadowIntegrityError`
- **Condition:** `shadow_ref` is missing on a payload that crosses the bridge.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** rejection event must still be logged if technically possible

### `PAYLOAD_SHADOW_INCONSISTENT`

- **Class:** `ShadowIntegrityError`
- **Condition:** `shadow_ref` exists but is malformed, dangling, or inconsistent with the payload.
- **Default effect:** `RETURN_WITH_BLOCKS`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record inconsistency details

---

## 5.6 Block Propagation Failures

### `PAYLOAD_BLOCK_NOT_PROPAGATED`

- **Class:** `BlockPropagationError`
- **Condition:** a Level B block exists internally but is absent from the `blocks` field.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record hidden block family

### `PAYLOAD_CRITICAL_BLOCK_DOWNGRADED`

- **Class:** `BlockPropagationError`
- **Condition:** a critical defect is downgraded to warning or omitted from block signaling.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** identify downgraded critical defect

### `PAYLOAD_BLOCK_CONTEXT_INSUFFICIENT`

- **Class:** `BlockPropagationError`
- **Condition:** a block is present but lacks enough information for Level A governance resumption.
- **Default effect:** `RETURN_WITH_BLOCKS`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** identify insufficient block context

---

## 5.7 Coverage, Vigenza, and Cross-Reference Failures

### `PAYLOAD_COVERAGE_UNDECLARED`

- **Class:** `CoverageIntegrityError`
- **Condition:** documentary coverage is partial, inadequate, or blocked, but this is not declared.
- **Default effect:** `RETURN_WITH_BLOCKS`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record undeclared coverage defect

### `PAYLOAD_VIGENZA_UNCERTAIN_UNDECLARED`

- **Class:** `CoverageIntegrityError`
- **Condition:** vigenza uncertainty exists but is not declared.
- **Default effect:** `RETURN_WITH_BLOCKS`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record undeclared vigenza issue

### `PAYLOAD_CROSSREF_UNRESOLVED_UNDECLARED`

- **Class:** `CoverageIntegrityError`
- **Condition:** unresolved rinvii or cross-references exist but are not declared.
- **Default effect:** `RETURN_WITH_BLOCKS`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record undeclared cross-reference issue

### `PAYLOAD_SOURCE_IDENTIFIABILITY_DEFECT`

- **Class:** `CoverageIntegrityError`
- **Condition:** sources or citations are not identifiable enough for controlled use.
- **Default effect:** `RETURN_WITH_BLOCKS`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record source identifiability defect

---

## 5.8 Bridge Gate Failures

### `PAYLOAD_REJECTED_BY_BRIDGE_GATE`

- **Class:** `BridgeGateError`
- **Condition:** the bridge gate rejects the payload after formal validation.
- **Default effect:** `REJECT`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record final gate rejection event

### `PAYLOAD_DEGRADED_BY_BRIDGE_GATE`

- **Class:** `BridgeGateError`
- **Condition:** the bridge gate permits crossing only as degraded documentary support.
- **Default effect:** `DEGRADE`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record degradation basis

### `PAYLOAD_RETURNED_WITH_BLOCKS_BY_BRIDGE_GATE`

- **Class:** `BridgeGateError`
- **Condition:** the bridge gate permits crossing only with explicit blocks.
- **Default effect:** `RETURN_WITH_BLOCKS`
- **Level A propagation:** mandatory
- **Minimum trace obligation:** record bridge-block basis

---

## 6. Effect Mapping Rules

The following rules must always apply:

1. `REJECT` prevails over `DEGRADE` and `RETURN_WITH_BLOCKS`.
2. `RETURN_WITH_BLOCKS` prevails over `DEGRADE` when unresolved critical documentary defects exist.
3. Multiple fail codes may coexist, but the most severe effect governs crossing.
4. No fail code may be silently absorbed.
5. Every fail code that affects bridge crossing must be represented in audit and SHADOW traces.

---

## 7. Level A Propagation Rules

Whenever a fail code is triggered, Level A must receive at least:

- the fail code;
- the error class;
- the operational effect;
- a concise technical reason;
- the relevant `trace_id`;
- the relevant `audit_ref`, where available;
- the relevant `shadow_ref`, where available.

Propagation must be explicit.

A fail code must never remain internal-only if it affects bridge crossing, M07 boundaries, audit integrity, SHADOW integrity, status integrity, or documentary sufficiency.

---

## 8. Compliant / Non-Compliant Handling Examples

### 8.1 Compliant Handling

A payload with partial coverage, explicit warning, explicit block, coherent status, valid audit, and valid SHADOW may cross with:

- no rejection;
- effect = `RETURN_WITH_BLOCKS`.

### 8.2 Non-Compliant Handling

A payload with `legal_conclusion`, `m07_completed = true`, and `payload_status = FINAL_DECISION_READY` must produce at least:

- `PAYLOAD_FORBIDDEN_KEY`
- `PAYLOAD_M07_SCOPE_VIOLATION`
- `PAYLOAD_CONCLUSIONAL_STATUS`
- resulting effect = `REJECT`

### 8.3 Degradation Handling

A payload with valid envelope but documentary confidence/status mismatch and missing secondary coverage declaration may produce:

- `PAYLOAD_STATUS_EFFECT_MISMATCH`
- `PAYLOAD_COVERAGE_UNDECLARED`
- resulting effect = `RETURN_WITH_BLOCKS` if the undeclared gap is critical;
- otherwise `DEGRADE`.

---

## 9. Minimum Acceptance Checklist

The registry is minimally respected only if all checks below pass.

- every fail code is uniquely named;
- every fail code has one primary class;
- every fail code has one primary default effect;
- reject/degrade/return-with-blocks semantics are stable;
- Level A propagation is explicit for bridge-relevant failures;
- audit and SHADOW obligations are preserved;
- M07 boundary violations are explicitly encoded;
- conclusional and validative semantics are explicitly rejectable;
- status-registry violations are explicitly encoded;
- coverage/vigenza/cross-reference masking is explicitly encoded.

---

## 10. Non-Production Statement

This document is a governance and validation artifact only.

It standardizes failure semantics for the controlled Level B bridge.

It does not authorize autonomous legal conclusion, validation, authorization, or closure by Level B.
