from runtime.final_ab_runner_real_invoker import FinalABRunnerRealInvoker
from runtime.final_ab_runtime_handoff_service import FinalABRuntimeHandoffService


def _base_request():
    return {
        "request_id": "req_004",
        "case_id": "case_004",
        "trace_id": "trace_004",
        "api_version": "v1",
        "caller_module": "level_a_frontdoor",
        "target_module": "level_b_runtime_handoff",
        "timestamp": "2026-03-18T10:15:00Z",
        "payload": {"query_text": "supporto lettura integrale", "domain_target": "l241"},
    }


def _runner_m07_support_ok(_runner_request):
    return {
        "documentary_packet": {
            "sources": [{"id": "src_m07"}],
            "norm_units": [{"id": "unit_m07"}],
            "citations_valid": [],
            "citations_blocked": [],
            "vigenza_records": [],
            "cross_reference_records": [],
            "coverage_assessment": {"status": "PARTIAL"},
            "warnings": [{"code": "M07_SUPPORT_ONLY", "message": "Support only"}],
            "errors": [],
            "blocks": [{"block_code": "M07_REQUIRED", "message": "Human completion still required"}],
            "shadow_fragment": {},
            "human_completion_required": True
        }
    }


def _runner_m07_certified(_runner_request):
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
            "reading_integral_certified": True
        }
    }


def test_m07_support_remains_documentary_and_open():
    service = FinalABRuntimeHandoffService(
        invocation_port=FinalABRunnerRealInvoker(runner_callable=_runner_m07_support_ok)
    )

    response = service.handle(_base_request())

    assert response["status"] == "BLOCKED"
    block_codes = {block["block_code"] for block in response["blocks"]}
    assert "M07_REQUIRED" in block_codes
    assert response["payload"]["human_completion_required"] is True


def test_m07_cannot_be_certified_by_level_b():
    service = FinalABRuntimeHandoffService(
        invocation_port=FinalABRunnerRealInvoker(runner_callable=_runner_m07_certified)
    )

    response = service.handle(_base_request())

    assert response["status"] == "REJECTED"
    block_codes = {block["block_code"] for block in response["blocks"]}
    assert "RAG_SCOPE_VIOLATION" in block_codes
