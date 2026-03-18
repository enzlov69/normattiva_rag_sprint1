# Level B Governance Index v1

## 1. Purpose

This document is the governance index of the Level B control package within the Normattiva RAG / Metodo Cerda bridge.

Its purpose is to:

- identify the active governance documents of the Level B package;
- define their hierarchy and reading order;
- clarify the role of each document;
- prevent overlap, contradiction, or uncontrolled extension of Level B powers;
- provide a stable reference for future validation, audit, and implementation work.

This index is organizational and governance-oriented only.

It does not expand Level B powers, does not authorize new payload semantics, and does not modify any active rule already defined in the underlying documents.

## 2. Governance Principle

The whole Level B package is governed by the following architectural rule:

**Metodo Cerda governs reasoning, interpretation, motivation, conclusion, and validation.**

**Level B governs documentary retrieval, source activation, traceability, and support outputs only.**

No document listed in this index may be interpreted in a way that allows Level B to:

- conclude the case;
- validate the act;
- close M07-LPR;
- authorize an opponibile output;
- replace Level A governance.

## 3. Active Document Set

The active Level B governance package currently consists of the following documents:

1. `METODO_CERDA_RAG_BRIDGE_SPEC_v1.md`
2. `METODO_CERDA_RAG_BRIDGE_ACCEPTANCE_MATRIX_v1.md`
3. `LEVEL_B_PAYLOAD_POLICY_v1.md`
4. `LEVEL_B_PAYLOAD_VALIDATION_RULES_v1.md`
5. `LEVEL_B_PAYLOAD_TEST_CASES_v1.md`
6. `LEVEL_B_PAYLOAD_STATUS_REGISTRY_v1.md`
7. `LEVEL_B_FAIL_CODE_REGISTRY_v1.md`

## 4. Hierarchy and Prevalence

In case of overlap or apparent tension, the following precedence order applies.

### 4.1 First-level precedence

1. `METODO_CERDA_RAG_BRIDGE_SPEC_v1.md`
2. `METODO_CERDA_RAG_BRIDGE_ACCEPTANCE_MATRIX_v1.md`

### 4.2 Second-level prevalence

3. `LEVEL_B_PAYLOAD_POLICY_v1.md`
4. `LEVEL_B_PAYLOAD_VALIDATION_RULES_v1.md`

### 4.3 Third-level operational support

5. `LEVEL_B_PAYLOAD_STATUS_REGISTRY_v1.md`
6. `LEVEL_B_FAIL_CODE_REGISTRY_v1.md`
7. `LEVEL_B_PAYLOAD_TEST_CASES_v1.md`

### 4.4 Interpretation rule

If two documents appear to conflict:

- the stricter bridge-boundary rule prevails;
- the rule that more strongly preserves Level A authority prevails;
- the rule that more strongly blocks conclusional or validative semantics in Level B prevails.

## 5. Functional Role of Each Document

### 5.1 Bridge Spec

`METODO_CERDA_RAG_BRIDGE_SPEC_v1.md` defines:

- the controlled relationship between Level A and Level B;
- the subordinate role of Level B;
- the allowed and forbidden bridge behavior;
- the return-to-method gate;
- the boundary conditions on M07-LPR, audit trail, SHADOW, and block propagation.

This is the primary architectural rulebook of the bridge.

### 5.2 Bridge Acceptance Matrix

`METODO_CERDA_RAG_BRIDGE_ACCEPTANCE_MATRIX_v1.md` defines:

- the formal acceptance controls of the bridge;
- pass / reserve / fail logic;
- auto-fail conditions;
- bridge-level conformity checks.

This is the primary acceptance instrument of the bridge.

### 5.3 Payload Policy

`LEVEL_B_PAYLOAD_POLICY_v1.md` defines:

- the allowed documentary nature of Level B payloads;
- the permitted and forbidden payload semantics;
- the Level B output perimeter;
- the non-conclusional nature of payloads.

This is the primary policy document for Level B payload content.

### 5.4 Payload Validation Rules

`LEVEL_B_PAYLOAD_VALIDATION_RULES_v1.md` defines:

- mandatory payload envelope rules;
- required keys;
- optional allowed keys;
- forbidden keys;
- semantic alias rejection rules;
- rejection conditions;
- validation constraints for M07-LPR, audit, SHADOW, and block propagation.

This is the primary validation grammar of Level B payloads.

### 5.5 Payload Status Registry

`LEVEL_B_PAYLOAD_STATUS_REGISTRY_v1.md` defines:

- the closed set of allowed `payload_status` values;
- the meaning of each status;
- the operational effect associated with each status;
- forbidden status families and semantic drift controls.

This is the authoritative status vocabulary for Level B payloads.

### 5.6 Fail Code Registry

`LEVEL_B_FAIL_CODE_REGISTRY_v1.md` defines:

- fail codes;
- error classes;
- activation conditions;
- operational effects;
- propagation requirements toward Level A.

This is the authoritative failure and rejection vocabulary for Level B governance.

### 5.7 Payload Test Cases

`LEVEL_B_PAYLOAD_TEST_CASES_v1.md` defines:

- representative compliant cases;
- representative reject cases;
- degraded and blocked cases;
- validation-oriented scenarios derived from the policy and validation rules.

This is the documentary test catalog for the Level B package.

## 6. Recommended Reading Order

The recommended reading order is the following:

1. Bridge Spec
2. Bridge Acceptance Matrix
3. Payload Policy
4. Payload Validation Rules
5. Payload Status Registry
6. Fail Code Registry
7. Payload Test Cases

Reason:

- first understand the architecture;
- then understand acceptance;
- then understand payload perimeter;
- then understand validation grammar;
- then understand controlled status/failure vocabularies;
- then inspect concrete test scenarios.

## 7. Maintenance Rules

The Level B governance package must evolve under controlled conditions only.

Minimum maintenance rules:

1. no new document may expand Level B powers;
2. no new registry may introduce decisional, conclusional, or validative semantics;
3. no change to payload grammar may contradict the Bridge Spec;
4. no change to validation rules may weaken M07-LPR safeguards;
5. no change may remove audit or SHADOW obligations;
6. no change may suppress block propagation toward Level A;
7. any new document should be added to this index explicitly.

## 8. Triggers for Future Updates

This index should be updated when one of the following occurs:

- a new active Level B governance document is created;
- an existing Level B governance document is deprecated or replaced;
- the hierarchy or prevalence order changes;
- a new controlled registry is introduced;
- the bridge acceptance structure changes materially.

## 9. Non-Extension Clause

Nothing in this index may be used to justify:

- new Level B decisional powers;
- hidden payload semantics;
- implicit closure of M07-LPR;
- bypass of Level A governance;
- bypass of bridge validation or audit requirements.

This index organizes the package.

It does not authorize any enlargement of Level B scope.

## 10. Governance Closure Statement

With the documents listed in this index, the Level B governance package reaches a structured baseline composed of:

- architectural rule;
- acceptance rule;
- payload content policy;
- formal validation grammar;
- controlled status vocabulary;
- controlled fail vocabulary;
- documentary test catalog.

Any future technical implementation should remain subordinate to this package and may not override it.

