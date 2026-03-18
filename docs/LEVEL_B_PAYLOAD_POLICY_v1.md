# Level B Payload Policy v1

## 1. Purpose

This document defines the contractual payload policy for **Level B** within the Normattiva RAG / Metodo Cerda – PPAV architecture.

Its function is to translate the bridge governance rules into an explicit technical contract for:
- allowed payload families;
- required envelope fields;
- forbidden fields and forbidden semantics;
- error and block signalling;
- M07-LPR support payload boundaries;
- audit trail and SHADOW obligations;
- validation and rejection rules.

This document is subordinate to:
1. the founding v2 baseline;
2. the v2 master;
3. the architecture v2;
4. the data schema v2;
5. the API v2;
6. the bridge spec v1;
7. the bridge acceptance matrix v1.

If any interpretation conflict arises, the stricter rule that prevents Level B from assuming methodological, decisional, conclusional, or validative functions prevails.

---

## 2. Scope

This policy applies to every payload generated, returned, persisted, transformed, or relayed by Level B, including:
- documentary search responses;
- source lists and citation packs;
- coverage reports;
- cross-reference and rinvio reconstruction outputs;
- vigenza support outputs;
- M07 documentary support packs;
- block reports;
- audit-linked technical responses;
- SHADOW-linked technical traces.

It also applies to:
- API responses exposed by Level B;
- internal technical objects that cross the A↔B boundary;
- serialized JSON objects, maps, DTOs, records, envelopes, or equivalent structures.

---

## 3. Foundational Rule

Level B may only produce **documentary, technical, trace, and block-support payloads**.

Level B may not produce payloads that:
- conclude the case;
- validate an act;
- authorize an output;
- declare full legal applicability as final outcome;
- close M07-LPR;
- close PPAV governance flow;
- replace the RAC or other Level A outputs;
- express GO / NO-GO as final methodological judgment.

No payload design trick, alternative naming, semantic alias, nested key, derived flag, or inferred equivalent may be used to bypass this rule.

---

## 4. Contract Position Inside the Architecture

The payload policy enforces the separation that already governs the architecture:
- Level A governs reasoning, interpretation, motivation, conclusion, validation, and final release;
- Level B governs retrieval, structuring, tracing, signalling, and blocking of documentary support.

Therefore:
- Level A may call Level B for documentary support;
- Level B may answer only with support payloads;
- any Level B block must propagate to Level A;
- no Level B payload may authorize continuation toward an opposable output.

---

## 5. Required Envelope for Every Level B Response

Every Level B response crossing the bridge should expose an envelope containing, at minimum where relevant:
- `trace_id`
- `case_id` or equivalent case reference
- `payload_type`
- `payload_version`
- `source_layer = "B"`
- `generated_at`
- `documentary_status`
- `warnings`
- `errors`
- `blocks`
- `audit_ref`
- `shadow_ref`

Where not applicable to a specific technical response, omission must be justified by payload design and must not impair ex post reconstruction.

### 5.1 Minimum semantic meaning

- `trace_id`: technical trace continuity across the bridge.
- `case_id`: link to the governed case.
- `payload_type`: identifies the documentary object family.
- `payload_version`: prevents silent contract drift.
- `source_layer`: must identify the payload as Level B.
- `documentary_status`: support status only, never conclusional status.
- `warnings`: non-blocking issues relevant to use.
- `errors`: response defects or failed technical steps.
- `blocks`: blocking conditions opened by Level B.
- `audit_ref`: reference to audit trail event(s).
- `shadow_ref`: reference to SHADOW trace.

### 5.2 Mandatory explicit signalling

When relevant to the case or to the result of the traversal, the response must explicitly include:
- warnings;
- errors;
- blocks;
- technical trace.

Silent omission of a relevant critical issue is non-compliant.

---

## 6. Allowed Payload Families

Level B may expose only the following payload families, or stricter subtypes coherent with them:

### 6.1 Source discovery payloads
Allowed examples:
- activated corpora;
- source lists;
- source identifiers;
- source metadata;
- URI and official-source references.

### 6.2 Citation payloads
Allowed examples:
- article and comma references;
- citation completeness notes;
- official citation paths;
- identifier reconstruction outputs.

### 6.3 Coverage payloads
Allowed examples:
- documentary coverage notes;
- unresolved gaps;
- missing annex or missing source notices;
- partial completeness flags.

### 6.4 Cross-reference payloads
Allowed examples:
- rinvio maps;
- linked-reference lists;
- unresolved rinvio alerts;
- dependency chains among sources.

