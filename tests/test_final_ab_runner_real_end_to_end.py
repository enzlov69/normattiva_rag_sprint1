from runtime.final_ab_runner_real_invoker import FinalABRunnerRealInvoker
from runtime.final_ab_runtime_handoff_service import FinalABRuntimeHandoffService


class FakeBlackBoxRunner:
    def __call__(self, runner_request):
        assert runner_request["request_id"] == "req_005"
        assert runner_request["case_id"] == "case_005"
        assert runner_request["trace_id"] == "trace_005"
        assert runner_request["query_text"] == "art. 107 TUEL"
        return {
            "payload": {
                "sources": [{"id": "src_107", "uri": "https://example.test/tuel/107"}],
                "norm_units": [{"id": "art_107", "article": "107"}],
                "citations_valid": [{"act": "D.Lgs. 267/2000", "article": "107"}],
                "citations_blocked": [],
                "vigenza_records": [{"status": "vigente", "official_uri": "https://example.test/tuel/107"}],
                "cross_reference_records": [{"resolved": True}],
                "coverage_assessment": {"status": "ADEQUATE", "coverage_score": 0.92},
                "warnings": [{"code": "DOCUMENTARY_ONLY", "message": "No applicative judgment"}],
                "errors": [],
                "blocks": [],
                "shadow_fragment": {"runner_trace": "blackbox_107"}
            }
        }


def _base_request():
    return {
        "request_id": "req_005",
        "case_id": "case_005",
        "trace_id": "trace_005",
        "api_version": "v1",
        "caller_module": "level_a_frontdoor",
        "target_module": "level_b_runtime_handoff",
        "timestamp": "2026-03-18T10:20:00Z",
        "payload": {
            "query_text": "art. 107 TUEL",
            "domain_target": "tuel",
            "metadata_filters": {"vigente": True},
            "top_k": 3,
            "runtime_flags": {"frontdoor_validated": True}
        }
    }


def test_end_to_end_real_runtime_handoff_with_black_box_runner():
    service = FinalABRuntimeHandoffService(
        invocation_port=FinalABRunnerRealInvoker(runner_callable=FakeBlackBoxRunner())
    )

    response = service.handle(_base_request())

    assert response["status"] == "SUCCESS_WITH_WARNINGS"
    assert response["payload"]["sources"][0]["id"] == "src_107"
    assert response["payload"]["norm_units"][0]["article"] == "107"
    assert response["warnings"][0]["code"] == "DOCUMENTARY_ONLY"
    assert response["blocks"] == []
    assert response["errors"] == []
