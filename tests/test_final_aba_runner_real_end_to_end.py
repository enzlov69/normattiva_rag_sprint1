from runtime.final_aba_runner_real_invoker import FederatedRunnerRealInvoker
from runtime.final_aba_runtime_handoff_service import FinalABARuntimeHandoffService


def _request():
    return {
        "request_id": "req_400",
        "case_id": "case_400",
        "trace_id": "trace_400",
        "api_version": "1.0",
        "caller_module": "A0_FASE0",
        "target_module": "B_REAL_FEDERATED_RUNNER",
        "timestamp": "2026-03-20T14:00:00Z",
        "status": "READY_FOR_LEVEL_B",
        "warnings": [],
        "errors": [],
        "blocks": [],
        "payload": {
            "documentary_goal": "retrieve documentary packet only",
            "domain_code": "ENTI_LOCALI",
            "m07_mode": "SUPPORT_ONLY",
        },
        "audit": {"trail_events": []},
        "shadow": {"fragments": []},
    }


def _runner_transport(request):
    return {
        "request_id": request["request_id"],
        "case_id": request["case_id"],
        "trace_id": request["trace_id"],
        "api_version": request["api_version"],
        "responder_module": "B_REAL_FEDERATED_RUNNER",
        "status": "SUCCESS",
        "payload": {
            "documentary_packet": {
                "sources": [{"id": "src_1", "uri": "urn:test:src_1"}],
                "norm_units": [{"id": "nu_1", "article": "1"}],
                "citations_valid": [{"id": "cit_1", "article": "1"}],
                "citations_blocked": [],
                "vigenza_records": [{"id": "vig_1", "status": "VIGENTE"}],
                "cross_reference_records": [{"id": "xref_1", "status": "RESOLVED"}],
                "coverage_assessment": {"coverage_status": "ADEQUATE", "critical_gap_flag": False},
                "warnings": [],
                "errors": [],
                "blocks": [],
                "shadow_fragment": {"trace_id": request["trace_id"], "runner_call": "executed"},
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": request["timestamp"],
    }


def test_end_to_end_real_roundtrip_keeps_level_a_in_charge():
    real_invoker = FederatedRunnerRealInvoker(transport=_runner_transport)
    service = FinalABARuntimeHandoffService(mode="real", real_invoker=real_invoker)

    result = service.handle(_request())

    assert result["status"] == "SUCCESS"
    assert result["request_id"] == "req_400"
    assert result["case_id"] == "case_400"
    assert result["trace_id"] == "trace_400"
    assert result["payload"]["level_b_documentary_only"] is True
    assert result["payload"]["opponibility_status"] == "NOT_OPPONIBLE_OUTSIDE_LEVEL_A"
    assert result["payload"]["level_a_next_step"] == "M07_LPR_GOVERNED_BY_LEVEL_A"
    assert result["blocks"] == []
    assert result["errors"] == []
    assert result["audit"]["trail_events"]
    assert result["shadow"]["fragments"]
