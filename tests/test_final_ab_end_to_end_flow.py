from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.final_ab_pre_runtime_adapter import FinalABPreRuntimeAdapter, build_demo_level_b_response


def make_request() -> dict:
    return {
        "request_id": "req_004",
        "case_id": "case_004",
        "trace_id": "trace_004",
        "flow_id": "FINAL_AB_MIN_FLOW_V1",
        "api_version": "1.0.0",
        "caller_module": "A1_OrchestratorePPAV",
        "target_module": "B16_M07SupportLayer",
        "target_endpoint": "/doc/m07/support",
        "level_a_phase": "IN_M07",
        "m07_context": {
            "required": True,
            "support_requested": True,
            "human_completion_required": True,
            "requested_scope": "ANNEX_AND_CROSSREF"
        },
        "block_policy": {
            "propagate_critical": True,
            "reject_forbidden_fields": True,
            "reject_m07_closure_attempts": True
        },
        "payload": {
            "query_text": "articolo 42 e rinvii con allegati",
            "domain_target": "tuel",
            "top_k": 5
        },
        "timestamp": "2026-03-18T09:15:00Z"
    }


def test_end_to_end_flow_returns_support_only_envelope_for_level_a() -> None:
    adapter = FinalABPreRuntimeAdapter()

    def provider(request: dict) -> dict:
        response = build_demo_level_b_response(request)
        response["responder_module"] = "B16_M07SupportLayer"
        response["documentary_packet"]["sources"].append(
            {
                "source_id": "source_demo_002",
                "atto_tipo": "L.",
                "atto_numero": "241",
                "atto_anno": "1990",
                "uri_ufficiale": "https://www.normattiva.it/"
            }
        )
        response["documentary_packet"]["cross_reference_records"] = [
            {
                "crossref_id": "xref_001",
                "resolved_flag": True,
                "resolution_status": "RESOLVED"
            }
        ]
        response["documentary_packet"]["coverage_assessment"] = {
            "coverage_id": "cov_end_001",
            "coverage_status": "SUFFICIENT",
            "critical_gap_flag": False
        }
        response["documentary_packet"]["shadow_fragment"] = {
            "human_completion_required": True,
            "ordered_reading_sequence": ["nu_demo_001", "nu_demo_002"],
            "annex_refs": ["ann_001"],
            "crossref_refs": ["xref_001"]
        }
        return response

    result = adapter.execute(make_request(), provider)

    assert result["status"] == "SUCCESS"
    assert result["support_only_flag"] is True
    assert result["opponibile_output_flag"] is False
    assert result["level_a_action_required"] is True
    assert result["m07_boundary_state"] == "PREPARATORY_ONLY"
    assert len(result["documentary_packet"]["sources"]) == 2
    assert result["shadow_fragment"]["request_contract_valid"] is True
    assert result["shadow_fragment"]["response_contract_valid"] is True
    assert result["propagated_blocks"] == []
