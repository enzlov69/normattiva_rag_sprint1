from __future__ import annotations

from typing import Any, Dict, List, Set


REQUEST_ALLOWED_FIELDS: Set[str] = {
    "request_id",
    "case_id",
    "source_level",
    "target_level",
    "request_kind",
    "source_phase",
    "documentary_scope",
    "expected_documentary_outputs",
    "trace",
}

REQUEST_FORBIDDEN_FIELDS: Set[str] = {
    "final_decision",
    "go_no_go",
    "firma_ready",
    "output_authorized",
    "final_opposability",
    "m07_closed",
    "m07_completed",
}

RESPONSE_ALLOWED_FIELDS: Set[str] = {
    "response_id",
    "request_id",
    "source_level",
    "target_level",
    "response_kind",
    "documentary_status",
    "documentary_packet",
    "citations",
    "coverage_report",
    "warnings",
    "errors",
    "blocks",
    "m07_documentary_support",
}

RESPONSE_FORBIDDEN_FIELDS: Set[str] = {
    "final_decision",
    "go_no_go",
    "firma_ready",
    "output_authorized",
    "final_opposability",
    "m07_closed",
    "m07_completed",
    "m07_approved",
    "layer_atto_firma_ready",
}


def build_valid_level_a_request() -> Dict[str, Any]:
    return {
        "request_id": "REQ-ABA-E2E-0001",
        "case_id": "CASE-ABA-E2E-0001",
        "source_level": "LEVEL_A",
        "target_level": "LEVEL_B",
        "request_kind": "DOCUMENTARY_SUPPORT_REQUEST",
        "source_phase": "S3",
        "documentary_scope": {
            "must_return_documentary_only": True,
            "level_b_is_non_decisional": True,
        },
        "expected_documentary_outputs": [
            "sources",
            "citations",
            "coverage_report",
            "warnings",
            "errors",
            "blocks",
        ],
        "trace": {
            "trace_id": "TRACE-ABA-E2E-0001",
        },
    }


def build_level_b_response(
    *,
    documentary_status: str = "DOCUMENTARY_OK",
    blocks: List[Dict[str, Any]] | None = None,
    coverage_status: str = "FULL",
    m07_completion_declared: bool = False,
) -> Dict[str, Any]:
    return {
        "response_id": "RESP-ABA-E2E-0001",
        "request_id": "REQ-ABA-E2E-0001",
        "source_level": "LEVEL_B",
        "target_level": "LEVEL_A",
        "response_kind": "DOCUMENTARY_SUPPORT_RESPONSE",
        "documentary_status": documentary_status,
        "documentary_packet": {
            "documentary_only": True,
            "contains_decision": False,
        },
        "citations": [
            {
                "source_type": "norma",
                "citation_text": "D.Lgs. 267/2000, art. 107",
                "official_source": True,
                "idonea": True,
            }
        ],
        "coverage_report": {
            "coverage_status": coverage_status,
        },
        "warnings": [],
        "errors": [],
        "blocks": blocks or [],
        "m07_documentary_support": {
            "support_provided": True,
            "documentary_only": True,
            "completion_declared": m07_completion_declared,
        },
    }


def validate_request_contract(payload: Dict[str, Any]) -> bool:
    actual_fields = set(payload.keys())
    if not actual_fields.issubset(REQUEST_ALLOWED_FIELDS):
        return False
    if not actual_fields.isdisjoint(REQUEST_FORBIDDEN_FIELDS):
        return False
    if payload["source_level"] != "LEVEL_A":
        return False
    if payload["target_level"] != "LEVEL_B":
        return False
    if payload["documentary_scope"]["must_return_documentary_only"] is not True:
        return False
    return True


def validate_response_contract(payload: Dict[str, Any]) -> bool:
    actual_fields = set(payload.keys())
    if not actual_fields.issubset(RESPONSE_ALLOWED_FIELDS):
        return False
    if not actual_fields.isdisjoint(RESPONSE_FORBIDDEN_FIELDS):
        return False
    if payload["source_level"] != "LEVEL_B":
        return False
    if payload["target_level"] != "LEVEL_A":
        return False
    if payload["documentary_packet"]["documentary_only"] is not True:
        return False
    if payload["documentary_packet"]["contains_decision"] is not False:
        return False
    return True


def evaluate_roundtrip(
    request_payload: Dict[str, Any],
    response_payload: Dict[str, Any],
) -> Dict[str, Any]:
    request_ok = validate_request_contract(request_payload)
    response_ok = validate_response_contract(response_payload)

    if not request_ok:
        return {
            "roundtrip_status": "INVALID_A_TO_B_REQUEST",
            "decided_by_level": "LEVEL_A",
            "can_emit_opposable_output": False,
            "can_emit_firma_ready": False,
        }

    if not response_ok:
        return {
            "roundtrip_status": "INVALID_B_TO_A_RESPONSE",
            "decided_by_level": "LEVEL_A",
            "can_emit_opposable_output": False,
            "can_emit_firma_ready": False,
        }

    block_codes = {block["code"] for block in response_payload.get("blocks", [])}
    has_critical_block = "CRITICAL_DOCUMENTARY_BLOCK" in block_codes
    has_m07_incomplete = "M07_DOCUMENTARY_INCOMPLETE" in block_codes
    has_degrading_block = bool(
        block_codes & {"COVERAGE_INSUFFICIENT", "CITATION_NOT_IDONEA", "VIGENCY_UNCERTAIN"}
    )
    m07_overreach = response_payload["m07_documentary_support"]["completion_declared"] is True
    full_coverage = response_payload["coverage_report"]["coverage_status"] == "FULL"

    if has_critical_block:
        return {
            "roundtrip_status": "BLOCKED_BY_LEVEL_B_CRITICAL_BLOCK",
            "decided_by_level": "LEVEL_A",
            "can_emit_opposable_output": False,
            "can_emit_firma_ready": False,
        }

    if has_m07_incomplete:
        return {
            "roundtrip_status": "M07_BLOCKED_AFTER_ROUNDTRIP",
            "decided_by_level": "LEVEL_A",
            "can_emit_opposable_output": False,
            "can_emit_firma_ready": False,
        }

    if m07_overreach:
        return {
            "roundtrip_status": "LEVEL_B_OVERREACH_ON_M07",
            "decided_by_level": "LEVEL_A",
            "can_emit_opposable_output": False,
            "can_emit_firma_ready": False,
        }

    if has_degrading_block or not full_coverage:
        return {
            "roundtrip_status": "DOCUMENTARY_SUPPORT_VALID_BUT_NOT_FULLY_OPPOSABLE",
            "decided_by_level": "LEVEL_A",
            "can_emit_opposable_output": False,
            "can_emit_firma_ready": False,
        }

    return {
        "roundtrip_status": "ROUNDTRIP_GREEN_UNDER_LEVEL_A_GOVERNANCE",
        "decided_by_level": "LEVEL_A",
        "can_emit_opposable_output": True,
        "can_emit_firma_ready": True,
    }


