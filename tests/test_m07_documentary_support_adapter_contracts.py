from runtime.m07_documentary_support_adapter import (
    build_m07_documentary_support_request,
    consume_m07_documentary_support_response,
)


def test_adapter_builds_valid_request() -> None:
    request_payload = build_m07_documentary_support_request(
        request_id="req_1001",
        case_id="case_1001",
        trace_id="trace_1001",
        timestamp="2026-03-19T18:00:00Z",
        goal_istruttorio="supporto documentale M07 su quesito TUEL",
        domain_target="enti_locali",
        query_text="articolo 107 del TUEL",
        source_priority=["corpus_governato", "fonti_ufficiali"],
        reading_focus=["articoli", "commi", "rinvii"],
        metadata_filters={"ente_target": "Comune di Cerda"},
        notes="verifica preparatoria per RAC",
    )

    assert request_payload["api_version"] == "2.0"
    assert request_payload["target_module"] == "B16_M07SupportLayer"
    assert request_payload["payload"]["m07_context"]["m07_opened"] is True
    assert request_payload["payload"]["m07_context"]["human_reading_required"] is True


def test_adapter_consumes_valid_response() -> None:
    response_payload = {
        "request_id": "req_1001",
        "case_id": "case_1001",
        "trace_id": "trace_1001",
        "api_version": "2.0",
        "responder_module": "B16_M07SupportLayer",
        "status": "SUCCESS",
        "payload": {
            "documentary_packet": {
                "source_ids": ["source_tuel_267_2000"],
                "norm_unit_ids": ["normunit_art107"],
                "support_only_flag": True,
                "m07_evidence_pack": {
                    "record_id": "rec_m07_1001",
                    "record_type": "M07EvidencePack",
                    "m07_pack_id": "m07pack_1001",
                    "case_id": "case_1001",
                    "source_ids": ["source_tuel_267_2000"],
                    "norm_unit_ids": ["normunit_art107"],
                    "ordered_reading_sequence": [],
                    "annex_refs": [],
                    "crossref_refs": [],
                    "coverage_ref_id": "cov_1001",
                    "missing_elements": [],
                    "m07_support_status": "READY_FOR_HUMAN_READING",
                    "human_completion_required": True,
                    "created_at": "2026-03-19T18:00:00Z",
                    "updated_at": "2026-03-19T18:00:00Z",
                    "schema_version": "1.0",
                    "record_version": 1,
                    "source_layer": "B",
                    "trace_id": "trace_1001",
                    "active_flag": True
                }
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": "2026-03-19T18:00:01Z"
    }

    consumed = consume_m07_documentary_support_response(response_payload)

    assert consumed["adapter_status"] == "SUCCESS"
    assert consumed["requires_human_m07_completion"] is True
    assert consumed["can_close_m07"] is False
    assert consumed["can_authorize_output"] is False
    assert consumed["documentary_packet"]["support_only_flag"] is True