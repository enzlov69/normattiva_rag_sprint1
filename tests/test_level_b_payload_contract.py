from __future__ import annotations

import json
from pathlib import Path

from validators.level_b_payload_validator import validate_level_b_payload

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "level_b_payloads"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_pass_fixture_is_contract_valid():
    payload = load_json(FIXTURES / "pass" / "basic_success.json")
    report = validate_level_b_payload(payload)
    assert report.ok, report.findings


def test_reject_fixture_with_forbidden_field_fails():
    payload = load_json(FIXTURES / "reject" / "forbidden_final_decision.json")
    report = validate_level_b_payload(payload)
    codes = {finding.code for finding in report.findings}
    assert "FORBIDDEN_LEVEL_B_FIELD" in codes
    assert not report.ok