### 6.5 Vigenza support payloads
Allowed examples:
- documentary vigenza notes;
- uncertainty flags;
- official-source mismatch alerts.

### 6.6 M07 documentary support payloads
Allowed examples:
- evidence packs;
- structured documentary support for reading;
- article/comma mapping support;
- completeness support notes.

### 6.7 Audit and SHADOW linked payloads
Allowed examples:
- technical trace bundles;
- audit-linked event references;
- SHADOW support references.

### 6.8 Blocking payloads
Allowed examples:
- scope violation notices;
- citation insufficiency notices;
- unresolved essential rinvio notices;
- source-verification failure notices;
- coverage inadequacy notices.

---

## 7. Forbidden Payload Purposes

A Level B payload is forbidden if its purpose, direct or indirect, is to:
- close the case;
- validate the act;
- authorize release;
- produce dispositive content;
- resolve interpretive conflict as final answer;
- select the prevailing norm as final output;
- certify legal lawfulness/unlawfulness as conclusive result;
- replace the methodological judgment of Level A;
- close M07-LPR;
- close PPAV flow;
- create RAC as Level B output;
- emit final GO / NO-GO.

A payload is equally forbidden when such purpose is carried by:
- top-level fields;
- nested fields;
- computed booleans;
- status enums;
- alias keys;
- natural-language summary framed as final conclusion;
- hidden or metadata-carried conclusional semantics.

---

## 8. Forbidden Fields and Forbidden Semantics

The v2 schema already identifies the following fields as forbidden in Level B objects:
- `final_decision`
- `final_applicability`
- `legal_conclusion`
- `motivazione_finale`
- `output_authorized`
- `m07_closed`
- `ppav_closed`
- `go_finale`

The presence of such fields produces:
- invalidation of the record;
- rejection of the payload;
- opening or support of `RAG_SCOPE_VIOLATION`.

### 8.1 Semantic equivalents are also forbidden

The prohibition applies equally to semantic equivalents, including for example:
- `decision`
- `final_result`
- `applicable_final`
- `is_lawful`
- `validated`
- `approval_status`
- `authorization_status`
- `ready_for_signature`
- `ready_for_release`
- `m07_completed`
- `m07_certified`
- `workflow_closed`
- `final_go`
- `release_allowed`

### 8.2 Forbidden value semantics

Even where the key name appears neutral, the payload is forbidden if values imply final methodological effect, for example:
- `status = APPROVED`
- `status = VALIDATED`
- `status = GO`
- `status = M07_COMPLETE`
- `status = RELEASE_READY`
- `result = LAWFUL`
- `authorization = TRUE`

### 8.3 Forbidden natural-language formulations inside payloads

Free-text fields are non-compliant when framed as conclusional outputs, for example:
- “the act is lawful”;
- “the rule applicable is definitively X”;
- “M07 is complete”;
- “output may be signed”;
- “final authorization granted”.

Level B text may describe documentary support or documentary insufficiency, but not final methodological outcome.

---

## 9. Allowed Status Semantics

Allowed statuses in Level B must remain documentary or technical.

Examples of allowed status families:
- `DOCUMENTARY_OK`
- `DOCUMENTARY_PARTIAL`
- `DOCUMENTARY_INCOMPLETE`
- `BLOCKED`
- `REJECTED`
- `SOURCE_UNVERIFIED`
- `VIGENZA_UNCERTAIN`
- `RINVIO_UNRESOLVED`
- `M07_SUPPORT_READY`
- `M07_REQUIRED`
- `TRACE_INCOMPLETE`

These statuses must not be interpreted as:
- legal applicability;
- validation;
- final authorization;
- final GO / NO-GO.

---

## 10. M07-LPR Payload Boundary

Level B may support M07-LPR through documentary objects such as evidence packs, article maps, reference bundles, and support status.

Level B may not:
- declare M07 closed;
- declare M07 completed;
- declare M07 certified;
- substitute the reading governor;
- state that the presidio is sufficient as final methodological outcome.

### 10.1 Allowed M07 support object

An `M07EvidencePack` or equivalent support object may contain:
- support references;
- mapped articles/commi;
- completeness notes;
- documentary gaps;
- `m07_support_status`.

### 10.2 Forbidden M07 fields

Not admitted in Level B:
- `m07_closed = true`
- `m07_completed = true`
- `m07_certified = true`
- `m07_go = true`
- any semantically equivalent field.

### 10.3 Legal effect rule

RAG documentary support for M07-LPR does **not** equal closure, completion, or certification of M07.
M07 remains governed exclusively by Level A.

---