def test_green_roundtrip_a_to_b_to_a() -> None:
    request = build_valid_level_a_request()
    response = build_level_b_response(
        documentary_status="DOCUMENTARY_OK",
        blocks=[],
        coverage_status="FULL",
        m07_completion_declared=False,
    )

    result = evaluate_roundtrip(request, response)

    assert result["roundtrip_status"] == "ROUNDTRIP_GREEN_UNDER_LEVEL_A_GOVERNANCE"
    assert result["decided_by_level"] == "LEVEL_A"
    assert result["can_emit_opposable_output"] is True
    assert result["can_emit_firma_ready"] is True


def test_roundtrip_with_critical_block_is_blocked_in_level_a() -> None:
    request = build_valid_level_a_request()
    response = build_level_b_response(
        documentary_status="DOCUMENTARY_BLOCKED",
        blocks=[
            {
                "code": "CRITICAL_DOCUMENTARY_BLOCK",
                "severity": "HIGH",
                "documentary_only": True,
            }
        ],
    )

    result = evaluate_roundtrip(request, response)

    assert result["roundtrip_status"] == "BLOCKED_BY_LEVEL_B_CRITICAL_BLOCK"
    assert result["decided_by_level"] == "LEVEL_A"
    assert result["can_emit_opposable_output"] is False
    assert result["can_emit_firma_ready"] is False


def test_roundtrip_with_m07_incomplete_cannot_proceed_usefully() -> None:
    request = build_valid_level_a_request()
    response = build_level_b_response(
        documentary_status="DOCUMENTARY_BLOCKED",
        blocks=[
            {
                "code": "M07_DOCUMENTARY_INCOMPLETE",
                "severity": "HIGH",
                "documentary_only": True,
            }
        ],
    )

    result = evaluate_roundtrip(request, response)

    assert result["roundtrip_status"] == "M07_BLOCKED_AFTER_ROUNDTRIP"
    assert result["can_emit_opposable_output"] is False
    assert result["can_emit_firma_ready"] is False


def test_roundtrip_with_documentary_support_valid_but_not_fully_opposable() -> None:
    request = build_valid_level_a_request()
    response = build_level_b_response(
        documentary_status="DOCUMENTARY_WARNING",
        coverage_status="PARTIAL",
        blocks=[
            {
                "code": "COVERAGE_INSUFFICIENT",
                "severity": "MEDIUM",
                "documentary_only": True,
            }
        ],
    )

    result = evaluate_roundtrip(request, response)

    assert result["roundtrip_status"] == "DOCUMENTARY_SUPPORT_VALID_BUT_NOT_FULLY_OPPOSABLE"
    assert result["decided_by_level"] == "LEVEL_A"
    assert result["can_emit_opposable_output"] is False
    assert result["can_emit_firma_ready"] is False


def test_roundtrip_rejects_invalid_level_b_response_with_forbidden_field() -> None:
    request = build_valid_level_a_request()
    response = build_level_b_response()
    response["final_decision"] = "APPROVED"

    result = evaluate_roundtrip(request, response)

    assert result["roundtrip_status"] == "INVALID_B_TO_A_RESPONSE"
    assert result["decided_by_level"] == "LEVEL_A"
    assert result["can_emit_opposable_output"] is False
    assert result["can_emit_firma_ready"] is False


def test_roundtrip_rejects_invalid_level_a_request_with_decisional_field() -> None:
    request = build_valid_level_a_request()
    request["firma_ready"] = True
    response = build_level_b_response()

    result = evaluate_roundtrip(request, response)

    assert result["roundtrip_status"] == "INVALID_A_TO_B_REQUEST"
    assert result["decided_by_level"] == "LEVEL_A"
    assert result["can_emit_opposable_output"] is False
    assert result["can_emit_firma_ready"] is False


def test_roundtrip_detects_level_b_overreach_on_m07_completion() -> None:
    request = build_valid_level_a_request()
    response = build_level_b_response(
        documentary_status="DOCUMENTARY_OK",
        blocks=[],
        coverage_status="FULL",
        m07_completion_declared=True,
    )

    result = evaluate_roundtrip(request, response)

    assert result["roundtrip_status"] == "LEVEL_B_OVERREACH_ON_M07"
    assert result["decided_by_level"] == "LEVEL_A"
    assert result["can_emit_opposable_output"] is False
    assert result["can_emit_firma_ready"] is False