from __future__ import annotations

import json
from pathlib import Path

from validators.level_b_payload_validator import validate_level_b_payload

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "level_b_payloads"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_degraded_fixture_remains_valid_support_only():
    payload = load_json(FIXTURES / "degrade" / "coverage_degraded.json")
    report = validate_level_b_payload(payload)
    assert report.ok, report.findings


def test_blocked_without_blocks_is_invalid():
    payload = load_json(FIXTURES / "reject" / "blocked_without_blocks.json")
    report = validate_level_b_payload(payload)
    codes = {finding.code for finding in report.findings}
    assert "BLOCKS_REQUIRED_FOR_BLOCKED_STATUS" in codes
    assert not report.ok
