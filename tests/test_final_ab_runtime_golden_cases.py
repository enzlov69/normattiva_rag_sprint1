import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "schemas" / "final_ab_runtime_anomaly_registry_v1.json"
GOLDEN_PATH = ROOT / "data" / "final_ab_runtime_golden_cases_v1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _registry_index():
    registry = _load(REGISTRY_PATH)
    return {item["anomaly_code"]: item for item in registry["anomalies"]}


def _cases():
    payload = _load(GOLDEN_PATH)
    return payload.get("golden_cases", payload.get("cases", []))


def test_golden_cases_have_required_fields():
    required = {
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
    for case in _cases():
        assert required.issubset(case.keys())


def test_golden_case_codes_exist_in_registry():
    registry_codes = set(_registry_index().keys())
    for case in _cases():
        assert case["anomaly_code"] in registry_codes


def test_boundary_m07_cases_are_blocking_or_rejected():
    cases = _cases()
    for case in cases:
        if case["expected_family"] == "BOUNDARY" or "M07" in case["anomaly_code"]:
            assert case["expected_envelope_status"] in {"BLOCKED", "REJECTED"}
            assert case["expected_signal_class"] == "BLOCK"


def test_opponibility_blocking_cases_are_not_internal():
    for case in _cases():
        if case["expected_blocks_opponibility"] is True:
            assert case["expected_signal_class"] != "INTERNAL"


def test_blocked_or_rejected_cases_have_release_coherence():
    registry = _registry_index()
    for case in _cases():
        if case["expected_envelope_status"] not in {"BLOCKED", "REJECTED"}:
            continue
        anomaly = registry[case["anomaly_code"]]
        if anomaly["release_allowed"] is True:
            assert "EXCEPTION:" in anomaly["notes"]
        else:
            assert anomaly["release_allowed"] is False


def test_success_cases_have_non_contradictory_semantics():
    registry = _registry_index()
    for case in _cases():
        if case["expected_envelope_status"] not in {"SUCCESS", "SUCCESS_WITH_WARNINGS"}:
            continue
        assert case["expected_signal_class"] in {"INTERNAL", "WARNING"}
        anomaly = registry[case["anomaly_code"]]
        assert anomaly["default_envelope_status"] == case["expected_envelope_status"]
        assert anomaly["default_signal_class"] == case["expected_signal_class"]
