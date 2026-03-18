from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.final_ab_pre_runtime_adapter import FinalABPreRuntimeAdapter, build_demo_level_b_response


def make_request() -> dict:
    return {
        "request_id": "req_003",
        "case_id": "case_003",
        "trace_id": "trace_003",
        "flow_id": "FINAL_AB_MIN_FLOW_V1",
        "api_version": "1.0.0",
        "caller_module": "A4_M07Governor",
        "target_module": "B16_M07SupportLayer",
        "target_endpoint": "/doc/m07/support",
        "level_a_phase": "IN_M07",
        "m07_context": {
            "required": True,
            "support_requested": True,
            "human_completion_required": True,
            "requested_scope": "ANNEX_AND_CROSSREF",
        },
        "block_policy": {
            "propagate_critical": True,
            "reject_forbidden_fields": True,
            "reject_m07_closure_attempts": True,
        },
        "payload": {
            "query_text": "supporto documentale m07 lettura integrale",
            "domain_target": "l241"
        },
        "timestamp": "2026-03-18T09:10:00Z",
    }


def test_m07_support_remains_preparatory_only() -> None:
    adapter = FinalABPreRuntimeAdapter()

    def provider(request: dict) -> dict:
        response = build_demo_level_b_response(request)
        response["responder_module"] = "B16_M07SupportLayer"
        response["documentary_packet"]["shadow_fragment"] = {
            "human_completion_required": True,
            "ordered_reading_sequence": ["nu_demo_001", "nu_demo_002"],
            "annex_refs": ["ann_001"],
            "crossref_refs": ["xref_001"],
        }
        return response

    result = adapter.execute(make_request(), provider)

    assert result["status"] == "SUCCESS"
    assert result["m07_boundary_state"] == "PREPARATORY_ONLY"
    assert result["support_only_flag"] is True
    assert result["opponibile_output_flag"] is False


def test_m07_closure_attempt_from_level_b_is_rejected() -> None:
    adapter = FinalABPreRuntimeAdapter()

    def provider(request: dict) -> dict:
        response = build_demo_level_b_response(request)
        response["responder_module"] = "B16_M07SupportLayer"
        response["documentary_packet"]["m07_closed"] = True
        return response

    result = adapter.execute(make_request(), provider)

    assert result["status"] == "REJECTED"
    assert result["m07_boundary_state"] == "BOUNDARY_VIOLATION"
    assert any(block["block_code"] == "RAG_SCOPE_VIOLATION" for block in result["propagated_blocks"])


def test_m07_support_cannot_remove_human_completion_requirement() -> None:
    adapter = FinalABPreRuntimeAdapter()

    def provider(request: dict) -> dict:
        response = build_demo_level_b_response(request)
        response["responder_module"] = "B16_M07SupportLayer"
        response["documentary_packet"]["shadow_fragment"] = {
            "human_completion_required": False,
            "ordered_reading_sequence": ["nu_demo_001"]
        }
        return response

    result = adapter.execute(make_request(), provider)

    assert result["status"] == "REJECTED"
    assert result["m07_boundary_state"] == "BOUNDARY_VIOLATION"
