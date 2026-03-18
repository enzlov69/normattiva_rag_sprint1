
from __future__ import annotations

import json
from pathlib import Path

import pytest

from validators.level_b_payload_validator import validate_level_b_payload
from validators.level_b_semantic_rules import load_fail_code_set

ROOT = Path(__file__).resolve().parent.parent
MATRIX_PATH = ROOT / "schemas" / "level_b_validation_traceability_matrix_v1.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


MATRIX = load_json(MATRIX_PATH)
ENTRIES = MATRIX["entries"]


@pytest.mark.parametrize("entry", ENTRIES, ids=[entry["rule_id"] for entry in ENTRIES])
def test_traceability_matrix_cases(entry):
    payload = load_json(ROOT / entry["fixture_path"])
    report = validate_level_b_payload(payload)
    assert report.ok is entry["expected_ok"], (entry["rule_id"], report.findings)

    if entry["expected_findings_any_of"]:
        codes = {finding.code for finding in report.findings}
        assert codes.intersection(entry["expected_findings_any_of"]), (entry["rule_id"], codes)


@pytest.mark.parametrize("entry", ENTRIES, ids=[entry["rule_id"] for entry in ENTRIES])
def test_traceability_matrix_points_to_existing_assets(entry):
    fixture_path = ROOT / entry["fixture_path"]
    test_module = ROOT / entry["test_module"]
    assert fixture_path.exists(), entry["fixture_path"]
    assert test_module.exists(), entry["test_module"]


@pytest.mark.parametrize("entry", ENTRIES, ids=[entry["rule_id"] for entry in ENTRIES])
def test_traceability_expected_findings_are_registered(entry):
    registered = load_fail_code_set()
    for code in entry["expected_findings_any_of"]:
        assert code in registered, (entry["rule_id"], code)
