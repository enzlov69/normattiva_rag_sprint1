from runtime.final_aba_runner_real_invoker import FederatedRunnerRealInvoker


def _base_request():
    return {
        "request_id": "req_100",
        "case_id": "case_100",
        "trace_id": "trace_100",
        "api_version": "1.0",
        "caller_module": "A1_Orchestrator",
        "target_module": "B_REAL_FEDERATED_RUNNER",
        "timestamp": "2026-03-20T11:00:00Z",
        "payload": {"documentary_goal": "retrieve documentary packet only"},
    }


def _valid_response(request):
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
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": request["timestamp"],
    }


def test_real_response_with_forbidden_field_is_rejected():
    def transport(request):
        response = _valid_response(request)
        response["payload"]["documentary_packet"]["final_decision"] = "GO"
        return response

    invoker = FederatedRunnerRealInvoker(transport=transport)
    result = invoker.invoke(_base_request())

    assert result["status"] == "REJECTED"
    assert "FORBIDDEN_LEVEL_B_RESPONSE_FIELD" in result["errors"]
    assert "RAG_SCOPE_VIOLATION" in result["blocks"]
    assert "OUTPUT_NOT_OPPONIBLE" in result["blocks"]


def test_real_response_missing_documentary_field_is_rejected():
    def transport(request):
        response = _valid_response(request)
        del response["payload"]["documentary_packet"]["sources"]
        return response

    invoker = FederatedRunnerRealInvoker(transport=transport)
    result = invoker.invoke(_base_request())

    assert result["status"] == "REJECTED"
    assert "INVALID_DOCUMENTARY_PACKET" in result["errors"]
    assert "AUDIT_INCOMPLETE" in result["blocks"]
    assert "OUTPUT_NOT_OPPONIBLE" in result["blocks"]


def test_real_response_cannot_be_non_documentary_scalar_payload():
    def transport(request):
        response = _valid_response(request)
        response["payload"] = "not-a-dict"
        return response

    invoker = FederatedRunnerRealInvoker(transport=transport)
    result = invoker.invoke(_base_request())

    assert result["status"] == "REJECTED"
    assert "INVALID_LEVEL_B_RESPONSE" in result["errors"]
    assert "OUTPUT_NOT_OPPONIBLE" in result["blocks"]
