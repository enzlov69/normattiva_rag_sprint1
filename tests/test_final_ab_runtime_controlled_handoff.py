from runtime.final_ab_runtime_handoff_service import FinalABRuntimeHandoffService


class DummyRunner:
    def invoke(self, _request):
        return {
            "warnings": [{"code": "DOCUMENTARY_ONLY", "message": "support only"}],
            "errors": [],
            "blocks": [],
            "payload": {
                "sources": [{"source_id": "src_runtime_001"}],
                "norm_units": [{"norm_unit_id": "nu_runtime_001"}],
                "citations_valid": [],
                "citations_blocked": [],
                "vigenza_records": [],
                "cross_reference_records": [],
                "coverage_assessment": {"status": "ADEQUATE"},
                "warnings": [],
                "errors": [],
                "blocks": [],
                "shadow_fragment": {"trace_id": "trace_runtime_001", "executed_modules": ["runner"]}
            }
        }


def _request() -> dict:
    return {
        "request_id": "req_runtime_001",
        "case_id": "case_runtime_001",
        "trace_id": "trace_runtime_001",
        "api_version": "1.0",
        "caller_module": "A1_OrchestratorePPAV",
        "target_module": "RAG_NORMATIVO_GOVERNATO_E_FEDERATO",
        "payload": {"query_text": "art. 42 TUEL"}
    }


def _mapper(raw_output, request_envelope=None, validation_result=None):
    payload = raw_output["payload"]
    return {
        "request_id": request_envelope["request_id"],
        "case_id": request_envelope["case_id"],
        "trace_id": request_envelope["trace_id"],
        "api_version": request_envelope["api_version"],
        "responder_module": "B21_ResponseMapper",
        "status": "SUCCESS_WITH_WARNINGS",
        "timestamp": "2026-03-19T11:00:00Z",
        "warnings": raw_output["warnings"],
        "errors": raw_output["errors"],
        "blocks": raw_output["blocks"],
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


def test_runtime_controlled_handoff_tracks_documentary_packet_warnings_audit_and_shadow() -> None:
    service = FinalABRuntimeHandoffService(
        runner_invoker=DummyRunner(),
        raw_validator=lambda raw: {
            "status": "SUCCESS_WITH_WARNINGS",
            "warnings": raw["warnings"],
            "errors": raw["errors"],
            "blocks": raw["blocks"]
        },
        response_mapper=_mapper,
    )

    result = service.execute(_request())

    assert result["status"] == "SUCCESS_WITH_WARNINGS"
    assert result["payload"]["documentary_packet"]["sources"][0]["source_id"] == "src_runtime_001"
    assert result["warnings"][0]["code"] == "DOCUMENTARY_ONLY"
    assert result["payload"]["documentary_packet"]["shadow_fragment"]["trace_id"] == "trace_runtime_001"
    assert result["payload"]["response_envelope_gate_report"]["guard_applied"] is True

