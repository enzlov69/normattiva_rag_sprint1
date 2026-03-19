import pytest

from runtime.fip_ind_gate import (
    FIPINDBoundaryViolationError,
    validate_documentary_support_response,
)


def test_level_b_response_rejects_final_qualification() -> None:
    response = {
        "request_id": "req_fip_001",
        "case_id": "case_fip_001",
        "trace_id": "trace_fip_001",
        "api_version": "2.0",
        "responder_module": "B17_FIPINDSupportLayer",
        "status": "SUCCESS",
        "payload": {
            "documentary_packet": {
                "question_ids": ["Q01", "Q02"],
                "support_only_flag": True
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": "2026-03-20T10:00:01Z",
        "final_act_qualification": "INDIRIZZO_PURO"
    }

    with pytest.raises(FIPINDBoundaryViolationError):
        validate_documentary_support_response(response)


def test_level_b_response_rejects_non_support_only_flag() -> None:
    response = {
        "request_id": "req_fip_002",
        "case_id": "case_fip_002",
        "trace_id": "trace_fip_002",
        "api_version": "2.0",
        "responder_module": "B17_FIPINDSupportLayer",
        "status": "SUCCESS",
        "payload": {
            "documentary_packet": {
                "question_ids": ["Q01", "Q02"],
                "support_only_flag": False
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": "2026-03-20T10:00:01Z"
    }

    with pytest.raises(FIPINDBoundaryViolationError):
        validate_documentary_support_response(response)
