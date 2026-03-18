from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.final_ab_pre_runtime_adapter import FinalABPreRuntimeAdapter, build_demo_level_b_response


def make_request() -> dict:
    return {
        "request_id": "req_002",
        "case_id": "case_002",
        "trace_id": "trace_002",
        "flow_id": "FINAL_AB_MIN_FLOW_V1",
        "api_version": "1.0.0",
        "caller_module": "A1_OrchestratorePPAV",
        "target_module": "B13_VigenzaChecker",
        "target_endpoint": "/doc/vigenza/check",
        "level_a_phase": "IN_RETRIEVAL",
        "m07_context": {
            "required": False,
            "support_requested": False,
            "human_completion_required": True,
            "requested_scope": "NONE",
        },
        "block_policy": {
            "propagate_critical": True,
            "reject_forbidden_fields": True,
            "reject_m07_closure_attempts": True,
        },
        "payload": {
            "query_text": "vigenza norma su punto essenziale",
            "domain_target": "tuel"
        },
        "timestamp": "2026-03-18T09:05:00Z",
    }


def test_critical_block_is_mandatorily_propagated_from_b_to_a() -> None:
    adapter = FinalABPreRuntimeAdapter()

    def provider(request: dict) -> dict:
        response = build_demo_level_b_response(request)
        block = {
            "block_id": "blk_vig_001",
            "case_id": request["case_id"],
            "block_code": "VIGENZA_UNCERTAIN",
            "block_category": "VIGENZA",
            "block_severity": "CRITICAL",
            "origin_module": "B13_VigenzaChecker",
            "affected_object_type": "VigenzaRecord",
            "affected_object_id": "vig_demo_001",
            "block_reason": "Essential point has uncertain vigore status.",
            "block_status": "OPEN",
        }
        response["blocks"] = [block]
        response["documentary_packet"]["blocks"] = [block]
        response["status"] = "DEGRADED"
        return response

    result = adapter.execute(make_request(), provider)

    assert result["status"] == "BLOCKED"
    assert len(result["propagated_blocks"]) == 1
    assert result["propagated_blocks"][0]["block_code"] == "VIGENZA_UNCERTAIN"
    assert result["propagated_blocks"][0]["level_a_required_handling"] == "RECEIVE_AND_STOP_OR_DEGRADE_UNTIL_METHOD_HANDLING"


def test_non_critical_warning_does_not_create_propagated_block() -> None:
    adapter = FinalABPreRuntimeAdapter()

    def provider(request: dict) -> dict:
        response = build_demo_level_b_response(request)
        response["warnings"] = [{"code": "PARTIAL_CONTEXT", "message": "Some contextual sources are not indexed yet."}]
        response["documentary_packet"]["warnings"] = response["warnings"]
        response["status"] = "SUCCESS_WITH_WARNINGS"
        return response

    result = adapter.execute(make_request(), provider)

    assert result["status"] == "SUCCESS_WITH_WARNINGS"
    assert result["warnings"]
    assert result["propagated_blocks"] == []
