from runtime.final_aba_runner_real_invoker import FederatedRunnerRealInvoker


def _valid_transport(request_envelope):
    documentary_packet = {
        "sources": [{"source_id": "src_001"}],
        "norm_units": [{"norm_unit_id": "nu_001"}],
        "citations_valid": [{"citation_id": "cit_001"}],
        "citations_blocked": [],
        "vigenza_records": [{"vigenza_id": "vig_001"}],
        "cross_reference_records": [{"crossref_id": "xref_001"}],
        "coverage_assessment": {
            "coverage_status": "ADEQUATE",
            "critical_gap_flag": False,
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "shadow_fragment": {
            "trace_id": request_envelope["trace_id"],
            "executed_modules": ["B_REAL_FEDERATED_RUNNER"],
        },
    }
    return {
        "request_id": request_envelope["request_id"],
        "case_id": request_envelope["case_id"],
        "trace_id": request_envelope["trace_id"],
        "api_version": request_envelope["api_version"],
        "responder_module": "B_REAL_FEDERATED_RUNNER",
        "status": "SUCCESS",
        "payload": {"documentary_packet": documentary_packet},
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": request_envelope["timestamp"],
    }


def _valid_request():
    return {
        "request_id": "req_001",
        "case_id": "case_001",
        "trace_id": "trace_001",
        "api_version": "1.0",
        "caller_module": "A5_FinalComplianceGate",
        "target_module": "B_REAL_FEDERATED_RUNNER",
        "timestamp": "2026-03-20T10:00:00Z",
        "payload": {
            "documentary_goal": "retrieve documentary packet only",
            "domain_code": "ENTI_LOCALI",
        },
    }


def test_request_is_normalized_with_default_status_and_lists():
    invoker = FederatedRunnerRealInvoker(transport=_valid_transport)

    response = invoker.invoke(_valid_request())

    assert response["status"] == "SUCCESS"
    assert response["blocks"] == []
    assert response["errors"] == []


def test_request_missing_case_id_is_rejected():
    invoker = FederatedRunnerRealInvoker(transport=_valid_transport)
    request = _valid_request()
    request.pop("case_id")

    response = invoker.invoke(request)

    assert response["status"] == "REJECTED"
    assert "INVALID_LEVEL_B_REQUEST" in response["errors"]
    assert "OUTPUT_NOT_OPPONIBLE" in response["blocks"]


def test_request_missing_trace_id_is_rejected():
    invoker = FederatedRunnerRealInvoker(transport=_valid_transport)
    request = _valid_request()
    request.pop("trace_id")

    response = invoker.invoke(request)

    assert response["status"] == "REJECTED"
    assert "INVALID_LEVEL_B_REQUEST" in response["errors"]
    assert "OUTPUT_NOT_OPPONIBLE" in response["blocks"]


def test_request_with_decisional_field_is_rejected_before_runner_call():
    calls = {"count": 0}

    def counting_transport(request_envelope):
        calls["count"] += 1
        return _valid_transport(request_envelope)

    invoker = FederatedRunnerRealInvoker(transport=counting_transport)
    request = _valid_request()
    request["payload"]["final_decision"] = "GO"

    response = invoker.invoke(request)

    assert response["status"] == "REJECTED"
    assert "FORBIDDEN_LEVEL_B_REQUEST_FIELD" in response["errors"]
    assert "RAG_SCOPE_VIOLATION" in response["blocks"]
    assert "OUTPUT_NOT_OPPONIBLE" in response["blocks"]
    assert calls["count"] == 0


def test_request_lists_must_be_lists_when_explicitly_provided():
    invoker = FederatedRunnerRealInvoker(transport=_valid_transport)
    request = _valid_request()
    request["warnings"] = "not-a-list"

    response = invoker.invoke(request)

    assert response["status"] == "REJECTED"
    assert "INVALID_LEVEL_B_REQUEST" in response["errors"]
    assert "OUTPUT_NOT_OPPONIBLE" in response["blocks"]
