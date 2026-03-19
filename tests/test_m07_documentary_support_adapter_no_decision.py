import pytest

from runtime.m07_documentary_support_adapter import (
    M07BoundaryViolationError,
    consume_m07_documentary_support_response,
)


def test_adapter_rejects_top_level_forbidden_decision_field() -> None:
    response_payload = {
        "request_id": "req_3001",
        "case_id": "case_3001",
        "trace_id": "trace_3001",
        "api_version": "2.0",
        "responder_module": "B16_M07SupportLayer",
        "status": "SUCCESS",
        "payload": {
            "documentary_packet": {
                "source_ids": ["source_1"],
                "norm_unit_ids": ["unit_1"],
                "support_only_flag": True
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": "2026-03-19T18:20:01Z",
        "final_decision": "GO"
    }

    with pytest.raises(M07BoundaryViolationError):
        consume_m07_documentary_support_response(response_payload)


def test_adapter_rejects_nested_forbidden_m07_closed_field() -> None:
    response_payload = {
        "request_id": "req_3002",
        "case_id": "case_3002",
        "trace_id": "trace_3002",
        "api_version": "2.0",
        "responder_module": "B16_M07SupportLayer",
        "status": "SUCCESS",
        "payload": {
            "documentary_packet": {
                "source_ids": ["source_1"],
                "norm_unit_ids": ["unit_1"],
                "support_only_flag": True,
                "citation_packets": [
                    {
                        "citation_id": "cit_1",
                        "m07_closed": True
                    }
                ]
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": "2026-03-19T18:20:01Z"
    }

    with pytest.raises(M07BoundaryViolationError):
        consume_m07_documentary_support_response(response_payload)


def test_adapter_rejects_documentary_packet_without_support_only_flag_true() -> None:
    response_payload = {
        "request_id": "req_3003",
        "case_id": "case_3003",
        "trace_id": "trace_3003",
        "api_version": "2.0",
        "responder_module": "B16_M07SupportLayer",
        "status": "SUCCESS",
        "payload": {
            "documentary_packet": {
                "source_ids": ["source_1"],
                "norm_unit_ids": ["unit_1"],
                "support_only_flag": False
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": "2026-03-19T18:20:01Z"
    }

    with pytest.raises(M07BoundaryViolationError):
        consume_m07_documentary_support_response(response_payload)