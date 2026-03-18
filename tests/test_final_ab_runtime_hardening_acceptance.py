from dataclasses import dataclass

import pytest

from runtime.final_ab_runtime_handoff_service import FinalABRuntimeHandoffService


class DummyRunner:
    def __init__(self, raw_response):
        self.raw_response = raw_response

    def invoke(self, _runner_request):
        return self.raw_response


class TrackingMapper:
    def __init__(self, mapped_response):
        self.mapped_response = mapped_response
        self.called = False

    def map(self, raw_output, request_envelope=None, validation_result=None):
        self.called = True
        return self.mapped_response


@dataclass
class RawValidationDataclassLike:
    status: str
    warnings: list
    errors: list
    blocks: list
    validated_raw_payload: dict


@pytest.mark.parametrize(
    "target_module",
    ["level_b_runtime_handoff", "B_RUNTIME_HANDOFF", "B_Runtime"],
)
def test_accepts_legacy_and_runtime_targets_without_mismatch(target_module):
    service = FinalABRuntimeHandoffService(
        runner_invoker=DummyRunner(raw_response={"warnings": [], "errors": [], "blocks": []}),
        raw_validator=lambda _raw: {"status": "SUCCESS", "warnings": [], "errors": [], "blocks": []},
        response_mapper=lambda _raw: {"sources": [], "shadow_fragment": {"trace_id": "t", "executed_modules": ["m"]}},
    )

    result = service.execute(
        {
            "request_id": "req_01",
            "case_id": "case_01",
            "trace_id": "trace_01",
            "api_version": "1.0",
            "target_module": target_module,
            "payload": {"query": "art. 107"},
        }
    )

    assert result["status"] == "SUCCESS"
    assert not any(err.get("code") == "TARGET_MODULE_MISMATCH" for err in result["errors"])


def test_invalid_target_stays_rejected_with_legacy_codes():
    service = FinalABRuntimeHandoffService(
        runner_invoker=DummyRunner(raw_response={"warnings": [], "errors": [], "blocks": []}),
        raw_validator=lambda _raw: {"status": "SUCCESS", "warnings": [], "errors": [], "blocks": []},
        response_mapper=lambda _raw: {"sources": [], "shadow_fragment": {"trace_id": "t", "executed_modules": ["m"]}},
    )

    result = service.execute(
        {
            "request_id": "req_02",
            "case_id": "case_02",
            "trace_id": "trace_02",
            "api_version": "1.0",
            "target_module": "invalid_target",
            "payload": {"query": "x"},
        }
    )

    assert result["status"] == "REJECTED"
    assert result["errors"][0]["code"] == "TARGET_MODULE_MISMATCH"
    assert result["blocks"][0]["block_code"] == "RAG_SCOPE_VIOLATION"


def test_stop_before_mapper_when_structured_raw_validation_is_blocked():
    mapper = TrackingMapper(mapped_response={"sources": []})
    service = FinalABRuntimeHandoffService(
        runner_invoker=DummyRunner(raw_response={"warnings": [], "errors": [], "blocks": []}),
        raw_validator=lambda _raw: RawValidationDataclassLike(
            status="BLOCKED",
            warnings=[],
            errors=[],
            blocks=[{"block_code": "CITATION_INCOMPLETE", "code": "CITATION_INCOMPLETE"}],
            validated_raw_payload={"warnings": [], "errors": [], "blocks": []},
        ),
        response_mapper=mapper,
    )

    result = service.execute(
        {
            "request_id": "req_03",
            "case_id": "case_03",
            "trace_id": "trace_03",
            "api_version": "1.0",
            "target_module": "B_RUNTIME_HANDOFF",
            "payload": {"query": "x"},
        }
    )

    assert result["status"] == "BLOCKED"
    assert mapper.called is False
    assert any(block.get("block_code") == "CITATION_INCOMPLETE" for block in result["blocks"])


def test_post_mapper_gate_runs_for_envelope_based_flow():
    mapper = TrackingMapper(
        mapped_response={
            "request_id": "req_04",
            "case_id": "case_04",
            "trace_id": "trace_04",
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
                    "shadow_fragment": {"trace_id": "trace_04", "executed_modules": ["mapper"]},
                    "audit_fragment": {"trace_id": "trace_04", "event_type": "response_mapped"},
                }
            },
        }
    )

    service = FinalABRuntimeHandoffService(
        runner_invoker=DummyRunner(raw_response={"warnings": [], "errors": [], "blocks": []}),
        raw_validator=lambda _raw: {"status": "SUCCESS", "warnings": [], "errors": [], "blocks": []},
        response_mapper=mapper,
    )

    result = service.execute(
        {
            "request_id": "req_04",
            "case_id": "case_04",
            "trace_id": "trace_04",
            "api_version": "1.0",
            "target_module": "B_Runtime",
            "payload": {"query": "x"},
        }
    )

    assert result["status"] == "SUCCESS"
    assert mapper.called is True
    assert result["payload"]["response_envelope_gate_report"]["guard_applied"] is True
