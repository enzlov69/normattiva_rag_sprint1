from __future__ import annotations

import json
from pathlib import Path

from validators.level_b_payload_validator import validate_level_b_payload

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "level_b_payloads" / "reject"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_audit_and_shadow_are_required():
    payload = load_json(FIXTURES / "missing_audit_shadow.json")
    report = validate_level_b_payload(payload)
    codes = {finding.code for finding in report.findings}
    assert "AUDIT_SHADOW_REQUIRED" in codes
    assert not report.ok
