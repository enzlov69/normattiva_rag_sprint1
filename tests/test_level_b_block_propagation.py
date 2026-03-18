from __future__ import annotations

import json
from pathlib import Path

from validators.level_b_payload_validator import validate_level_b_payload

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "level_b_payloads"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_critical_block_requires_blocked_or_rejected_status():
    payload = load_json(FIXTURES / "pass" / "basic_success.json")
    payload["blocks"] = [
        {
            "block_code": "RAG_SCOPE_VIOLATION",
            "block_category": "scope",
            "block_severity": "CRITICAL",
            "origin_module": "B17_GuardrailEngine",
            "affected_object_type": "payload",
            "affected_object_id": "req_lb_001",
            "block_reason": "Campo decisorio rilevato.",
            "block_status": "OPEN",
            "release_condition": "Rimozione del campo vietato."
        }
    ]
    report = validate_level_b_payload(payload)
    codes = {finding.code for finding in report.findings}
    assert "CRITICAL_BLOCK_STATUS_MISMATCH" in codes
    assert not report.ok
