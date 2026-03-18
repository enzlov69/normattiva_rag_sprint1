from runtime.final_ab_runner_real_invoker import FinalABRunnerRealInvoker
from runtime.final_ab_runtime_handoff_service import FinalABRuntimeHandoffService


def _base_request():
    return {
        "request_id": "req_003",
        "case_id": "case_003",
        "trace_id": "trace_003",
        "api_version": "v1",
        "caller_module": "level_a_frontdoor",
        "target_module": "level_b_runtime_handoff",
        "timestamp": "2026-03-18T10:10:00Z",
        "payload": {"query_text": "rinvio allegato mancante", "domain_target": "dlgs118"},
    }


def _runner_with_blocks(_runner_request):
    return {
        "documentary_packet": {
            "sources": [],
            "norm_units": [],
            "citations_valid": [],
            "citations_blocked": [{"act": "D.Lgs. 118/2011", "article": "1"}],
            "vigenza_records": [],
            "cross_reference_records": [],
            "coverage_assessment": {"status": "INADEQUATE"},
            "warnings": [],
            "errors": [],
            "blocks": [
                {"block_code": "CITATION_INCOMPLETE", "message": "Citation incomplete"},
                {"block_code": "VIGENZA_UNCERTAIN", "message": "Vigenza uncertain"},
                {"block_code": "CROSSREF_UNRESOLVED", "message": "Cross-reference unresolved"},
                {"block_code": "COVERAGE_INADEQUATE", "message": "Coverage inadequate"}
            ],
            "shadow_fragment": {}
        }
    }


def test_propagates_critical_blocks_to_level_a():
    service = FinalABRuntimeHandoffService(
        invocation_port=FinalABRunnerRealInvoker(runner_callable=_runner_with_blocks)
    )

    response = service.handle(_base_request())

    assert response["status"] == "BLOCKED"
    block_codes = {block["block_code"] for block in response["blocks"]}
    assert "CITATION_INCOMPLETE" in block_codes
    assert "VIGENZA_UNCERTAIN" in block_codes
    assert "CROSSREF_UNRESOLVED" in block_codes
    assert "COVERAGE_INADEQUATE" in block_codes
    assert response["payload"]["blocks"] == response["blocks"]
