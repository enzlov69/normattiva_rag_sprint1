from runtime.final_aba_runner_real_invoker import FederatedRunnerRealInvoker
from runtime.final_aba_runtime_handoff_service import FinalABARuntimeHandoffService


def _request():
    return {
        "request_id": "req_200",
        "case_id": "case_200",
        "trace_id": "trace_200",
        "api_version": "1.0",
        "caller_module": "A4_DomainActivation",
        "target_module": "B_REAL_FEDERATED_RUNNER",
        "timestamp": "2026-03-20T12:00:00Z",
        "payload": {"documentary_goal": "retrieve documentary packet only"},
    }


def _transport_with_blocks(request):
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
                "citations_valid": [],
                "citations_blocked": [{"id": "cit_blk_1"}],
                "vigenza_records": [{"id": "vig_1"}],
                "cross_reference_records": [{"id": "xref_1"}],
                "coverage_assessment": {"coverage_status": "INADEQUATE", "critical_gap_flag": True},
                "warnings": [],
                "errors": ["AUDIT_INCOMPLETE"],
                "blocks": [
                    "CRITICAL_DOCUMENTARY_BLOCK",
                    "M07_REQUIRED",
                    "COVERAGE_INADEQUATE",
                    "OUTPUT_NOT_OPPONIBLE",
                    "AUDIT_INCOMPLETE",
                ],
                "shadow_fragment": {"trace_id": request["trace_id"]},
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": request["timestamp"],
    }


def test_critical_blocks_are_propagated_to_level_a_without_loss():
    real_invoker = FederatedRunnerRealInvoker(transport=_transport_with_blocks)
    service = FinalABARuntimeHandoffService(mode="real", real_invoker=real_invoker)

    result = service.handle(_request())

    assert result["status"] == "BLOCKED"
    assert "CRITICAL_DOCUMENTARY_BLOCK" in result["blocks"]
    assert "M07_REQUIRED" in result["blocks"]
    assert "COVERAGE_INADEQUATE" in result["blocks"]
    assert "OUTPUT_NOT_OPPONIBLE" in result["blocks"]
    assert "AUDIT_INCOMPLETE" in result["blocks"]
    assert result["payload"]["level_a_next_step"] == "M07_LPR_MANDATORY_CONTINUATION_IN_LEVEL_A"
