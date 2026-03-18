from runtime.final_ab_runtime_handoff_service import FinalABRuntimeHandoffService


class RunnerEcho:
    def __init__(self, raw):
        self.raw = raw

    def invoke(self, request_envelope):
        payload = dict(self.raw)
        payload.setdefault("request_id", request_envelope.get("request_id"))
        payload.setdefault("case_id", request_envelope.get("case_id"))
        payload.setdefault("trace_id", request_envelope.get("trace_id"))
        return payload


class MapperTracker:
    def __init__(self, mapped):
        self.mapped = mapped
        self.called = False

    def map_response(self, raw_response, raw_validation_result=None, request_envelope=None):
        self.called = True
        return self.mapped


class RawValidationObject:
    def __init__(self, status="SUCCESS", blocks=None, validated_raw_payload=None):
        self.status = status
        self.warnings = []
        self.errors = []
        self.blocks = blocks or []
        if validated_raw_payload is not None:
            self.validated_raw_payload = validated_raw_payload


def _request(target_module="B_RUNTIME_HANDOFF"):
    return {
        "request_id": "req_sg",
        "case_id": "case_sg",
        "trace_id": "trace_sg",
        "api_version": "1.0",
        "target_module": target_module,
        "payload": {"query": "art. 191 TUEL"},
    }


def test_constructor_aliases_invocation_port_and_runner_invoker_are_backward_compatible():
    raw = {"warnings": [], "errors": [], "blocks": []}
    mapper = lambda _raw: {"sources": [], "shadow_fragment": {"trace_id": "trace_sg", "executed_modules": ["m"]}}
    validator = lambda _raw: {"status": "SUCCESS", "warnings": [], "errors": [], "blocks": []}

    service_a = FinalABRuntimeHandoffService(
        invocation_port=RunnerEcho(raw),
        response_mapper=mapper,
        raw_validator=validator,
    )
    service_b = FinalABRuntimeHandoffService(
        runner_invoker=RunnerEcho(raw),
        response_mapper=mapper,
        raw_validator=validator,
    )

    result_a = service_a.execute(_request())
    result_b = service_b.execute(_request())

    assert result_a["status"] == "SUCCESS"
    assert result_b["status"] == "SUCCESS"
    assert result_a["payload"]["documentary_packet"] == result_b["payload"]["documentary_packet"]


def test_raw_validation_object_without_mapping_is_normalized_and_mapper_runs():
    mapper = MapperTracker(
        mapped={
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
            "shadow_fragment": {"trace_id": "trace_sg", "executed_modules": ["mapper"]},
        }
    )

    service = FinalABRuntimeHandoffService(
        runner_invoker=RunnerEcho({"warnings": [], "errors": [], "blocks": []}),
        raw_validator=lambda _raw: RawValidationObject(status="SUCCESS"),
        response_mapper=mapper,
    )

    result = service.execute(_request("level_b_runtime_handoff"))

    assert result["status"] == "SUCCESS"
    assert mapper.called is True


def test_structured_blocked_raw_validation_object_stops_before_mapper():
    mapper = MapperTracker(mapped={"sources": []})
    service = FinalABRuntimeHandoffService(
        runner_invoker=RunnerEcho({"warnings": [], "errors": [], "blocks": []}),
        raw_validator=lambda _raw: RawValidationObject(
            status="REJECTED",
            blocks=[{"block_code": "RAG_SCOPE_VIOLATION", "code": "RAG_SCOPE_VIOLATION"}],
            validated_raw_payload={"warnings": [], "errors": [], "blocks": []},
        ),
        response_mapper=mapper,
    )

    result = service.execute(_request("B_Runtime"))

    assert result["status"] == "REJECTED"
    assert mapper.called is False
    assert any(block.get("block_code") == "RAG_SCOPE_VIOLATION" for block in result["blocks"])


def test_gate_preserves_critical_block_without_status_downgrade_on_envelope_flow():
    mapper = MapperTracker(
        mapped={
            "request_id": "req_sg",
            "case_id": "case_sg",
            "trace_id": "trace_sg",
            "api_version": "1.0",
            "responder_module": "B21_ResponseMapper",
            "status": "SUCCESS",
            "timestamp": "2026-03-18T10:00:00Z",
            "warnings": [],
            "errors": [],
            "blocks": [],
            "payload": {
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
                    "shadow_fragment": {"trace_id": "trace_sg", "executed_modules": ["mapper"]},
                },
                "audit_fragment": {"trace_id": "trace_sg", "event_type": "response_mapped"},
            },
        }
    )

    service = FinalABRuntimeHandoffService(
        runner_invoker=RunnerEcho(
            {
                "status": "BLOCKED",
                "warnings": [],
                "errors": [],
                "blocks": [{"code": "VIGENZA_UNCERTAIN", "severity": "CRITICAL", "reason": "essential"}],
                "payload": {"shadow_fragment": {"trace_id": "trace_sg", "executed_modules": ["runner"]}},
            }
        ),
        raw_validator=lambda raw: {
            "status": raw["status"],
            "warnings": raw["warnings"],
            "errors": raw["errors"],
            "blocks": raw["blocks"],
        },
        response_mapper=mapper,
    )

    result = service.execute(_request("B_Runtime"))

    assert result["status"] == "BLOCKED"
    assert any(block.get("code") == "VIGENZA_UNCERTAIN" for block in result["blocks"])
    assert any(error.get("code") == "CRITICAL_BLOCK_LOSS_DETECTED" for error in result["errors"])