## 11. Audit Trail and SHADOW Rules

Audit trail and SHADOW are mandatory across the bridge.

Every critical Level B payload must be reconstructible ex post through:
- audit event reference(s);
- SHADOW trace reference(s);
- payload/type/version linkage;
- case/trace continuity.

### 11.1 Non-substitutive rule

Audit and SHADOW do not substitute:
- methodological control;
- human validation;
- Level A conclusion;
- Level A authorization.

### 11.2 Critical defect rule

Missing audit or missing SHADOW on critical transitions produces at least:
- degradation;
- or block;
- and explicit signalling to Level A.

---

## 12. Error Model and Block Taxonomy

Level B must use an explicit error and block model.

### 12.1 Minimum block causes

At least the following causes must be supported:
- source not official or not identifiable;
- insufficient metadata;
- incomplete citation;
- uncertain vigenza on essential point;
- unresolved essential rinvio;
- essential annex missing;
- orphan chunk;
- incomplete audit;
- forbidden field in Level B object;
- inadequate coverage on essential point;
- attempted scope overreach;
- attempted M07 closure from support layer.

### 12.2 Minimum named outcomes

Typical expected outcomes include:
- `REJECTED`
- `BLOCKED`
- `RAG_SCOPE_VIOLATION`
- `M07_REQUIRED`
- `SOURCE_UNVERIFIED`
- `TRACE_INCOMPLETE`
- `FINAL_AUTHORIZATION_DENIED` when a forbidden release effect is attempted across the bridge.

### 12.3 Propagation rule

A block opened in Level B must be propagated to Level A.

It may not be silently absorbed, downgraded, hidden, or auto-resolved without explicit governed handling.

---

## 13. Validation Rules

A Level B payload is valid only if all the following conditions are satisfied:
1. payload purpose is documentary/technical/block-support only;
2. no forbidden field is present;
3. no forbidden semantic equivalent is present;
4. no forbidden conclusional text is present;
5. audit reference is available where relevant;
6. SHADOW reference is available where relevant;
7. warnings/errors/blocks are explicit where relevant;
8. M07 support objects do not close or certify M07;
9. payload can be linked to case and trace context;
10. the response remains non-opposable and non-authorizing by design.

A Level B payload must be rejected when any critical validation rule fails.

---

## 14. Compliance Examples

### 14.1 Compliant payload sketch

```json
{
  "trace_id": "trc-001",
  "case_id": "case-001",
  "payload_type": "citation_pack",
  "payload_version": "1.0",
  "source_layer": "B",
  "documentary_status": "DOCUMENTARY_PARTIAL",
  "citations": ["D.Lgs. 267/2000, art. 176"],
  "warnings": ["vigenza da verificare su rinvio collegato"],
  "errors": [],
  "blocks": [],
  "audit_ref": "audit-778",
  "shadow_ref": "shadow-778"
}
```

### 14.2 Non-compliant payload sketch — forbidden decision

```json
{
  "trace_id": "trc-002",
  "source_layer": "B",
  "final_decision": "the act is lawful"
}
```

Expected outcome:
- `REJECTED`
- `RAG_SCOPE_VIOLATION`

### 14.3 Non-compliant payload sketch — forbidden M07 closure

```json
{
  "trace_id": "trc-003",
  "source_layer": "B",
  "payload_type": "m07_support",
  "m07_closed": true
}
```

Expected outcome:
- `REJECTED`
- no M07 closure in Level B
- block propagation to Level A

---

## 15. Minimum Acceptance Checklist

The payload policy is acceptable only if the implementation ensures that:
- Level B exposes no conclusional endpoints;
- Level B objects contain no decisional or validation fields;
- semantic aliases are also blocked;
- M07 support does not close M07;
- RAC cannot be created by Level B;
- audit and SHADOW are mandatory on critical crossings;
- blocks propagate from Level B to Level A;
- no payload authorizes an opposable output;
- no payload expresses final GO / NO-GO;
- regression tests reject forbidden fields and forbidden semantics.

---

## 16. Recommended Next Technical Effects

This policy should drive the next project artifacts:
1. payload validators for Level B objects;
2. API contract checks on bridge responses;
3. regression tests for forbidden semantic aliases;
4. JSON schema or equivalent contract definitions;
5. anti-scope-overreach test fixtures.

---

## 17. Final Rule

Level B payloads may retrieve, structure, trace, signal, and block.

They may not decide, validate, authorize, conclude, certify M07, close PPAV, or produce opposable output.

Any payload design that weakens this separation is non-compliant with the v2 project baseline.
