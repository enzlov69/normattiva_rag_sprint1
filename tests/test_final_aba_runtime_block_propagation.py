from __future__ import annotations

from runtime.final_aba_runtime_handoff_service import (
    build_level_a_internal_envelope,
    propagate_documentary_blocks,
)


def build_valid_runtime_request() -> dict:
    return {
        "request_id": "REQ-RUNTIME-BLOCK-0001",
        "case_id": "CASE-RUNTIME-BLOCK-0001",
        "trace_id": "TRACE-RUNTIME-BLOCK-0001",
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
    }


def build_valid_runtime_response(blocks: list[dict] | None = None) -> dict:
    return {
        "response_id": "RESP-RUNTIME-BLOCK-0001",
        "request_id": "REQ-RUNTIME-BLOCK-0001",
        "source_level": "LEVEL_B",
        "target_level": "LEVEL_A",
        "response_kind": "DOCUMENTARY_SUPPORT_RESPONSE",
        "documentary_status": "DOCUMENTARY_WARNING",
        "documentary_packet": {
            "documentary_only": True,
            "contains_decision": False,
        },
        "citations": [],
        "vigency_checks": [],
        "cross_references": [],
        "coverage_report": {
            "coverage_status": "PARTIAL",
        },
        "warnings": [],
        "errors": [],
        "blocks": blocks or [],
        "m07_documentary_support": {
            "support_provided": True,
            "documentary_only": True,
            "completion_declared": False,
        },
        "audit": {
            "created_by": "LEVEL_B_RUNTIME",
            "internal_only": True,
        },
    }


def test_no_blocks_produces_roundtrip_green() -> None:
    response = build_valid_runtime_response(blocks=[])

    result = propagate_documentary_blocks(response)

    assert result["runtime_status"] == "ROUNDTRIP_GREEN"
    assert result["documentary_block_propagated"] is False
    assert result["critical_block_present"] is False
    assert result["degrading_block_present"] is False
    assert result["block_codes_received"] == []
    assert result["can_emit_go_no_go"] is False
    assert result["can_emit_firma_ready"] is False
    assert result["can_authorize_output"] is False


def test_critical_documentary_block_produces_roundtrip_blocked() -> None:
    response = build_valid_runtime_response(
        blocks=[
            {
                "code": "CRITICAL_DOCUMENTARY_BLOCK",
                "severity": "HIGH",
                "documentary_only": True,
            }
        ]
    )

    result = propagate_documentary_blocks(response)

    assert result["runtime_status"] == "ROUNDTRIP_BLOCKED"
    assert result["documentary_block_propagated"] is True
    assert result["critical_block_present"] is True
    assert result["degrading_block_present"] is False
    assert "CRITICAL_DOCUMENTARY_BLOCK" in result["block_codes_received"]


def test_m07_documentary_incomplete_is_treated_as_critical_block() -> None:
    response = build_valid_runtime_response(
        blocks=[
            {
                "code": "M07_DOCUMENTARY_INCOMPLETE",
                "severity": "HIGH",
                "documentary_only": True,
            }
        ]
    )

    result = propagate_documentary_blocks(response)

    assert result["runtime_status"] == "ROUNDTRIP_BLOCKED"
    assert result["critical_block_present"] is True
    assert "M07_DOCUMENTARY_INCOMPLETE" in result["block_codes_received"]


def test_coverage_insufficient_produces_roundtrip_degraded() -> None:
    response = build_valid_runtime_response(
        blocks=[
            {
                "code": "COVERAGE_INSUFFICIENT",
                "severity": "MEDIUM",
                "documentary_only": True,
            }
        ]
    )

    result = propagate_documentary_blocks(response)

    assert result["runtime_status"] == "ROUNDTRIP_DEGRADED"
    assert result["documentary_block_propagated"] is True
    assert result["critical_block_present"] is False
    assert result["degrading_block_present"] is True
    assert "COVERAGE_INSUFFICIENT" in result["block_codes_received"]


def test_citation_not_idonea_and_vigency_uncertain_keep_degraded_status() -> None:
    response = build_valid_runtime_response(
        blocks=[
            {
                "code": "CITATION_NOT_IDONEA",
                "severity": "HIGH",
                "documentary_only": True,
            },
            {
                "code": "VIGENCY_UNCERTAIN",
                "severity": "HIGH",
                "documentary_only": True,
            },
        ]
    )

    result = propagate_documentary_blocks(response)

    assert result["runtime_status"] == "ROUNDTRIP_DEGRADED"
    assert result["critical_block_present"] is False
    assert result["degrading_block_present"] is True
    assert "CITATION_NOT_IDONEA" in result["block_codes_received"]
    assert "VIGENCY_UNCERTAIN" in result["block_codes_received"]


def test_critical_and_degrading_blocks_together_remain_blocked() -> None:
    response = build_valid_runtime_response(
        blocks=[
            {
                "code": "CRITICAL_DOCUMENTARY_BLOCK",
                "severity": "HIGH",
                "documentary_only": True,
            },
            {
                "code": "COVERAGE_INSUFFICIENT",
                "severity": "MEDIUM",
                "documentary_only": True,
            },
        ]
    )

    result = propagate_documentary_blocks(response)

    assert result["runtime_status"] == "ROUNDTRIP_BLOCKED"
    assert result["critical_block_present"] is True
    assert result["degrading_block_present"] is True


def test_internal_envelope_is_non_opposable_and_contains_propagation_trace() -> None:
    request = build_valid_runtime_request()
    response = build_valid_runtime_response(
        blocks=[
            {
                "code": "COVERAGE_INSUFFICIENT",
                "severity": "MEDIUM",
                "documentary_only": True,
            }
        ]
    )
    propagation = propagate_documentary_blocks(response)

    envelope = build_level_a_internal_envelope(
        request_payload=request,
        response_payload=response,
        propagation_result=propagation,
    )

    assert envelope["envelope_kind"] == "LEVEL_A_INTERNAL_DOCUMENTARY_RETURN"
    assert envelope["request_id"] == request["request_id"]
    assert envelope["response_id"] == response["response_id"]
    assert envelope["case_id"] == request["case_id"]
    assert envelope["trace_id"] == request["trace_id"]
    assert envelope["runtime_status"] == "ROUNDTRIP_DEGRADED"
    assert envelope["documentary_block_propagated"] is True
    assert envelope["degrading_block_present"] is True
    assert envelope["can_emit_go_no_go"] is False
    assert envelope["can_emit_firma_ready"] is False
    assert envelope["can_authorize_output"] is False
    assert envelope["shadow"]["internal_use_only"] is True
    assert envelope["shadow"]["non_opposable"] is True
    assert envelope["shadow"]["contains_no_final_decision"] is True