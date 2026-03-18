from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_REGISTRY = REPO_ROOT / "schemas" / "final_ab_runtime_anomaly_registry_v1.json"
SCHEMA_CANON = REPO_ROOT / "schemas" / "final_ab_runtime_severity_canon_v1.json"
SCHEMA_MATRIX = REPO_ROOT / "schemas" / "final_ab_runtime_propagation_matrix_v1.json"
GOLDEN_CASES = REPO_ROOT / "data" / "final_ab_runtime_golden_cases_v1.json"

REQUIRED_CODES = {
    "MISSING_REQUEST_ID",
    "MISSING_CASE_ID",
    "MISSING_TRACE_ID",
    "MISSING_API_VERSION",
    "MISSING_CALLER_MODULE",
    "MISSING_TARGET_MODULE",
    "RESPONSE_ENVELOPE_MISSING",
    "RESPONSE_STATUS_INVALID",
    "RESPONSE_TIMESTAMP_MISSING",
    "RESPONSE_PAYLOAD_MISSING",
    "RESPONSE_WARNINGS_INCONSISTENT",
    "RESPONSE_ERRORS_INCONSISTENT",
    "RESPONSE_BLOCKS_INCONSISTENT",
    "RESPONDER_MODULE_MISMATCH",
    "DOCUMENTARY_PACKET_MISSING",
    "DOCUMENTARY_PACKET_INCOMPLETE",
    "DOCUMENTARY_PACKET_TRACE_MISSING",
    "DOCUMENTARY_PACKET_INTEGRITY_BROKEN",
    "SOURCE_UNVERIFIED",
    "CITATION_INCOMPLETE",
    "VIGENZA_UNCERTAIN",
    "CROSSREF_UNRESOLVED",
    "COVERAGE_INADEQUATE",
    "AUDIT_INCOMPLETE",
    "SHADOW_INCOMPLETE",
    "RAG_SCOPE_VIOLATION",
    "M07_BOUNDARY_VIOLATION",
    "FORBIDDEN_FIELD_PRESENT",
    "OUTPUT_NOT_OPPONIBLE",
}

MANDATORY_FIELDS = {
    "anomaly_code",
    "title",
    "family",
    "description",
    "default_severity",
    "default_signal_class",
    "default_runtime_effect",
    "default_envelope_status",
    "propagate_to_level_a",
    "level_a_effect",
    "blocks_opponibility",
    "boundary_sensitive",
    "m07_sensitive",
    "documentary_integrity_sensitive",
    "traceability_sensitive",
    "release_allowed",
    "notes",
}


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _mk_row_key(family: str, severity: str, signal_class: str) -> Tuple[str, str, str]:
    return family, severity, signal_class


