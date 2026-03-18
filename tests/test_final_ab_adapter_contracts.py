from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.final_ab_pre_runtime_adapter import FinalABPreRuntimeAdapter, build_demo_level_b_response


def make_request() -> dict:
    return {
        "request_id": "req_001",
        "case_id": "case_001",
        "trace_id": "trace_001",
        "flow_id": "FINAL_AB_MIN_FLOW_V1",
        "api_version": "1.0.0",
        "caller_module": "A1_OrchestratorePPAV",
        "target_module": "B10_HybridRetriever",
        "target_endpoint": "/doc/retrieval/query",
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
            "query_text": "articolo 42 tuel",
            "domain_target": "tuel",
            "top_k": 3,
        },
        "timestamp": "2026-03-18T09:00:00Z",
    }


def test_adapter_accepts_valid_request_and_valid_response() -> None:
    adapter = FinalABPreRuntimeAdapter()
    result = adapter.execute(make_request(), build_demo_level_b_response)

    assert result["status"] == "SUCCESS"
    assert result["support_only_flag"] is True
    assert result["opponibile_output_flag"] is False
    assert result["errors"] == []
    assert result["propagated_blocks"] == []


def test_adapter_rejects_request_without_case_id() -> None:
    adapter = FinalABPreRuntimeAdapter()
    request = make_request()
    del request["case_id"]

    result = adapter.execute(request, build_demo_level_b_response)

    assert result["status"] == "REJECTED"
    assert any(error["code"] == "MISSING_CASE_ID" for error in result["errors"])
    assert result["support_only_flag"] is True
    assert result["opponibile_output_flag"] is False


def test_adapter_rejects_response_with_forbidden_level_b_field() -> None:
    adapter = FinalABPreRuntimeAdapter()

    def provider(request: dict) -> dict:
        response = build_demo_level_b_response(request)
        response["final_decision"] = "GO"
        return response

    result = adapter.execute(make_request(), provider)

    assert result["status"] == "REJECTED"
    assert any(block["block_code"] == "RAG_SCOPE_VIOLATION" for block in result["propagated_blocks"])
    assert "final_decision" in result["shadow_fragment"]["forbidden_fields_detected"]
