from pathlib import Path

from tools import final_ab_runtime_baseline_verifier as verifier


ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = ROOT / "tests" / "_tmp_runtime_baseline_verifier"


def _tmp_file(name: str, content: str) -> Path:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    path = TMP_DIR / name
    path.write_text(content, encoding="utf-8")
    return path


def test_verifier_reads_expected_files():
    result = verifier.validate()
    assert result["exit_status"] == 0
    assert "schemas/final_ab_runtime_anomaly_registry_v1.json" in result["checked_files"]
    assert "data/final_ab_runtime_golden_cases_v1.json" in result["checked_files"]


def test_verifier_returns_positive_result_on_current_baseline():
    result = verifier.validate()
    assert result["summary"] == "PASSED"
    assert result["release_readiness"] == "FULLY_RELEASABLE"
    assert result["exit_status"] == 0


def test_verifier_fails_when_essential_artifact_is_missing(monkeypatch):
    missing_artifact = TMP_DIR / "missing_registry.json"
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(verifier, "KEY_JSON_ARTIFACTS", [missing_artifact, *verifier.KEY_JSON_ARTIFACTS[1:]])

    result = verifier.validate()
    assert result["exit_status"] == 1
    assert result["release_readiness"] == "NOT_RELEASABLE"
    assert any("Missing key runtime artifacts" in item for item in result["failed_checks"])


def test_verifier_reports_not_ready_when_spec_or_validator_is_missing(monkeypatch):
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    missing_spec = TMP_DIR / "missing_spec.md"
    missing_validator = TMP_DIR / "missing_validator.py"
    monkeypatch.setattr(verifier, "ESSENTIAL_PHASE_DOCS", [missing_spec])
    monkeypatch.setattr(verifier, "REQUIRED_EXECUTABLES", [missing_validator])

    result = verifier.validate()
    assert result["exit_status"] == 1
    assert result["release_readiness"] == "NOT_RELEASABLE"
    assert any("Missing phase 8-9 essential docs" in item for item in result["failed_checks"])
    assert any("Missing offline validator executables" in item for item in result["failed_checks"])


def test_verifier_report_contains_minimum_fields():
    result = verifier.validate()
    expected = {
        "summary",
        "checked_files",
        "passed_checks",
        "failed_checks",
        "warnings",
        "release_readiness",
        "exit_status",
    }
    assert expected.issubset(result.keys())


def test_verifier_detects_missing_governance_presidia(monkeypatch):
    governance_doc = _tmp_file(
        "governance_missing_presidia.md",
        "# temp\nQuesto file non contiene i presidi richiesti.\n",
    )
    naming_doc = _tmp_file(
        "naming_missing.md",
        "# temp\nNaming non coerente.\n",
    )

    monkeypatch.setattr(verifier, "PERTINENT_GOVERNANCE_DOCS", [governance_doc])
    monkeypatch.setattr(verifier, "RELEASE_NAMING_DOCS", [naming_doc])

    result = verifier.validate()
    assert result["exit_status"] == 1
    assert any("AI-assisted orchestration" in item for item in result["failed_checks"])
    assert any("final human approval" in item for item in result["failed_checks"])
    assert any("Level B technical naming" in item for item in result["failed_checks"])