def validate() -> Dict[str, Any]:
    passed: List[str] = []
    failed: List[str] = []
    warns: List[str] = []
    coverage_stats: Dict[str, Any] = {}

    files = [SCHEMA_REGISTRY, SCHEMA_CANON, SCHEMA_MATRIX, GOLDEN_CASES]
    missing_files = [str(p) for p in files if not p.exists()]
    if missing_files:
        failed.append(f"Missing files: {', '.join(missing_files)}")
        return {
            "summary": "FAILED",
            "passed_checks": passed,
            "failed_checks": failed,
            "warnings": warns,
            "coverage_stats": coverage_stats,
            "exit_status": 1,
        }

    registry = _read_json(SCHEMA_REGISTRY)
    canon = _read_json(SCHEMA_CANON)
    matrix = _read_json(SCHEMA_MATRIX)
    golden = _read_json(GOLDEN_CASES)

    anomalies = registry.get("anomalies", [])
    rows = matrix.get("rows", [])

    codes = [a.get("anomaly_code") for a in anomalies]
    if len(codes) != len(set(codes)):
        failed.append("Duplicate anomaly_code values found in registry.")
    else:
        passed.append("Registry anomaly_code uniqueness verified.")

    missing_codes = sorted(REQUIRED_CODES - set(codes))
    if missing_codes:
        failed.append(f"Missing mandatory anomaly codes: {', '.join(missing_codes)}")
    else:
        passed.append("Mandatory anomaly code coverage verified.")

    missing_fields_by_code = []
    for item in anomalies:
        absent = sorted(MANDATORY_FIELDS - set(item.keys()))
        if absent:
            missing_fields_by_code.append(f"{item.get('anomaly_code')}: {', '.join(absent)}")
    if missing_fields_by_code:
        failed.append("Mandatory fields missing in registry entries: " + " | ".join(missing_fields_by_code))
    else:
        passed.append("Mandatory registry fields verified.")

    severities = {s["name"] for s in canon.get("severities", [])}
    signals = set(canon.get("signal_classes", []))
    runtime_effects = set(canon.get("runtime_effects", []))
    statuses = set(canon.get("envelope_statuses", []))
    level_effects = set(canon.get("level_a_effects", []))

    bad_values: List[str] = []
    for item in anomalies:
        code = item["anomaly_code"]
        if item["default_severity"] not in severities:
            bad_values.append(f"{code}: unknown severity {item['default_severity']}")
        if item["default_signal_class"] not in signals:
            bad_values.append(f"{code}: unknown signal_class {item['default_signal_class']}")
        if item["default_runtime_effect"] not in runtime_effects:
            bad_values.append(f"{code}: unknown runtime_effect {item['default_runtime_effect']}")
        if item["default_envelope_status"] not in statuses:
            bad_values.append(f"{code}: unknown envelope_status {item['default_envelope_status']}")
        if item["level_a_effect"] not in level_effects:
            bad_values.append(f"{code}: unknown level_a_effect {item['level_a_effect']}")
    if bad_values:
        failed.append("Registry to canon mismatch: " + " | ".join(bad_values))
    else:
        passed.append("Registry values align with severity canon.")

    matrix_keys = {
        _mk_row_key(r.get("family"), r.get("severity"), r.get("signal_class"))
        for r in rows
    }
    unresolved = []
    for item in anomalies:
        key = _mk_row_key(item["family"], item["default_severity"], item["default_signal_class"])
        if key not in matrix_keys:
            unresolved.append(f"{item['anomaly_code']} -> {key}")
    if unresolved:
        failed.append("Uncovered registry trajectories in matrix: " + " | ".join(unresolved))
    else:
        passed.append("Registry trajectories resolvable through propagation matrix.")

    bad_internal_blocks = [
        a["anomaly_code"]
        for a in anomalies
        if a.get("blocks_opponibility") is True and a.get("default_signal_class") == "INTERNAL"
    ]
    if bad_internal_blocks:
        failed.append("Invalid INTERNAL + blocks_opponibility=true: " + ", ".join(bad_internal_blocks))
    else:
        passed.append("No INTERNAL anomalies block opponibility.")

    restricted = {"BLOCKED", "REJECTED"}
    release_issues = []
    for a in anomalies:
        if a.get("default_envelope_status") in restricted and a.get("release_allowed") is True:
            notes = str(a.get("notes", ""))
            if "EXCEPTION:" not in notes:
                release_issues.append(a["anomaly_code"])
            else:
                warns.append(f"Release exception declared for {a['anomaly_code']}.")
    if release_issues:
        failed.append("release_allowed must be false for blocked/rejected anomalies: " + ", ".join(release_issues))
    else:
        passed.append("release_allowed coherence verified for blocked/rejected outcomes.")

    boundary_critical_nonblocking = [
        a["anomaly_code"]
        for a in anomalies
        if a.get("family") == "BOUNDARY"
        and a.get("default_severity") == "CRITICAL"
        and a.get("default_envelope_status") not in {"BLOCKED", "REJECTED"}
    ]
    if boundary_critical_nonblocking:
        failed.append("Boundary critical anomalies not blocked/rejected: " + ", ".join(boundary_critical_nonblocking))
    else:
        passed.append("Boundary critical anomalies are blocking/rejecting.")

    documentary_critical_internal = [
        a["anomaly_code"]
        for a in anomalies
        if a.get("family") in {"DOCUMENTARY", "TRACEABILITY"}
        and a.get("default_severity") == "CRITICAL"
        and a.get("default_signal_class") == "INTERNAL"
    ]
    if documentary_critical_internal:
        failed.append("Critical documentary/traceability anomalies cannot be INTERNAL: " + ", ".join(documentary_critical_internal))
    else:
        passed.append("Critical documentary/traceability anomalies are not INTERNAL.")

    traceability_critical_unpropagated = [
        a["anomaly_code"]
        for a in anomalies
        if a.get("family") == "TRACEABILITY"
        and a.get("default_severity") == "CRITICAL"
        and a.get("blocks_opponibility") is True
        and a.get("propagate_to_level_a") is False
    ]
    if traceability_critical_unpropagated:
        failed.append("Critical traceability anomalies affecting opponibility must propagate: " + ", ".join(traceability_critical_unpropagated))
    else:
        passed.append("Critical traceability propagation is coherent.")

    golden_cases = golden.get("golden_cases")
    if golden_cases is None:
        golden_cases = golden.get("cases", [])
    golden_req = {
        "case_id",
        "title",
        "anomaly_code",
        "expected_family",
        "expected_severity",
        "expected_signal_class",
        "expected_runtime_effect",
        "expected_envelope_status",
        "expected_propagate_to_level_a",
        "expected_level_a_effect",
        "expected_blocks_opponibility",
        "rationale",
    }
    case_issues = []
    if not golden_cases:
        case_issues.append("No golden cases found in fixture.")
    code_map = {a["anomaly_code"]: a for a in anomalies}
    for case in golden_cases:
        missing = sorted(golden_req - set(case.keys()))
        if missing:
            case_issues.append(f"{case.get('case_id')}: missing fields {', '.join(missing)}")
            continue
        code = case["anomaly_code"]
        anomaly = code_map.get(code)
        if anomaly is None:
            case_issues.append(f"{case['case_id']}: anomaly_code not found in registry ({code})")
            continue
        trajectory = _mk_row_key(case["expected_family"], case["expected_severity"], case["expected_signal_class"])
        if trajectory not in matrix_keys:
            case_issues.append(f"{case['case_id']}: matrix has no row for {trajectory}")

        expected_vs_registry = [
            ("expected_family", "family"),
            ("expected_severity", "default_severity"),
            ("expected_signal_class", "default_signal_class"),
            ("expected_runtime_effect", "default_runtime_effect"),
            ("expected_envelope_status", "default_envelope_status"),
            ("expected_propagate_to_level_a", "propagate_to_level_a"),
            ("expected_level_a_effect", "level_a_effect"),
            ("expected_blocks_opponibility", "blocks_opponibility"),
        ]
        for ckey, akey in expected_vs_registry:
            if case[ckey] != anomaly[akey]:
                case_issues.append(
                    f"{case['case_id']}: {ckey}={case[ckey]!r} != registry[{akey}]={anomaly[akey]!r}"
                )

    if case_issues:
        failed.append("Golden cases mismatch: " + " | ".join(case_issues))
    else:
        passed.append("Golden cases coherent with registry/canon/matrix.")

    coverage_stats = {
        "registry_anomalies": len(anomalies),
        "matrix_rows": len(rows),
        "golden_cases": len(golden_cases),
        "resolved_registry_trajectories": len(anomalies) - len(unresolved),
    }

    return {
        "summary": "PASSED" if not failed else "FAILED",
        "passed_checks": passed,
        "failed_checks": failed,
        "warnings": warns,
        "coverage_stats": coverage_stats,
        "exit_status": 0 if not failed else 1,
    }


def main() -> int:
    result = validate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return int(result["exit_status"])


if __name__ == "__main__":
    raise SystemExit(main())
