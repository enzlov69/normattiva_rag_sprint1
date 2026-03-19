from adapters.final_ab_pre_runtime_adapter import FinalABPreRuntimeAdapter, build_demo_level_b_response


def _base_request() -> dict:
    return {
        "request_id": "req_phase10_e2e_001",
        "case_id": "case_phase10_e2e_001",
        "trace_id": "trace_phase10_e2e_001",
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
            "requested_scope": "NONE"
        },
        "block_policy": {
            "propagate_critical": True,
            "reject_forbidden_fields": True,
            "reject_m07_closure_attempts": True
        },
        "payload": {
            "query_text": "articolo 191 tuel",
            "domain_target": "tuel",
            "top_k": 5
        },
        "timestamp": "2026-03-19T10:33:00Z"
    }


def test_end_to_end_prehandoff_valid_flow_is_support_only() -> None:
    adapter = FinalABPreRuntimeAdapter()
    result = adapter.execute(_base_request(), build_demo_level_b_response)

    assert result["status"] == "SUCCESS"
    assert result["support_only_flag"] is True
    assert result["opponibile_output_flag"] is False
    assert result["propagated_blocks"] == []


def test_end_to_end_prehandoff_propagates_critical_blocks() -> None:
    adapter = FinalABPreRuntimeAdapter()

    def provider(request: dict) -> dict:
        response = build_demo_level_b_response(request)
        response["blocks"] = [
            {
                "block_code": "CITATION_INCOMPLETE",
                "block_severity": "CRITICAL",
                "origin_module": "B15_CitationBuilder"
            }
        ]
        return response

    result = adapter.execute(_base_request(), provider)

    assert result["status"] == "BLOCKED"
    assert any(block["block_code"] == "CITATION_INCOMPLETE" for block in result["propagated_blocks"])


def test_end_to_end_prehandoff_rejects_decisional_level_b_payload() -> None:
    adapter = FinalABPreRuntimeAdapter()

    def provider(request: dict) -> dict:
        response = build_demo_level_b_response(request)
        response["final_decision"] = "GO"
        return response

    result = adapter.execute(_base_request(), provider)

    assert result["status"] == "REJECTED"
    assert any(block["block_code"] == "RAG_SCOPE_VIOLATION" for block in result["propagated_blocks"])
