from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import final_ab_runtime_anomaly_validator as anomaly_validator

KEY_JSON_ARTIFACTS = [
    REPO_ROOT / "schemas" / "final_ab_runtime_anomaly_registry_v1.json",
    REPO_ROOT / "schemas" / "final_ab_runtime_severity_canon_v1.json",
    REPO_ROOT / "schemas" / "final_ab_runtime_propagation_matrix_v1.json",
    REPO_ROOT / "data" / "final_ab_runtime_golden_cases_v1.json",
]

JSON_ID_EXPECTATIONS = {
    REPO_ROOT / "schemas" / "final_ab_runtime_anomaly_registry_v1.json": ("schema_id", "final_ab_runtime_anomaly_registry_v1"),
    REPO_ROOT / "schemas" / "final_ab_runtime_severity_canon_v1.json": ("schema_id", "final_ab_runtime_severity_canon_v1"),
    REPO_ROOT / "schemas" / "final_ab_runtime_propagation_matrix_v1.json": ("schema_id", "final_ab_runtime_propagation_matrix_v1"),
    REPO_ROOT / "data" / "final_ab_runtime_golden_cases_v1.json": ("fixture_id", "final_ab_runtime_golden_cases_v1"),
}

ESSENTIAL_PHASE_DOCS = [
    REPO_ROOT / "docs" / "FINAL_AB_RUNTIME_ANOMALY_SEVERITY_PROPAGATION_SPEC_v1.md",
    REPO_ROOT / "docs" / "FINAL_AB_RUNTIME_GOLDEN_CASES_ACCEPTANCE_MATRIX_v1.md",
    REPO_ROOT / "docs" / "FINAL_AB_RUNTIME_ANOMALY_GOVERNANCE_LOCK_SPEC_v1.md",
]

REQUIRED_EXECUTABLES = [
    REPO_ROOT / "tools" / "final_ab_runtime_anomaly_validator.py",
]

REQUIRED_RELEASE_DOCS = [
    REPO_ROOT / "docs" / "FINAL_AB_RUNTIME_RELEASE_GATE_SPEC_v1.md",
    REPO_ROOT / "docs" / "FINAL_AB_RUNTIME_RELEASE_CHECKLIST_v1.md",
]

BOUNDARY_ARTIFACTS = [
    REPO_ROOT / "schemas" / "final_ab_m07_boundary_registry_v1.json",
]

PERTINENT_GOVERNANCE_DOCS = [
    REPO_ROOT / "docs" / "METODO_CERDA_RAG_BRIDGE_SPEC_v1.md",
    REPO_ROOT / "docs" / "LEVEL_A_LEVEL_B_FINAL_INTEGRATION_SPEC_v1.md",
    REPO_ROOT / "docs" / "FINAL_AB_RUNTIME_RELEASE_GATE_SPEC_v1.md",
    REPO_ROOT / "docs" / "FINAL_AB_RUNTIME_RELEASE_CHECKLIST_v1.md",
]

RELEASE_NAMING_DOCS = [
    REPO_ROOT / "docs" / "FINAL_AB_RUNTIME_RELEASE_GATE_SPEC_v1.md",
    REPO_ROOT / "docs" / "FINAL_AB_RUNTIME_RELEASE_CHECKLIST_v1.md",
]

AI_ASSISTED_TERMS = (
    "orchestrazione ai-assistita nel livello a",
    "ai assiste nel livello a",
)

HUMAN_APPROVAL_TERMS = (
    "approvazione umana finale obbligatoria",
    "l'uomo decide e firma",
)

LEVEL_B_NAMING_TERM = "rag normativo governato e federato"
M07_NON_CLOSURE_TERMS = (
    "supporto documentale a m07 non equivale a chiusura m07",
    "supporto documentale m07 non equivale a chiusura m07",
)


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def _relative(paths: Sequence[Path]) -> List[str]:
    return [str(path.relative_to(REPO_ROOT)).replace("\\", "/") for path in paths]


def _append_missing_check(paths: Sequence[Path], label: str, passed: List[str], failed: List[str]) -> bool:
    missing = [str(path.relative_to(REPO_ROOT)).replace("\\", "/") for path in paths if not path.exists()]
    if missing:
        failed.append(f"Missing {label}: {', '.join(missing)}")
        return False
    passed.append(f"{label.capitalize()} present.")
    return True


def _contains_any(text: str, terms: Sequence[str]) -> bool:
    return any(term in text for term in terms)


