import pytest

from runtime.federated_runner_live_observability import LiveObservabilityError, append_live_observability


def test_non_opponibility_and_level_a_governance_are_preserved_in_live_observability():
    request = {
        "request_id": "REQ-NOPP-001",
        "case_id": "CASE-NOPP-001",
        "trace_id": "TRACE-NOPP-001",
        "timestamp": "2026-03-20T09:00:00Z",
        "status": "READY_FOR_LEVEL_B",
        "payload": {},
        "warnings": [],
        "errors": [],
        "blocks": [],
    }

    response = {
        "request_id": "REQ-NOPP-001",
        "case_id": "CASE-NOPP-001",
        "trace_id": "TRACE-NOPP-001",
        "timestamp": "2026-03-20T09:00:02Z",
        "api_version": "v1",
        "responder_module": "federated_runner",
        "status": "SUCCESS_WITH_WARNINGS",
        "warnings": ["CITATION_INCOMPLETE"],
        "errors": [],
        "blocks": [],
        "audit": {"trail_events": []},
        "shadow": {"fragments": []},
        "payload": {
            "documentary_packet": {
                "sources": [],
                "norm_units": [],
                "citations_valid": [],
                "citations_blocked": [{"reason": "missing_uri"}],
                "vigenza_records": [],
                "cross_reference_records": [],
                "coverage_assessment": {"critical_gap_flag": False},
                "warnings": ["CITATION_INCOMPLETE"],
                "errors": [],
                "blocks": [],
                "shadow_fragment": {"query_hash": "nopp001"},
            },
            "level_b_documentary_only": True,
            "opponibility_status": "NOT_OPPONIBLE_OUTSIDE_LEVEL_A",
            "level_a_next_step": "M07_LPR_GOVERNED_BY_LEVEL_A",
        },
    }

    enriched = append_live_observability(
        request_envelope=request,
        response_envelope=response,
        transport_name="federated_runner_live_transport",
        transport_endpoint="https://runner.example.local/live",
        live_mode=True,
    )

    live = enriched["payload"]["live_observability"]
    assert live["opponibility_status"] == "NOT_OPPONIBLE_OUTSIDE_LEVEL_A"
    assert live["level_a_next_step"] == "M07_LPR_GOVERNED_BY_LEVEL_A"
    assert live["level_b_documentary_only"] is True
    assert enriched["shadow"]["fragments"][-1]["not_opponible_outside_level_a"] is True


def test_transport_endpoint_must_be_string_when_provided():
    with pytest.raises(LiveObservabilityError):
        append_live_observability(
            request_envelope={},
            response_envelope={},
            transport_name="federated_runner_live_transport",
            transport_endpoint=123,
            live_mode=True,
        )
