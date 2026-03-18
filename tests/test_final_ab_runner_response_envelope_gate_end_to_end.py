from runtime.final_ab_runtime_handoff_service import FinalABRuntimeHandoffService


class DummyRunnerInvoker:
    def invoke(self, request_envelope):
        return {
            "request_id": request_envelope["request_id"],
            "case_id": request_envelope["case_id"],
            "trace_id": request_envelope["trace_id"],
            "status": "BLOCKED",
            "warnings": [],
            "errors": [],
            "blocks": [
                {
                    "code": "VIGENZA_UNCERTAIN",
                    "severity": "CRITICAL",
                    "reason": "vigore non verificabile su punto essenziale",
                }
            ],
            "payload": {
                "runner_payload": "black-box",
                "shadow_fragment": {
                    "trace_id": request_envelope["trace_id"],
                    "executed_modules": ["runner"],
                },
            },
        }


class DummyRawValidator:
    def validate(self, raw_response):
        return {
            "status": raw_response["status"],
            "warnings": raw_response["warnings"],
            "errors": raw_response["errors"],
            "blocks": raw_response["blocks"],
            "audit_fragment": {
                "trace_id": raw_response["trace_id"],
                "event_type": "raw_validation_completed",
            },
            "shadow_fragment": {
                "trace_id": raw_response["trace_id"],
                "executed_modules": ["raw_validator"],
            },
        }


class DummyResponseMapper:
    def map_response(self, raw_response, raw_validation_result=None, request_envelope=None):
        return {
            "request_id": raw_response["request_id"],
            "case_id": raw_response["case_id"],
            "trace_id": raw_response["trace_id"],
            "api_version": "1.0",
            "responder_module": "B21_ResponseMapper",
            "status": "SUCCESS",
            "timestamp": "2026-03-18T10:00:00Z",
            "warnings": [],
            "errors": [],
            "blocks": [],
            "payload": {
                "documentary_packet": {
                    "sources": [{"source_id": "src-1"}],
                    "norm_units": [{"norm_unit_id": "nu-1"}],
                    "citations_valid": [{"citation_id": "cit-1"}],
                    "citations_blocked": [],
                    "vigenza_records": [{"vigenza_id": "vig-1"}],
                    "cross_reference_records": [],
                    "coverage_assessment": {"coverage_id": "cov-1"},
                    "warnings": [],
                    "errors": [],
                    "blocks": [],
                    "shadow_fragment": {
                        "trace_id": raw_response["trace_id"],
                        "executed_modules": ["response_mapper"],
                    },
                }
            },
        }


def _request():
    return {
        "request_id": "req-003",
        "case_id": "case-003",
        "trace_id": "trace-003",
        "api_version": "1.0",
        "caller_module": "A1_Orchestrator",
        "target_module": "B_Runtime",
        "timestamp": "2026-03-18T10:00:00Z",
        "payload": {"query": "art. 191 TUEL"},
    }


def test_handoff_service_applies_post_mapper_gate_and_preserves_raw_blocks():
    service = FinalABRuntimeHandoffService(
        runner_invoker=DummyRunnerInvoker(),
        raw_validator=DummyRawValidator(),
        response_mapper=DummyResponseMapper(),
    )

    result = service.handoff(_request())

    assert result["status"] == "BLOCKED"
    assert any(block["code"] == "VIGENZA_UNCERTAIN" for block in result["blocks"])
    assert any(error["code"] == "CRITICAL_BLOCK_LOSS_DETECTED" for error in result["errors"])
    assert result["payload"]["response_envelope_gate_report"]["guard_applied"] is True


class MapperMissingAuditShadow:
    def map_response(self, raw_response, raw_validation_result=None, request_envelope=None):
        return {
            "request_id": raw_response["request_id"],
            "case_id": raw_response["case_id"],
            "trace_id": raw_response["trace_id"],
            "api_version": "1.0",
            "responder_module": "B21_ResponseMapper",
            "status": "BLOCKED",
            "timestamp": "2026-03-18T10:00:00Z",
            "warnings": [],
            "errors": [],
            "blocks": raw_response["blocks"],
            "payload": {
                "documentary_packet": {
                    "sources": [{"source_id": "src-1"}],
                    "norm_units": [{"norm_unit_id": "nu-1"}],
                    "citations_valid": [{"citation_id": "cit-1"}],
                    "citations_blocked": [],
                    "vigenza_records": [{"vigenza_id": "vig-1"}],
                    "cross_reference_records": [],
                    "coverage_assessment": {"coverage_id": "cov-1"},
                    "warnings": [],
                    "errors": [],
                    "blocks": raw_response["blocks"],
                    "shadow_fragment": {},
                }
            },
        }


def test_handoff_service_blocks_critical_response_when_audit_shadow_are_incomplete():
    service = FinalABRuntimeHandoffService(
        runner_invoker=DummyRunnerInvoker(),
        raw_validator=DummyRawValidator(),
        response_mapper=MapperMissingAuditShadow(),
    )

    result = service.handoff(_request())

    assert result["status"] == "BLOCKED"
    assert any(block["code"] == "AUDIT_INCOMPLETE" for block in result["blocks"])
    assert any(error["code"] in {"AUDIT_FRAGMENT_MISSING", "SHADOW_FRAGMENT_MISSING"} for error in result["errors"])
