from runtime.m07_documentary_support_adapter import (
    consume_m07_documentary_support_response,
    run_m07_documentary_support_exchange,
)


def test_adapter_propagates_blocked_response() -> None:
    response_payload = {
        "request_id": "req_2001",
        "case_id": "case_2001",
        "trace_id": "trace_2001",
        "api_version": "2.0",
        "responder_module": "B16_M07SupportLayer",
        "status": "BLOCKED",
        "payload": {
            "documentary_packet": {
                "source_ids": [],
                "norm_unit_ids": [],
                "support_only_flag": True
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [
            {
                "block_id": "blk_2001",
                "case_id": "case_2001",
                "block_code": "CITATION_INCOMPLETE",
                "block_category": "CITATION",
                "block_severity": "CRITICAL",
                "origin_module": "B15_CitationBuilder",
                "block_reason": "citazione incompleta",
                "block_status": "OPEN"
            }
        ],
        "timestamp": "2026-03-19T18:10:01Z"
    }

    consumed = consume_m07_documentary_support_response(response_payload)

    assert consumed["adapter_status"] == "BLOCKED"
    assert len(consumed["blocks"]) == 1
    assert consumed["blocks"][0]["block_code"] == "CITATION_INCOMPLETE"
    assert consumed["can_close_m07"] is False


def test_adapter_propagates_degraded_response() -> None:
    response_payload = {
        "request_id": "req_2002",
        "case_id": "case_2002",
        "trace_id": "trace_2002",
        "api_version": "2.0",
        "responder_module": "B16_M07SupportLayer",
        "status": "DEGRADED",
        "payload": {
            "documentary_packet": {
                "source_ids": ["source_1"],
                "norm_unit_ids": ["unit_1"],
                "support_only_flag": True
            }
        },
        "warnings": [
            {
                "warning_code": "VIGENZA_PARTIAL",
                "warning_message": "controllo vigenza parziale"
            }
        ],
        "errors": [],
        "blocks": [],
        "timestamp": "2026-03-19T18:10:01Z"
    }

    consumed = consume_m07_documentary_support_response(response_payload)

    assert consumed["adapter_status"] == "DEGRADED"
    assert len(consumed["warnings"]) == 1
    assert consumed["can_authorize_output"] is False


def test_adapter_runs_transport_without_deciding() -> None:
    request_payload = {
        "request_id": "req_2003",
        "case_id": "case_2003",
        "trace_id": "trace_2003",
        "api_version": "2.0",
        "caller_module": "A1_OrchestratorePPAV",
        "target_module": "B16_M07SupportLayer",
        "timestamp": "2026-03-19T18:10:00Z",
        "payload": {
            "goal_istruttorio": "supporto documentale M07",
            "domain_target": "enti_locali",
            "query_text": "articolo 107 tuel",
            "documentary_scope": {
                "source_priority": ["corpus_governato"],
                "require_official_uri": True,
                "require_vigenza_check": True,
                "require_crossref_check": True,
                "require_coverage_check": True,
                "include_annexes": True
            },
            "m07_context": {
                "m07_opened": True,
                "human_reading_required": True
            },
            "requested_outputs": [
                "documentary_packet",
                "m07_evidence_pack",
                "warnings",
                "errors",
                "blocks",
                "technical_trace"
            ]
        }
    }

    def fake_transport(_: dict) -> dict:
        return {
            "request_id": "req_2003",
            "case_id": "case_2003",
            "trace_id": "trace_2003",
            "api_version": "2.0",
            "responder_module": "B16_M07SupportLayer",
            "status": "SUCCESS_WITH_WARNINGS",
            "payload": {
                "documentary_packet": {
                    "source_ids": ["source_107"],
                    "norm_unit_ids": ["unit_art107"],
                    "support_only_flag": True
                }
            },
            "warnings": [
                {
                    "warning_code": "COVERAGE_PARTIAL",
                    "warning_message": "coverage non piena"
                }
            ],
            "errors": [],
            "blocks": [],
            "timestamp": "2026-03-19T18:10:01Z"
        }

    consumed = run_m07_documentary_support_exchange(
        transport=fake_transport,
        request_payload=request_payload,
    )

    assert consumed["adapter_status"] == "SUCCESS_WITH_WARNINGS"
    assert consumed["decision_fields_detected"] is False
    assert consumed["can_close_m07"] is False
    assert consumed["can_authorize_output"] is False