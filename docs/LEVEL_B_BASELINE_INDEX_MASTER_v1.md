# LEVEL_B_BASELINE_INDEX_MASTER_v1

## 1. Purpose

This document defines the **Baseline Index Master v1** for the **Level B offline governance stack** of the Normattiva RAG / Metodo Cerda – PPAV project.

The Baseline Index Master is a **single high-level registry and execution map** for the consolidated Level B offline block. It does not introduce new runtime logic, does not modify the federated runner, and does not expose any conclusive or decisional semantics. Its role is to:

- enumerate the consolidated Level B checkpoints;
- map the key files of each checkpoint;
- define the ordered execution chain of the offline stack;
- map dependencies and protected baseline relationships;
- provide a single traceable reference for future audits, maintenance and onboarding.

## 2. Scope and non-scope

### In scope
- offline-only governance of Level B assets;
- checkpoint inventory;
- Git tag inventory;
- execution order inventory;
- file inventory;
- dependency inventory;
- consistency checks on the offline stack map.

### Out of scope
- federated runner modification;
- runtime integration;
- retrieval/router/corpus changes;
- bridge application logic;
- Level A / Metodo Cerda conclusive decisions;
- M07 closure;
- semantic validation of legal conclusions.

## 3. Architectural position

The Baseline Index Master is **descriptive, traceable and coordinative**.

It sits **above** the individual Level B offline packs as an index layer, but **below** the Metodo Cerda governance layer. It may:
- index;
- order;
- describe;
- cross-reference;
- signal structural incoherence.

It may not:
- authorize runtime promotion by itself;
- validate legal reasoning;
- close M07-LPR;
- replace the existing Golden / Gate / Runbook / Change Control controls.

## 4. Consolidated checkpoints indexed by this master

### LB-VAL
- Tag: `stable-level-b-validation-v1`
- Nature: initial Level B validation package

### LB-VAL2
- Tag: `stable-level-b-validation-v2`
- Nature: refined Level B validation kit and traceability matrix

### LB-GOLD
- Tag: `stable-level-b-golden-release-v1`
- Nature: golden baseline pack + offline release gate baseline checkpoint

### LB-RUN
- Tag: `stable-level-b-runbook-v1`
- Nature: runbook offline package

### LB-CC
- Tag: `stable-level-b-change-control-v1`
- Nature: change control pack

### LB-TRACE
- Tag: `stable-level-b-traceability-v1`
- Nature: traceability bundle

## 5. Ordered execution chain

The canonical execution order of the Level B offline stack is:

1. Validation suites
2. Golden baseline suite
3. Release gate offline
4. Runbook preflight
5. Change control precheck (only when a modification request exists)
6. Traceability bundle synthesis
7. Baseline Index Master synthesis

This order is mandatory for the master index and must not be inverted in future documentation without explicit governance update.

## 6. Dependency logic

### 6.1 Primary dependencies
- Golden baseline depends on the existence of the validation layer.
- Release gate depends on validation + golden baseline.
- Runbook depends on validation + golden baseline + release gate.
- Change control depends on the existence of protected baseline assets already consolidated.
- Traceability bundle depends on all previous packs.
- Baseline Index Master depends on all previous packs and tags.

### 6.2 Protected relationships
The following relationships are protected:
- Golden cases cannot be redefined without change control.
- Release gate manifest and runbook order must remain aligned.
- Traceability bundle must reflect actual committed checkpoints.
- Baseline Index Master must not reference future or missing checkpoints as consolidated.

## 7. Key file groups

### 7.1 Validation layer
- `docs/LEVEL_B_VALIDATION_TRACEABILITY_MATRIX_v1.md`
- `schemas/level_b_payload_schema_v1.json`
- `schemas/level_b_status_registry_v1.json`
- `schemas/level_b_fail_code_registry_v1.json`
- `schemas/level_b_validation_traceability_matrix_v1.json`
- `validators/level_b_result_model.py`
- `validators/level_b_semantic_rules.py`
- `validators/level_b_payload_validator.py`
- `tests/test_level_b_payload_contract.py`
- `tests/test_level_b_payload_semantics.py`
- `tests/test_level_b_m07_boundaries.py`
- `tests/test_level_b_audit_shadow.py`
- `tests/test_level_b_block_propagation.py`
- `tests/test_level_b_traceability_matrix.py`

