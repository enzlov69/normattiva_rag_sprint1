from runtime.final_ab_runner_real_invoker import FinalABRunnerRealInvoker
from runtime.final_ab_runtime_handoff_service import FinalABRuntimeHandoffService


def _base_request():
    return {
        "request_id": "req_002",
        "case_id": "case_002",
        "trace_id": "trace_002",
        "api_version": "v1",
        "caller_module": "level_a_frontdoor",
        "target_module": "level_b_runtime_handoff",
        "timestamp": "2026-03-18T10:05:00Z",
        "payload": {"query_text": "vigenza art. 1", "domain_target": "tuel"},
    }


def _runner_with_forbidden_field(_runner_request):
    return {
        "documentary_packet": {
            "sources": [],
            "norm_units": [],
            "citations_valid": [],
            "citations_blocked": [],
            "vigenza_records": [],
            "cross_reference_records": [],
            "coverage_assessment": {},
            "warnings": [],
            "errors": [],
            "blocks": [],
            "shadow_fragment": {},
            "final_decision": "APPLICABILE"
        }
    }


def _runner_with_m07_closure(_runner_request):
    return {
        "documentary_packet": {
            "sources": [],
            "norm_units": [],
            "citations_valid": [],
            "citations_blocked": [],
            "vigenza_records": [],
            "cross_reference_records": [],
            "coverage_assessment": {},
            "warnings": [],
            "errors": [],
            "blocks": [],
            "shadow_fragment": {},
            "m07_closed": True
        }
    }


def test_rejects_conclusory_field_from_runner():
    service = FinalABRuntimeHandoffService(
        invocation_port=FinalABRunnerRealInvoker(runner_callable=_runner_with_forbidden_field)
    )

    response = service.handle(_base_request())

    assert response["status"] == "REJECTED"
    block_codes = {block["block_code"] for block in response["blocks"]}
    assert "RAG_SCOPE_VIOLATION" in block_codes


def test_rejects_m07_closure_semantic_from_runner():
    service = FinalABRuntimeHandoffService(
        invocation_port=FinalABRunnerRealInvoker(runner_callable=_runner_with_m07_closure)
    )

    response = service.handle(_base_request())

    assert response["status"] == "REJECTED"
    block_codes = {block["block_code"] for block in response["blocks"]}
    assert "RAG_SCOPE_VIOLATION" in block_codes
