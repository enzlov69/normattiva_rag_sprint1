from __future__ import annotations

import json
from pathlib import Path

from validators.level_b_payload_validator import validate_level_b_payload

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "level_b_payloads" / "reject"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_m07_cannot_be_closed_by_level_b():
    payload = load_json(FIXTURES / "m07_closed_true.json")
    report = validate_level_b_payload(payload)
    codes = {finding.code for finding in report.findings}
    assert "M07_BOUNDARY_VIOLATION" in codes or "FORBIDDEN_LEVEL_B_FIELD" in codes
    assert "M07_SUPPORT_HUMAN_COMPLETION_REQUIRED" in codes
    assert not report.ok