### 7.2 Golden baseline and release gate
- `docs/LEVEL_B_GOLDEN_BASELINE_MATRIX_v1.md`
- `schemas/level_b_golden_baseline_registry_v1.json`
- `validators/level_b_golden_rules.py`
- `tests/test_level_b_golden_baseline.py`
- `docs/LEVEL_B_RELEASE_GATE_OFFLINE_v1.md`
- `schemas/level_b_release_gate_manifest_v1.json`
- `schemas/level_b_release_gate_report_schema_v1.json`
- `validators/level_b_release_gate_rules.py`
- `tools/run_level_b_release_gate_offline.py`
- `tests/test_level_b_release_gate_manifest.py`
- `tests/test_level_b_release_gate_rules.py`

### 7.3 Runbook
- `docs/LEVEL_B_RUNBOOK_OFFLINE_v1.md`
- `schemas/level_b_runbook_checklist_v1.json`
- `schemas/level_b_runbook_preflight_report_schema_v1.json`
- `validators/level_b_runbook_rules.py`
- `tools/run_level_b_runbook_preflight.py`
- `tests/test_level_b_runbook_checklist.py`
- `tests/test_level_b_runbook_rules.py`

### 7.4 Change control
- `docs/LEVEL_B_CHANGE_CONTROL_PACK_v1.md`
- `schemas/level_b_change_control_registry_v1.json`
- `schemas/level_b_change_request_schema_v1.json`
- `schemas/level_b_change_control_report_schema_v1.json`
- `validators/level_b_change_control_rules.py`
- `tools/run_level_b_change_control_precheck.py`
- `tests/test_level_b_change_control_registry.py`
- `tests/test_level_b_change_control_rules.py`
- `tests/test_level_b_change_control_runner.py`

### 7.5 Traceability bundle
- `docs/LEVEL_B_TRACEABILITY_BUNDLE_v1.md`
- `schemas/level_b_traceability_bundle_registry_v1.json`
- `schemas/level_b_traceability_bundle_report_schema_v1.json`
- `validators/level_b_traceability_bundle_rules.py`
- `tools/run_level_b_traceability_bundle.py`
- `tests/test_level_b_traceability_bundle_registry.py`
- `tests/test_level_b_traceability_bundle_rules.py`
- `tests/test_level_b_traceability_bundle_runner.py`

## 8. Index master control logic

The Baseline Index Master checks:

- that each checkpoint entry has a unique id;
- that checkpoint order is contiguous and explicit;
- that each indexed checkpoint has at least one Git tag;
- that key files are declared for every checkpoint;
- that the canonical order is coherent with dependency declarations;
- that no indexed checkpoint is marked consolidated if key files are missing;
- that no future checkpoint is referenced as already stable.

## 9. Decision vocabulary

The master runner may return only:

- `COMPLETE`: the indexed stack is structurally coherent and present;
- `HOLD`: the index exists but one or more indexed assets/tags/files are missing or the worktree is not clean;
- `ERROR`: the registry itself is malformed.

No other decisional status is allowed.

## 10. Governance rule

This master is an **index of the baseline**, not a substitute for the baseline packs.  
If conflict exists:
1. the pack-specific registry prevails in its own scope;
2. the protective gate/change-control logic prevails over the index;
3. the Metodo Cerda governance layer remains superior to the Level B index.

## 11. Recommended usage

The recommended usage order is:

1. keep the repository clean;
2. run validation/golden/gate/runbook/change-control/traceability checks as applicable;
3. run the baseline index master;
4. use the resulting report as the high-level offline snapshot of the consolidated Level B stack.

## 12. Commit and tag recommendation

Recommended commit message:
- `Add Level B baseline index master v1`

Recommended tag:
- `stable-level-b-baseline-index-v1`
