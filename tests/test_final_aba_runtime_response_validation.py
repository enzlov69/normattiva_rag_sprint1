from __future__ import annotations

from runtime.final_aba_runtime_handoff_service import validate_level_b_response


def build_valid_runtime_response() -> dict:
    return {
        "response_id": "RESP-RUNTIME-0001",
        "request_id": "REQ-RUNTIME-0001",
        "source_level": "LEVEL_B",
        "target_level": "LEVEL_A",
        "response_kind": "DOCUMENTARY_SUPPORT_RESPONSE",
        "documentary_status": "DOCUMENTARY_WARNING",
        "documentary_packet": {
            "documentary_only": True,
            "contains_decision": False,
        },
        "citations": [
            {
                "source_type": "norma",
                "citation_text": "D.Lgs. 267/2000, art. 107",
                "official_source": True,
            }
        ],
        "vigency_checks": [
            {
                "source": "D.Lgs. 267/2000",
                "vigency_status": "TO_VERIFY_IN_CONTEXT",
            }
        ],
        "cross_references": [
            {
                "source": "D.Lgs. 267/2000, art. 107",
                "linked_to": "L. 241/1990, art. 1",
            }
        ],
        "coverage_report": {
            "coverage_status": "PARTIAL",
        },
        "warnings": [
            "Coverage documentale parziale: da governare in Livello A",
        ],
        "errors": [],
        "blocks": [
            {
                "code": "COVERAGE_INSUFFICIENT",
                "severity": "MEDIUM",
                "documentary_only": True,
            }
        ],
        "m07_documentary_support": {
            "support_provided": True,
            "documentary_only": True,
            "completion_declared": False,
        },
        "audit": {
            "created_by": "LEVEL_B_RUNTIME",
            "internal_only": True,
        },
        "shadow": {
            "internal_use_only": True,
        },
    }


def test_valid_runtime_response_is_accepted() -> None:
    payload = build_valid_runtime_response()

    result = validate_level_b_response(payload)

    assert result.is_valid is True
    assert result.status == "RESPONSE_VALID"
    assert result.errors == []


def test_response_requires_level_b_as_source() -> None:
    payload = build_valid_runtime_response()
    payload["source_level"] = "LEVEL_A"

    result = validate_level_b_response(payload)

    assert result.is_valid is False
    assert "source_level must be LEVEL_B" in result.errors


def test_response_requires_level_a_as_target() -> None:
    payload = build_valid_runtime_response()
    payload["target_level"] = "LEVEL_B"

    result = validate_level_b_response(payload)

    assert result.is_valid is False
    assert "target_level must be LEVEL_A" in result.errors


def test_response_requires_documentary_support_response_kind() -> None:
    payload = build_valid_runtime_response()
    payload["response_kind"] = "FINAL_DECISION_RESPONSE"

    result = validate_level_b_response(payload)

    assert result.is_valid is False
    assert "response_kind must be DOCUMENTARY_SUPPORT_RESPONSE" in result.errors


def test_response_rejects_forbidden_decisional_field() -> None:
    payload = build_valid_runtime_response()
    payload["final_decision"] = "APPROVED"

    result = validate_level_b_response(payload)

    assert result.is_valid is False
    assert any("Forbidden response fields present" in error for error in result.errors)
    assert any("final_decision" in error for error in result.errors)


def test_response_rejects_missing_required_field() -> None:
    payload = build_valid_runtime_response()
    payload.pop("documentary_status")

    result = validate_level_b_response(payload)

    assert result.is_valid is False
    assert any("Missing required response fields" in error for error in result.errors)
    assert any("documentary_status" in error for error in result.errors)


def test_response_rejects_unexpected_field() -> None:
    payload = build_valid_runtime_response()
    payload["unexpected_field"] = "not_allowed"

    result = validate_level_b_response(payload)

    assert result.is_valid is False
    assert any("Unexpected response fields present" in error for error in result.errors)
    assert any("unexpected_field" in error for error in result.errors)


def test_response_requires_allowed_documentary_status() -> None:
    payload = build_valid_runtime_response()
    payload["documentary_status"] = "FINAL_OK"

    result = validate_level_b_response(payload)

    assert result.is_valid is False
    assert any("documentary_status must be one of" in error for error in result.errors)


def test_response_requires_documentary_packet_flags() -> None:
    payload = build_valid_runtime_response()
    payload["documentary_packet"]["documentary_only"] = False
    payload["documentary_packet"]["contains_decision"] = True

    result = validate_level_b_response(payload)

    assert result.is_valid is False
    assert "documentary_packet.documentary_only must be True" in result.errors
    assert "documentary_packet.contains_decision must be False" in result.errors


def test_response_requires_warnings_errors_blocks_as_lists() -> None:
    payload = build_valid_runtime_response()
    payload["warnings"] = "not-a-list"
    payload["errors"] = "not-a-list"
    payload["blocks"] = "not-a-list"

    result = validate_level_b_response(payload)

    assert result.is_valid is False
    assert "warnings must be a list" in result.errors
    assert "errors must be a list" in result.errors
    assert "blocks must be a list" in result.errors


def test_response_rejects_m07_completion_declared_by_level_b() -> None:
    payload = build_valid_runtime_response()
    payload["m07_documentary_support"]["completion_declared"] = True

    result = validate_level_b_response(payload)

    assert result.is_valid is False
    assert "Level B cannot declare m07 completion" in result.errors


def test_response_rejects_non_documentary_m07_support() -> None:
    payload = build_valid_runtime_response()
    payload["m07_documentary_support"]["documentary_only"] = False

    result = validate_level_b_response(payload)

    assert result.is_valid is False
    assert "m07_documentary_support.documentary_only must be True" in result.errors


def test_response_with_audit_internal_only_false_generates_warning() -> None:
    payload = build_valid_runtime_response()
    payload["audit"]["internal_only"] = False

    result = validate_level_b_response(payload)

    assert result.is_valid is True
    assert "audit.internal_only should be True" in result.warnings