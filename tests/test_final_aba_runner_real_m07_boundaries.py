from runtime.final_aba_runner_real_invoker import FederatedRunnerRealInvoker


def _request():
    return {
        "request_id": "req_300",
        "case_id": "case_300",
        "trace_id": "trace_300",
        "api_version": "1.0",
        "caller_module": "A6_M07",
        "target_module": "B_REAL_FEDERATED_RUNNER",
        "timestamp": "2026-03-20T13:00:00Z",
        "payload": {"documentary_goal": "support M07 documentary reconstruction only"},
    }


def _response_with_m07_closure(request):
    return {
        "request_id": request["request_id"],
        "case_id": request["case_id"],
        "trace_id": request["trace_id"],
        "api_version": request["api_version"],
        "responder_module": "B_REAL_FEDERATED_RUNNER",
        "status": "SUCCESS",
        "payload": {
            "documentary_packet": {
                "sources": [{"id": "src_1"}],
                "norm_units": [{"id": "nu_1"}],
                "citations_valid": [{"id": "cit_1"}],
                "citations_blocked": [],
                "vigenza_records": [{"id": "vig_1"}],
                "cross_reference_records": [{"id": "xref_1"}],
                "coverage_assessment": {"coverage_status": "ADEQUATE", "critical_gap_flag": False},
                "warnings": [],
                "errors": [],
                "blocks": [],
                "shadow_fragment": {"trace_id": request["trace_id"]},
                "m07_completed": True,
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": request["timestamp"],
    }


def test_runner_cannot_close_m07_or_certify_it_completed():
    invoker = FederatedRunnerRealInvoker(transport=_response_with_m07_closure)

    result = invoker.invoke(_request())

    assert result["status"] == "REJECTED"
    assert "FORBIDDEN_LEVEL_B_RESPONSE_FIELD" in result["errors"]
    assert "M07_REQUIRED" in result["blocks"]
    assert "RAG_SCOPE_VIOLATION" in result["blocks"]
    assert "OUTPUT_NOT_OPPONIBLE" in result["blocks"]
