import copy
import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "runtime" / "final_ab_runner_frontdoor.py"
spec = importlib.util.spec_from_file_location("final_ab_runner_frontdoor", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec.loader is not None
spec.loader.exec_module(module)

FinalABRunnerFrontDoor = module.FinalABRunnerFrontDoor
FrontDoorContractError = module.FrontDoorContractError


def _base_request():
    return {
        "request_id": "req_001",
        "case_id": "case_001",
        "trace_id": "trace_001",
        "api_version": "1.0",
        "caller_module": "A1_OrchestratorePPAV",
        "target_module": "B10_HybridRetriever",
        "timestamp": "2026-03-18T09:00:00Z",
        "payload": {
            "runner_payload": {
                "query": "art. 191 TUEL",
                "domain": "tuel",
                "top_k": 5,
            }
        },
    }


def _success_response(request, payload=None, blocks=None):
    return {
        "request_id": request["request_id"],
        "case_id": request["case_id"],
        "trace_id": request["trace_id"],
        "api_version": request["api_version"],
        "responder_module": "B10_HybridRetriever",
        "status": "SUCCESS",
        "payload": payload or {
            "documentary_packet": {
                "sources": [{"source_id": "src_001"}],
                "norm_units": [{"norm_unit_id": "nu_001"}],
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": blocks or [],
        "timestamp": "2026-03-18T09:00:01Z",
    }


def test_frontdoor_accepts_valid_request_and_response():
    request = _base_request()

    def adapter_bridge(incoming_request):
        return _success_response(incoming_request)

    frontdoor = FinalABRunnerFrontDoor(adapter_bridge=adapter_bridge)
    response = frontdoor.execute(request)

    assert response["status"] == "SUCCESS"
    assert response["payload"]["documentary_packet"]["sources"][0]["source_id"] == "src_001"


def test_frontdoor_rejects_incomplete_request_contract():
    request = _base_request()
    del request["case_id"]

    def adapter_bridge(_incoming_request):
        raise AssertionError("Adapter must not be called for invalid request")

    frontdoor = FinalABRunnerFrontDoor(adapter_bridge=adapter_bridge)

    try:
        frontdoor.execute(request)
    except FrontDoorContractError as exc:
        assert "case_id" in str(exc)
    else:
        raise AssertionError("Expected FrontDoorContractError for missing case_id")


def test_frontdoor_rejects_forbidden_level_b_fields():
    request = _base_request()

    def adapter_bridge(incoming_request):
        response = _success_response(
            incoming_request,
            payload={
                "documentary_packet": {"sources": [{"source_id": "src_001"}]},
                "final_decision": "GO",
            },
        )
        return response

    frontdoor = FinalABRunnerFrontDoor(adapter_bridge=adapter_bridge)
    response = frontdoor.execute(request)

    assert response["status"] == "REJECTED"
    assert any(block["block_code"] == "RAG_SCOPE_VIOLATION" for block in response["blocks"])
    assert "rejected_field_paths" in response["payload"]


def test_frontdoor_rejects_m07_closure_attempt():
    request = _base_request()

    def adapter_bridge(incoming_request):
        response = _success_response(
            incoming_request,
            payload={
                "documentary_packet": {"sources": [{"source_id": "src_001"}]},
                "m07_closed": True,
            },
        )
        return response

    frontdoor = FinalABRunnerFrontDoor(adapter_bridge=adapter_bridge)
    response = frontdoor.execute(request)

    assert response["status"] == "REJECTED"
    assert any(block["block_code"] == "RAG_SCOPE_VIOLATION" for block in response["blocks"])


def test_frontdoor_propagates_critical_blocks_without_downgrade():
    request = _base_request()

    def adapter_bridge(incoming_request):
        return _success_response(
            incoming_request,
            blocks=[
                {
                    "block_code": "CITATION_INCOMPLETE",
                    "block_severity": "CRITICAL",
                    "origin_module": "B15_CitationBuilder",
                }
            ],
        )

    frontdoor = FinalABRunnerFrontDoor(adapter_bridge=adapter_bridge)
    response = frontdoor.execute(request)

    assert response["status"] == "BLOCKED"
    assert any(block["block_code"] == "CITATION_INCOMPLETE" for block in response["blocks"])


def test_frontdoor_keeps_runner_payload_semantics_unchanged():
    request = _base_request()
    observed_payload = {}

    def adapter_bridge(incoming_request):
        observed_payload["request_payload"] = copy.deepcopy(incoming_request["payload"]["runner_payload"])
        return _success_response(incoming_request)

    frontdoor = FinalABRunnerFrontDoor(adapter_bridge=adapter_bridge)
    response = frontdoor.execute(request)

    assert response["status"] == "SUCCESS"
    assert observed_payload["request_payload"] == request["payload"]["runner_payload"]