def validate() -> Dict[str, Any]:
    passed: List[str] = []
    failed: List[str] = []
    warnings: List[str] = []
    loaded_json: Dict[Path, Any] = {}

    checked_files = _relative(
        KEY_JSON_ARTIFACTS
        + ESSENTIAL_PHASE_DOCS
        + REQUIRED_EXECUTABLES
        + REQUIRED_RELEASE_DOCS
        + BOUNDARY_ARTIFACTS
    )

    artifacts_ok = _append_missing_check(KEY_JSON_ARTIFACTS, "key runtime artifacts", passed, failed)
    phase_docs_ok = _append_missing_check(ESSENTIAL_PHASE_DOCS, "phase 8-9 essential docs", passed, failed)
    validator_ok = _append_missing_check(REQUIRED_EXECUTABLES, "offline validator executables", passed, failed)
    release_docs_ok = _append_missing_check(REQUIRED_RELEASE_DOCS, "release gate docs", passed, failed)
    boundary_ok = _append_missing_check(BOUNDARY_ARTIFACTS, "boundary artifacts", passed, failed)

    if artifacts_ok:
        for path in KEY_JSON_ARTIFACTS:
            try:
                loaded_json[path] = _read_json(path)
            except json.JSONDecodeError as exc:
                failed.append(f"Invalid JSON in {path.relative_to(REPO_ROOT).as_posix()}: {exc}")

    if artifacts_ok and len(loaded_json) == len(KEY_JSON_ARTIFACTS):
        mismatch_messages: List[str] = []
        registry = loaded_json[KEY_JSON_ARTIFACTS[0]]
        canon = loaded_json[KEY_JSON_ARTIFACTS[1]]
        matrix = loaded_json[KEY_JSON_ARTIFACTS[2]]
        golden = loaded_json[KEY_JSON_ARTIFACTS[3]]

        for path, (field_name, expected_value) in JSON_ID_EXPECTATIONS.items():
            actual_value = loaded_json[path].get(field_name)
            if actual_value != expected_value:
                mismatch_messages.append(
                    f"{path.relative_to(REPO_ROOT).as_posix()} -> {field_name}={actual_value!r}, expected {expected_value!r}"
                )

        if mismatch_messages:
            failed.append("Baseline id mismatches: " + " | ".join(mismatch_messages))
        else:
            passed.append("Baseline artifact identifiers are coherent.")

        anomalies = registry.get("anomalies", [])
        severities = canon.get("severities", [])
        rows = matrix.get("rows", [])
        cases = golden.get("golden_cases", golden.get("cases", []))

        if anomalies and severities and rows and cases:
            passed.append("Phase 8-9 baseline payloads are populated.")
        else:
            failed.append("Phase 8-9 baseline payloads are incomplete or empty.")

        registry_codes = {item.get("anomaly_code") for item in anomalies}
        golden_codes = [item.get("anomaly_code") for item in cases]
        missing_codes = [code for code in golden_codes if code not in registry_codes]
        if missing_codes:
            failed.append(
                "Golden cases reference anomaly codes not present in registry: " + ", ".join(sorted(set(missing_codes)))
            )
        else:
            passed.append("Golden cases align with the anomaly registry code set.")

    if validator_ok and artifacts_ok:
        anomaly_result = anomaly_validator.validate()
        if int(anomaly_result.get("exit_status", 1)) != 0:
            failed.append("Offline anomaly validator failed on the current baseline.")
        else:
            passed.append("Offline anomaly validator passed on the current baseline.")

    governance_docs_ready = all(path.exists() for path in PERTINENT_GOVERNANCE_DOCS)
    naming_docs_ready = all(path.exists() for path in RELEASE_NAMING_DOCS)

    if governance_docs_ready:
        governance_text = "\n".join(_read_text(path) for path in PERTINENT_GOVERNANCE_DOCS)

        if _contains_any(governance_text, AI_ASSISTED_TERMS):
            passed.append("Level A AI-assisted orchestration governance is documented.")
        else:
            failed.append("Missing Level A AI-assisted orchestration governance in pertinent documents.")

        if _contains_any(governance_text, HUMAN_APPROVAL_TERMS):
            passed.append("Final human approval governance is documented.")
        else:
            failed.append("Missing final human approval requirement in pertinent documents.")

        if _contains_any(governance_text, M07_NON_CLOSURE_TERMS):
            passed.append("M07 support remains distinct from M07 closure in pertinent documents.")
        else:
            failed.append("Missing explicit M07 non-closure rule in pertinent documents.")
    else:
        failed.append("Missing pertinent governance documents required for release governance checks.")

    if naming_docs_ready:
        naming_text = "\n".join(_read_text(path) for path in RELEASE_NAMING_DOCS)
        if LEVEL_B_NAMING_TERM in naming_text:
            passed.append("Level B technical naming is coherent in release governance documents.")
        else:
            failed.append("Missing required Level B technical naming in release governance documents.")
    else:
        failed.append("Missing release governance documents required for Level B naming checks.")

    if artifacts_ok and phase_docs_ok and validator_ok and release_docs_ok and boundary_ok and not failed:
        passed.append("Release baseline asset set is minimally complete.")

    if failed:
        summary = "FAILED"
        release_readiness = "NOT_RELEASABLE"
        exit_status = 1
    elif warnings:
        summary = "PASSED_WITH_WARNINGS"
        release_readiness = "RELEASABLE_WITH_WARNINGS"
        exit_status = 0
    else:
        summary = "PASSED"
        release_readiness = "FULLY_RELEASABLE"
        exit_status = 0

    return {
        "summary": summary,
        "checked_files": checked_files,
        "passed_checks": passed,
        "failed_checks": failed,
        "warnings": warnings,
        "release_readiness": release_readiness,
        "exit_status": exit_status,
    }


def main() -> int:
    result = validate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return int(result["exit_status"])


if __name__ == "__main__":
    raise SystemExit(main())
