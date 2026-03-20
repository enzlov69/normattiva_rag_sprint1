from runtime.federated_runner_live_observability import append_live_observability


def _request() -> dict:
    return {
        "request_id": "REQ-OBS-001",
        "case_id": "CASE-OBS-001",
        "trace_id": "TRACE-OBS-001",
        "timestamp": "2026-03-20T09:00:00Z",
        "status": "READY_FOR_LEVEL_B",
        "payload": {"query_pack": {"topic": "tuel"}},
        "warnings": [],
        "errors": [],
        "blocks": [],
    }


def _response() -> dict:
    return {
        "request_id": "REQ-OBS-001",
        "case_id": "CASE-OBS-001",
        "trace_id": "TRACE-OBS-001",
        "timestamp": "2026-03-20T09:00:02Z",
        "api_version": "v1",
        "responder_module": "federated_runner",
        "status": "SUCCESS",
        "warnings": [],
        "errors": [],
        "blocks": [],
        "audit": {"trail_events": []},
        "shadow": {"fragments": []},
        "payload": {
            "documentary_packet": {
                "sources": [{"uri": "https://normattiva.it/test"}],
                "norm_units": [{"article": "1"}],
                "citations_valid": [{"article": "1"}],
                "citations_blocked": [],
                "vigenza_records": [{"state": "vigente"}],
                "cross_reference_records": [{"target": "art. 2"}],
                "coverage_assessment": {"critical_gap_flag": False},
                "warnings": [],
                "errors": [],
                "blocks": [],
                "shadow_fragment": {"query_hash": "abc123"},
            },
            "level_b_documentary_only": True,
            "opponibility_status": "NOT_OPPONIBLE_OUTSIDE_LEVEL_A",
            "level_a_next_step": "M07_LPR_GOVERNED_BY_LEVEL_A",
        },
    }


def test_append_live_observability_adds_payload_audit_and_shadow_evidence():
    enriched = append_live_observability(
        request_envelope=_request(),
        response_envelope=_response(),
        transport_name="federated_runner_live_transport",
        transport_endpoint="https://runner.example.local/api/live?token=secret",
        live_mode=True,
    )

    live = enriched["payload"]["live_observability"]
    assert live["live_path_observed"] is True
    assert live["transport_name"] == "federated_runner_live_transport"
    assert live["transport_endpoint_redacted"] == "https://runner.example.local/api/live?[REDACTED]"
    assert live["request_identity"]["completeness"] == "COMPLETE"
    assert live["response_identity"]["completeness"] == "COMPLETE"
    assert live["documentary_summary"]["sources_count"] == 1
    assert live["documentary_summary"]["documentary_only"] is True

    assert enriched["audit"]["trail_events"][-1]["event"] == "LIVE_PATH_OBSERVED_REQUEST_RESPONSE"
    assert enriched["shadow"]["fragments"][-1]["kind"] == "live_observability"
