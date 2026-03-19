from runtime.final_ab_runner_real_invoker import FinalABRunnerRealInvoker
from runtime.final_ab_runtime_handoff_service import FinalABRuntimeHandoffService


def _base_request() -> dict:
    return {
        "request_id": "req_runtime_e2e_001",
        "case_id": "case_runtime_e2e_001",
        "trace_id": "trace_runtime_e2e_001",
        "api_version": "1.0",
        "caller_module": "A1_OrchestratorePPAV",
        "target_module": "RAG_NORMATIVO_GOVERNATO_E_FEDERATO",
        "payload": {
            "query_text": "art. 107 TUEL",
            "domain_target": "tuel",
            "top_k": 3
        }
    }


def _runtime_mapper(raw_output, request_envelope=None, validation_result=None):
    payload = raw_output["payload"]
    return {
        "request_id": request_envelope["request_id"],
        "case_id": request_envelope["case_id"],
        "trace_id": request_envelope["trace_id"],
        "api_version": request_envelope["api_version"],
        "responder_module": "B21_ResponseMapper",
        "status": raw_output.get("status", "SUCCESS"),
        "timestamp": "2026-03-19T11:10:00Z",
        "warnings": raw_output.get("warnings", []),
        "errors": raw_output.get("errors", []),
        "blocks": raw_output.get("blocks", []),
        "payload": {
            "documentary_packet": {
                "sources": payload["sources"],
                "norm_units": payload["norm_units"],
                "citations_valid": payload["citations_valid"],
                "citations_blocked": payload["citations_blocked"],
                "vigenza_records": payload["vigenza_records"],
                "cross_reference_records": payload["cross_reference_records"],
                "coverage_assessment": payload["coverage_assessment"],
                "warnings": payload["warnings"],
                "errors": payload["errors"],
                "blocks": payload["blocks"],
                "shadow_fragment": payload["shadow_fragment"],
                "audit_fragment": {
                    "trace_id": request_envelope["trace_id"],
                    "event_type": "response_mapped"
                }
            }
        }
    }


def test_runtime_end_to_end_valid_flow_remains_non_decisional_and_non_opponible() -> None:
    def runner(_runner_request):
        return {
            "status": "SUCCESS",
            "warnings": [],
            "errors": [],
            "blocks": [],
            "payload": {
                "sources": [{"source_id": "src_107"}],
                "norm_units": [{"norm_unit_id": "art_107"}],
                "citations_valid": [],
                "citations_blocked": [],
                "vigenza_records": [],
                "cross_reference_records": [],
                "coverage_assessment": {"status": "ADEQUATE"},
                "warnings": [],
                "errors": [],
                "blocks": [],
                "shadow_fragment": {"trace_id": "trace_runtime_e2e_001", "executed_modules": ["runner"]}
            }
        }

    service = FinalABRuntimeHandoffService(
        invocation_port=FinalABRunnerRealInvoker(runner_callable=runner),
        response_mapper=_runtime_mapper,
    )

    result = service.execute(_base_request())

    assert result["status"] == "SUCCESS_WITH_WARNINGS"
    assert "final_decision" not in str(result["payload"]).lower()
    assert "output_authorized" not in str(result["payload"]).lower()
    assert result["payload"]["response_envelope_gate_report"]["guard_applied"] is True


def test_runtime_end_to_end_propagates_critical_blocks() -> None:
    def runner(_runner_request):
        return {
            "status": "BLOCKED",
            "warnings": [],
            "errors": [],
            "blocks": [{"block_code": "VIGENZA_UNCERTAIN", "severity": "CRITICAL", "reason": "essential"}],
            "payload": {
                "sources": [{"source_id": "src_107"}],
                "norm_units": [{"norm_unit_id": "art_107"}],
                "citations_valid": [],
                "citations_blocked": [],
                "vigenza_records": [],
                "cross_reference_records": [],
                "coverage_assessment": {"status": "INADEQUATE"},
                "warnings": [],
                "errors": [],
                "blocks": [],
                "shadow_fragment": {"trace_id": "trace_runtime_e2e_001", "executed_modules": ["runner"]}
            }
        }

    service = FinalABRuntimeHandoffService(
        invocation_port=FinalABRunnerRealInvoker(runner_callable=runner),
        raw_validator=lambda raw: {
            "status": raw["status"],
            "warnings": raw["warnings"],
            "errors": raw["errors"],
            "blocks": raw["blocks"]
        },
        response_mapper=_runtime_mapper,
    )

    result = service.execute(_base_request())

    assert result["status"] == "BLOCKED"
    assert any(block.get("code") == "VIGENZA_UNCERTAIN" or block.get("block_code") == "VIGENZA_UNCERTAIN" for block in result["blocks"])


def test_runtime_end_to_end_rejects_m07_closure_from_documentary_runtime() -> None:
    def runner(_runner_request):
        return {
            "payload": {
                "sources": [{"source_id": "src_m07"}],
                "norm_units": [{"norm_unit_id": "nu_m07"}],
                "citations_valid": [],
                "citations_blocked": [],
                "vigenza_records": [],
                "cross_reference_records": [],
                "coverage_assessment": {"status": "ADEQUATE"},
                "warnings": [],
                "errors": [],
                "blocks": [],
                "shadow_fragment": {"trace_id": "trace_runtime_e2e_001", "executed_modules": ["runner"]},
                "m07_closed": True
            }
        }

    service = FinalABRuntimeHandoffService(
        invocation_port=FinalABRunnerRealInvoker(runner_callable=runner)
    )

    result = service.execute(_base_request())

    assert result["status"] == "REJECTED"
    assert any(block.get("anomaly_code") == "M07_SCOPE_VIOLATION" or block.get("block_code") == "RAG_SCOPE_VIOLATION" for block in result["blocks"])
