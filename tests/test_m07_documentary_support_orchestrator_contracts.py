from runtime.m07_documentary_support_orchestrator import (
    orchestrate_m07_documentary_support,
)


def test_orchestrator_success_contract() -> None:
    def fake_transport(_: dict) -> dict:
        return {
            "request_id": "req_4001",
            "case_id": "case_4001",
            "trace_id": "trace_4001",
            "api_version": "2.0",
            "responder_module": "B16_M07SupportLayer",
            "status": "SUCCESS",
            "payload": {
                "documentary_packet": {
                    "source_ids": ["source_tuel_267_2000"],
                    "norm_unit_ids": ["normunit_art107"],
                    "support_only_flag": True,
                    "m07_evidence_pack": {
                        "record_id": "rec_m07_4001",
                        "record_type": "M07EvidencePack",
                        "m07_pack_id": "m07pack_4001",
                        "case_id": "case_4001",
                        "source_ids": ["source_tuel_267_2000"],
                        "norm_unit_ids": ["normunit_art107"],
                        "ordered_reading_sequence": [],
                        "annex_refs": [],
                        "crossref_refs": [],
                        "coverage_ref_id": "cov_4001",
                        "missing_elements": [],
                        "m07_support_status": "READY_FOR_HUMAN_READING",
                        "human_completion_required": True,
                        "created_at": "2026-03-19T19:00:00Z",
                        "updated_at": "2026-03-19T19:00:00Z",
                        "schema_version": "1.0",
                        "record_version": 1,
                        "source_layer": "B",
                        "trace_id": "trace_4001",
                        "active_flag": True
                    }
                }
            },
            "warnings": [],
            "errors": [],
            "blocks": [],
            "timestamp": "2026-03-19T19:00:01Z"
        }

    envelope = orchestrate_m07_documentary_support(
        transport=fake_transport,
        session_id="sess_4001",
        request_id="req_4001",
        case_id="case_4001",
        trace_id="trace_4001",
        timestamp="2026-03-19T19:00:00Z",
        caller_module="A1_OrchestratorePPAV",
        goal_istruttorio="supporto documentale M07 su art. 107 TUEL",
        domain_target="enti_locali",
        query_text="articolo 107 TUEL competenze gestionali",
        source_priority=["corpus_governato", "fonti_ufficiali"],
        reading_focus=["articoli", "commi", "rinvii"],
        metadata_filters={"ente_target": "Comune di Cerda"},
        notes="orchestrazione locale cantiere m07",
    )

    assert envelope["session_id"] == "sess_4001"
    assert envelope["orchestration_status"] == "SUCCESS"
    assert envelope["manual_level_a_only"] is True
    assert envelope["runner_federated_touched"] is False
    assert envelope["can_close_m07"] is False
    assert envelope["can_authorize_output"] is False
    assert envelope["response_consumption"]["m07_evidence_pack_present"] is True