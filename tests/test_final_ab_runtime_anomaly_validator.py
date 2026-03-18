import json
from pathlib import Path

from tools import final_ab_runtime_anomaly_validator as validator


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "schemas" / "final_ab_runtime_anomaly_registry_v1.json"
CANON_PATH = ROOT / "schemas" / "final_ab_runtime_severity_canon_v1.json"
MATRIX_PATH = ROOT / "schemas" / "final_ab_runtime_propagation_matrix_v1.json"
GOLDEN_PATH = ROOT / "data" / "final_ab_runtime_golden_cases_v1.json"
TMP_DIR = ROOT / "tests" / "_tmp_runtime_validator"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _tmp_file(name: str) -> Path:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    return TMP_DIR / name


def test_validator_passes_on_baseline():
    result = validator.validate()
    assert result["exit_status"] == 0
    assert result["summary"] == "PASSED"


def test_validator_fails_when_mandatory_code_missing(monkeypatch):
    registry = _load(REGISTRY_PATH)
    registry["anomalies"] = [
        a for a in registry["anomalies"] if a["anomaly_code"] != "MISSING_REQUEST_ID"
    ]
    reg_tmp = _tmp_file("registry_missing_code.json")
    _dump(reg_tmp, registry)

    monkeypatch.setattr(validator, "SCHEMA_REGISTRY", reg_tmp)
    monkeypatch.setattr(validator, "SCHEMA_CANON", CANON_PATH)
    monkeypatch.setattr(validator, "SCHEMA_MATRIX", MATRIX_PATH)
    monkeypatch.setattr(validator, "GOLDEN_CASES", GOLDEN_PATH)

    result = validator.validate()
    assert result["exit_status"] == 1
    assert any("Missing mandatory anomaly codes" in msg for msg in result["failed_checks"])
    reg_tmp.unlink(missing_ok=True)


def test_validator_fails_on_forbidden_downgrade(monkeypatch):
    registry = _load(REGISTRY_PATH)
    for anomaly in registry["anomalies"]:
        if anomaly["anomaly_code"] == "RAG_SCOPE_VIOLATION":
            anomaly["default_signal_class"] = "WARNING"
            anomaly["default_envelope_status"] = "SUCCESS_WITH_WARNINGS"
            anomaly["default_runtime_effect"] = "PROPAGATE_WARNING"
            break

    reg_tmp = _tmp_file("registry_forbidden_downgrade.json")
    _dump(reg_tmp, registry)

    monkeypatch.setattr(validator, "SCHEMA_REGISTRY", reg_tmp)
    monkeypatch.setattr(validator, "SCHEMA_CANON", CANON_PATH)
    monkeypatch.setattr(validator, "SCHEMA_MATRIX", MATRIX_PATH)
    monkeypatch.setattr(validator, "GOLDEN_CASES", GOLDEN_PATH)

    result = validator.validate()
    assert result["exit_status"] == 1
    assert any("Boundary critical anomalies not blocked/rejected" in msg for msg in result["failed_checks"])
    reg_tmp.unlink(missing_ok=True)


def test_validator_fails_when_golden_case_not_covered_by_matrix(monkeypatch):
    golden = _load(GOLDEN_PATH)
    cases = golden.get("golden_cases", golden.get("cases", []))
    cases[0]["expected_family"] = "NOT_A_FAMILY"
    gold_tmp = _tmp_file("golden_uncovered_matrix.json")
    _dump(gold_tmp, {**golden, "cases": cases})

    monkeypatch.setattr(validator, "SCHEMA_REGISTRY", REGISTRY_PATH)
    monkeypatch.setattr(validator, "SCHEMA_CANON", CANON_PATH)
    monkeypatch.setattr(validator, "SCHEMA_MATRIX", MATRIX_PATH)
    monkeypatch.setattr(validator, "GOLDEN_CASES", gold_tmp)

    result = validator.validate()
    assert result["exit_status"] == 1
    assert any("Golden cases mismatch" in msg for msg in result["failed_checks"])
    gold_tmp.unlink(missing_ok=True)
