from runtime.final_ab_runner_real_invoker import FinalABRunnerRealInvoker
from runtime.final_ab_runtime_handoff_service import FinalABRuntimeHandoffService


def _runner_ok(_runner_request):
    return {
        "documentary_packet": {
            "sources": [{"id": "src_1", "uri": "https://example.test/norma/1"}],
            "norm_units": [{"id": "art_1", "article": "1"}],
            "citations_valid": [{"act": "D.Lgs. 267/2000", "article": "1"}],
            "citations_blocked": [],
            "vigenza_records": [{"status": "vigente"}],
            "cross_reference_records": [{"resolved": True}],
            "coverage_assessment": {"status": "ADEQUATE"},
            "warnings": [],
            "errors": [],
            "blocks": [],
            "shadow_fragment": {"runner_trace": "rbx_001"}
        }
    }


def _base_request():
    return {
        "request_id": "req_001",
        "case_id": "case_001",
        "trace_id": "trace_001",
        "api_version": "v1",
        "caller_module": "level_a_frontdoor",
        "target_module": "level_b_runtime_handoff",
        "timestamp": "2026-03-18T10:00:00Z",
        "payload": {
            "query_text": "articolo 1 TUEL",
            "domain_target": "tuel",
            "metadata_filters": {"vigente": True},
            "top_k": 5
        }
    }


def test_real_handoff_contract_success():
    service = FinalABRuntimeHandoffService(
        invocation_port=FinalABRunnerRealInvoker(runner_callable=_runner_ok)
    )

    response = service.handle(_base_request())

    assert response["status"] == "SUCCESS"
    assert response["request_id"] == "req_001"
    assert response["case_id"] == "case_001"
    assert response["trace_id"] == "trace_001"
    assert response["responder_module"] == "level_b_runtime_handoff"
    assert "payload" in response
    assert set(
        [
            "sources",
            "norm_units",
            "citations_valid",
            "citations_blocked",
            "vigenza_records",
            "cross_reference_records",
            "coverage_assessment",
            "warnings",
            "errors",
            "blocks",
            "shadow_fragment",
        ]
    ).issubset(set(response["payload"].keys()))


def test_real_handoff_rejects_missing_case_id():
    service = FinalABRuntimeHandoffService(
        invocation_port=FinalABRunnerRealInvoker(runner_callable=_runner_ok)
    )
    request = _base_request()
    del request["case_id"]

    response = service.handle(request)

    assert response["status"] == "REJECTED"
    assert response["errors"][0]["code"] == "INVALID_AB_REQUEST"
    assert response["blocks"][0]["block_code"] == "AUDIT_INCOMPLETE"


def test_real_handoff_rejects_target_module_mismatch():
    service = FinalABRuntimeHandoffService(
        invocation_port=FinalABRunnerRealInvoker(runner_callable=_runner_ok)
    )
    request = _base_request()
    request["target_module"] = "invalid_target"

    response = service.handle(request)

    assert response["status"] == "REJECTED"
    assert response["errors"][0]["code"] == "TARGET_MODULE_MISMATCH"
    assert response["blocks"][0]["block_code"] == "RAG_SCOPE_VIOLATION"
