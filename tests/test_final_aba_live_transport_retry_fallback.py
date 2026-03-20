from __future__ import annotations

from urllib import error

from runtime.federated_runner_live_transport import invoke_transport_with_guarded_fallback


class _FakeResponse:
    def __init__(self, body: str):
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _request_envelope() -> dict:
    return {
        "request_id": "REQ-RETRY-001",
        "case_id": "CASE-RETRY-001",
        "trace_id": "TRACE-RETRY-001",
        "status": "READY",
        "warnings": [],
        "errors": [],
        "blocks": [],
    }


def test_guarded_fallback_returns_blocked_documentary_envelope_on_transport_failure():
    def _transport(_request):
        raise RuntimeError("low level socket failure")

    response = invoke_transport_with_guarded_fallback(
        _request_envelope(),
        transport=_transport,
        transport_name="federated_runner_live_transport",
        transport_endpoint="https://runner.test/live",
        live_mode=True,
    )

    assert response["status"] == "BLOCKED"
    assert "CRITICAL_DOCUMENTARY_BLOCK" in response["blocks"]
    assert "LIVE_TRANSPORT_ERROR" in response["blocks"]
    assert response["payload"]["non_opponibility"]["outside_level_a"] is True
    assert response["payload"]["live_transport"]["fallback_triggered"] is True
    assert response["audit"]["trail_events"][0]["event"] == "live_transport_fallback_triggered"
    assert response["shadow"]["fragments"][0]["kind"] == "live_transport_fallback"


def test_guarded_fallback_rejects_forbidden_level_b_fields_even_when_response_is_json():
    def _transport(_request):
        return {
            "status": "OK",
            "warnings": [],
            "errors": [],
            "blocks": [],
            "payload": {
                "documentary_packet": {
                    "sources": [],
                    "normative_units": [],
                    "citations": [],
                    "incomplete_citations": [],
                    "vigenza_status": "CONFIRMED",
                    "rinvii_status": "RESOLVED",
                    "coverage": "ADEQUATE",
                }
            },
            "final_decision": "GO",
        }

    response = invoke_transport_with_guarded_fallback(
        _request_envelope(),
        transport=_transport,
        transport_name="federated_runner_live_transport",
        transport_endpoint="https://runner.test/live",
        live_mode=True,
    )

    assert response["status"] == "BLOCKED"
    assert any("Forbidden Level B fields" in err for err in response["errors"])
    assert response["payload"]["documentary_evidence_matrix"]["non_opponible_outside_level_a"] is True
