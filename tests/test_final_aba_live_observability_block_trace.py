from runtime.federated_runner_live_observability import append_live_observability


def test_block_propagation_state_is_blocks_present_when_packet_blocks_are_propagated():
    request = {
        "request_id": "REQ-BLK-001",
        "case_id": "CASE-BLK-001",
        "trace_id": "TRACE-BLK-001",
        "timestamp": "2026-03-20T09:00:00Z",
        "status": "READY_FOR_LEVEL_B",
        "payload": {},
        "warnings": [],
        "errors": [],
        "blocks": [],
    }

    response = {
        "request_id": "REQ-BLK-001",
        "case_id": "CASE-BLK-001",
        "trace_id": "TRACE-BLK-001",
        "timestamp": "2026-03-20T09:00:02Z",
        "api_version": "v1",
        "responder_module": "federated_runner",
        "status": "BLOCKED",
        "warnings": [],
        "errors": [],
        "blocks": ["CRITICAL_DOCUMENTARY_BLOCK", "M07_REQUIRED"],
        "audit": {"trail_events": []},
        "shadow": {"fragments": []},
        "payload": {
            "documentary_packet": {
                "sources": [],
                "norm_units": [],
                "citations_valid": [],
                "citations_blocked": [],
                "vigenza_records": [],
                "cross_reference_records": [],
                "coverage_assessment": {"critical_gap_flag": True},
                "warnings": [],
                "errors": [],
                "blocks": ["CRITICAL_DOCUMENTARY_BLOCK", "M07_REQUIRED"],
                "shadow_fragment": {"query_hash": "blk001"},
            },
            "level_b_documentary_only": True,
            "opponibility_status": "NOT_OPPONIBLE_OUTSIDE_LEVEL_A",
            "level_a_next_step": "M07_LPR_MANDATORY_CONTINUATION_IN_LEVEL_A",
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
    assert live["block_propagation_state"] == "BLOCKS_PRESENT"
    assert live["documentary_summary"]["coverage_critical_gap_flag"] is True
    assert enriched["shadow"]["fragments"][-1]["block_propagation_state"] == "BLOCKS_PRESENT"
