from __future__ import annotations

from runtime.final_aba_runtime_handoff_service import perform_runtime_roundtrip


def build_valid_runtime_request() -> dict:
    return {
        "request_id": "REQ-RUNTIME-E2E-0001",
        "case_id": "CASE-RUNTIME-E2E-0001",
        "trace_id": "TRACE-RUNTIME-E2E-0001",
        "source_level": "LEVEL_A",
        "target_level": "LEVEL_B",
        "request_kind": "DOCUMENTARY_SUPPORT_REQUEST",
        "source_phase": "S3",
        "documentary_scope": {
            "must_return_documentary_only": True,
            "level_b_is_non_decisional": True,
            "objective": "Roundtrip runtime reale controllato",
        },
        "expected_documentary_outputs": [
            "sources",
            "citations",
            "vigency_checks",
            "cross_references",
            "coverage_report",
            "warnings",
            "errors",
            "blocks",
        ],
        "active_presidia": [
            "OP_ANTI_ALLUCINAZIONI_NORMATIVE",
            "OP_DOPPIA_LENTE_RATIO",
            "OP_COT++",
        ],
        "audit": {
            "created_by": "LEVEL_A_RUNTIME",
            "internal_only": True,
        },
        "shadow": {
            "internal_use_only": True,
        },
    }


def build_valid_runtime_response(
    *,
    documentary_status: str = "DOCUMENTARY_OK",
    blocks: list[dict] | None = None,
    internal_only_audit: bool = True,
    completion_declared: bool = False,
) -> dict:
    return {
        "response_id": "RESP-RUNTIME-E2E-0001",
        "request_id": "REQ-RUNTIME-E2E-0001",
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
            }
        ],
        "vigency_checks": [],
        "cross_references": [],
        "coverage_report": {
            "coverage_status": "FULL",
        },
        "warnings": [],
        "errors": [],
        "blocks": blocks or [],
        "m07_documentary_support": {
            "support_provided": True,
            "documentary_only": True,
            "completion_declared": completion_declared,
        },
        "audit": {
            "created_by": "LEVEL_B_RUNTIME",
            "internal_only": internal_only_audit,
        },
        "shadow": {
            "internal_use_only": True,
        },
    }


def test_green_runtime_roundtrip() -> None:
    request = build_valid_runtime_request()

    def invoker(payload: dict) -> dict:
        assert payload["request_id"] == request["request_id"]
        return build_valid_runtime_response(documentary_status="DOCUMENTARY_OK", blocks=[])

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "ROUNDTRIP_GREEN"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is True
    assert result["internal_envelope"] is not None
    assert result["internal_envelope"]["runtime_status"] == "ROUNDTRIP_GREEN"
    assert result["internal_envelope"]["can_emit_go_no_go"] is False
    assert result["internal_envelope"]["can_emit_firma_ready"] is False
    assert result["internal_envelope"]["can_authorize_output"] is False


def test_request_invalid_stops_roundtrip_before_invoker() -> None:
    request = build_valid_runtime_request()
    request["firma_ready"] = True

    def invoker(_: dict) -> dict:
        raise AssertionError("L'invoker non doveva essere chiamato con request invalida")

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "REQUEST_INVALID"
    assert result["request_validation"]["is_valid"] is False
    assert result["response_validation"] is None
    assert result["internal_envelope"] is None


def test_response_invalid_due_to_forbidden_field_stops_roundtrip() -> None:
    request = build_valid_runtime_request()

    def invoker(_: dict) -> dict:
        response = build_valid_runtime_response()
        response["final_decision"] = "APPROVED"
        return response

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "RESPONSE_INVALID"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is False
    assert result["internal_envelope"] is None


def test_runtime_roundtrip_with_critical_block_becomes_blocked() -> None:
    request = build_valid_runtime_request()

    def invoker(_: dict) -> dict:
        return build_valid_runtime_response(
            documentary_status="DOCUMENTARY_BLOCKED",
            blocks=[
                {
                    "code": "CRITICAL_DOCUMENTARY_BLOCK",
                    "severity": "HIGH",
                    "documentary_only": True,
                }
            ],
        )

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "ROUNDTRIP_BLOCKED"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is True
    assert result["internal_envelope"] is not None
    assert result["internal_envelope"]["critical_block_present"] is True
    assert "CRITICAL_DOCUMENTARY_BLOCK" in result["internal_envelope"]["block_codes_received"]


def test_runtime_roundtrip_with_m07_incomplete_becomes_blocked() -> None:
    request = build_valid_runtime_request()

    def invoker(_: dict) -> dict:
        return build_valid_runtime_response(
            documentary_status="DOCUMENTARY_BLOCKED",
            blocks=[
                {
                    "code": "M07_DOCUMENTARY_INCOMPLETE",
                    "severity": "HIGH",
                    "documentary_only": True,
                }
            ],
        )

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "ROUNDTRIP_BLOCKED"
    assert result["response_validation"]["is_valid"] is True
    assert "M07_DOCUMENTARY_INCOMPLETE" in result["internal_envelope"]["block_codes_received"]


def test_runtime_roundtrip_with_coverage_insufficient_becomes_degraded() -> None:
    request = build_valid_runtime_request()

    def invoker(_: dict) -> dict:
        return build_valid_runtime_response(
            documentary_status="DOCUMENTARY_WARNING",
            blocks=[
                {
                    "code": "COVERAGE_INSUFFICIENT",
                    "severity": "MEDIUM",
                    "documentary_only": True,
                }
            ],
        )

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "ROUNDTRIP_DEGRADED"
    assert result["response_validation"]["is_valid"] is True
    assert result["internal_envelope"]["degrading_block_present"] is True
    assert "COVERAGE_INSUFFICIENT" in result["internal_envelope"]["block_codes_received"]


def test_runtime_roundtrip_rejects_level_b_m07_completion_overreach() -> None:
    request = build_valid_runtime_request()

    def invoker(_: dict) -> dict:
        return build_valid_runtime_response(
            documentary_status="DOCUMENTARY_OK",
            blocks=[],
            completion_declared=True,
        )

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "RESPONSE_INVALID"
    assert result["response_validation"]["is_valid"] is False
    assert any(
        "Level B cannot declare m07 completion" in error
        for error in result["response_validation"]["errors"]
    )
    assert result["internal_envelope"] is None


def test_runtime_roundtrip_allows_warning_only_audit_issue_without_failing_validation() -> None:
    request = build_valid_runtime_request()

    def invoker(_: dict) -> dict:
        return build_valid_runtime_response(
            documentary_status="DOCUMENTARY_OK",
            blocks=[],
            internal_only_audit=False,
        )

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "ROUNDTRIP_GREEN"
    assert result["response_validation"]["is_valid"] is True
    assert "audit.internal_only should be True" in result["response_validation"]["warnings"]
    assert result["internal_envelope"] is not None