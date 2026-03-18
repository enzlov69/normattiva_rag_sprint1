from runtime.final_ab_runtime_handoff_service import FinalABRuntimeHandoffService
from runtime.final_ab_runner_raw_validator import FinalABRunnerRawValidator

def make_minimal_valid_raw():
    return {
        "sources": [],
        "norm_units": [],
        "citations_valid": [],
        "citations_blocked": [],
        "vigenza_records": [],
        "cross_reference_records": [],
        "coverage_assessment": None,
        "warnings": [],
        "errors": [],
        "blocks": [],
        "shadow_fragment": {"executed_modules": ["B10", "B15"], "technical_notes": []}
    }



class FakeRunnerInvoker:
    def __init__(self, raw_output):
        self.raw_output = raw_output

    def invoke(self, request_envelope):
        return self.raw_output


class FakeResponseMapper:
    def __init__(self):
        self.called = False

    def map(self, raw_output, request_envelope=None, validation_result=None):
        self.called = True
        return {
            "sources": raw_output.get("sources", []),
            "norm_units": raw_output.get("norm_units", []),
            "citations_valid": raw_output.get("citations_valid", []),
            "citations_blocked": raw_output.get("citations_blocked", []),
            "vigenza_records": raw_output.get("vigenza_records", []),
            "cross_reference_records": raw_output.get("cross_reference_records", []),
            "coverage_assessment": raw_output.get("coverage_assessment"),
            "warnings": raw_output.get("warnings", []),
            "errors": raw_output.get("errors", []),
            "blocks": raw_output.get("blocks", []),
            "shadow_fragment": raw_output.get("shadow_fragment"),
        }


def make_request():
    return {
        "request_id": "req_001",
        "case_id": "case_001",
        "trace_id": "trace_001",
        "api_version": "1.0",
        "caller_module": "A1_OrchestratorePPAV",
        "target_module": "B_RUNTIME_HANDOFF",
        "payload": {"query": "art. 107 TUEL"},
    }


def test_end_to_end_success_passes_through_validator_then_mapper():
    raw = make_minimal_valid_raw()
    mapper = FakeResponseMapper()
    service = FinalABRuntimeHandoffService(
        runner_invoker=FakeRunnerInvoker(raw),
        response_mapper=mapper,
        raw_validator=FinalABRunnerRawValidator(),
    )

    envelope = service.execute(make_request())

    assert envelope["status"] == "SUCCESS"
    assert mapper.called is True
    assert envelope["payload"]["documentary_packet"]["shadow_fragment"] == raw["shadow_fragment"]


def test_end_to_end_blocked_stops_before_mapper_and_propagates_block():
    raw = make_minimal_valid_raw()
    raw["citations_valid"] = [
        {
            "atto_tipo": "D.Lgs.",
            "atto_numero": "267",
            "atto_anno": "2000",
            "articolo": "107",
            "uri_ufficiale": "",
            "stato_vigenza": "VIGENTE_VERIFICATA",
        }
    ]
    mapper = FakeResponseMapper()
    service = FinalABRuntimeHandoffService(
        runner_invoker=FakeRunnerInvoker(raw),
        response_mapper=mapper,
        raw_validator=FinalABRunnerRawValidator(),
    )

    envelope = service.execute(make_request())

    assert envelope["status"] == "BLOCKED"
    assert mapper.called is False
    assert any(block["block_code"] == "CITATION_INCOMPLETE" for block in envelope["blocks"])


def test_end_to_end_rejected_for_scope_violation_stops_before_mapper():
    raw = make_minimal_valid_raw()
    raw["output_authorized"] = True
    mapper = FakeResponseMapper()
    service = FinalABRuntimeHandoffService(
        runner_invoker=FakeRunnerInvoker(raw),
        response_mapper=mapper,
        raw_validator=FinalABRunnerRawValidator(),
    )

    envelope = service.execute(make_request())

    assert envelope["status"] == "REJECTED"
    assert mapper.called is False
    assert any(block["block_code"] == "RAG_SCOPE_VIOLATION" for block in envelope["blocks"])
