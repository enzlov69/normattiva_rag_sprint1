from runtime.m07_documentary_support_module_registry import (
    get_m07_documentary_support_registry_snapshot,
)
from runtime.m07_documentary_support_orchestrator import (
    orchestrate_m07_documentary_support,
)


def test_acceptance_full_local_cycle_success() -> None:
    def fake_transport(_: dict) -> dict:
        return {
            "request_id": "req_5001",
            "case_id": "case_5001",
            "trace_id": "trace_5001",
            "api_version": "2.0",
            "responder_module": "B16_M07SupportLayer",
            "status": "SUCCESS",
            "payload": {
                "documentary_packet": {
                    "source_ids": ["source_tuel_267_2000"],
                    "norm_unit_ids": ["normunit_art107"],
                    "support_only_flag": True,
                    "m07_evidence_pack": {
                        "record_id": "rec_m07_5001",
                        "record_type": "M07EvidencePack",
                        "m07_pack_id": "m07pack_5001",
                        "case_id": "case_5001",
                        "source_ids": ["source_tuel_267_2000"],
                        "norm_unit_ids": ["normunit_art107"],
                        "ordered_reading_sequence": [],
                        "annex_refs": [],
                        "crossref_refs": [],
                        "coverage_ref_id": "cov_5001",
                        "missing_elements": [],
                        "m07_support_status": "READY_FOR_HUMAN_READING",
                        "human_completion_required": True,
                        "created_at": "2026-03-19T20:00:00Z",
                        "updated_at": "2026-03-19T20:00:00Z",
                        "schema_version": "1.0",
                        "record_version": 1,
                        "source_layer": "B",
                        "trace_id": "trace_5001",
                        "active_flag": True,
                    },
                }
            },
            "warnings": [],
            "errors": [],
            "blocks": [],
            "timestamp": "2026-03-19T20:00:01Z",
        }

    envelope = orchestrate_m07_documentary_support(
        transport=fake_transport,
        session_id="sess_5001",
        request_id="req_5001",
        case_id="case_5001",
        trace_id="trace_5001",
        timestamp="2026-03-19T20:00:00Z",
        caller_module="A1_OrchestratorePPAV",
        goal_istruttorio="supporto documentale M07 su art. 107 TUEL",
        domain_target="enti_locali",
        query_text="articolo 107 TUEL competenze gestionali",
        source_priority=["corpus_governato", "fonti_ufficiali"],
    )

    snapshot = get_m07_documentary_support_registry_snapshot()

    assert envelope["orchestration_status"] == "SUCCESS"
    assert envelope["resolved_module_id"] == "A_M07_DOCUMENTARY_SUPPORT_ADAPTER"
    assert envelope["dispatch_mode"] == "MANUAL_LEVEL_A_ONLY"
    assert envelope["target_module"] == "B16_M07SupportLayer"
    assert envelope["response_consumption"]["m07_evidence_pack_present"] is True

    assert envelope["manual_level_a_only"] is True
    assert envelope["runner_federated_touched"] is False
    assert snapshot["runner_federated_touched"] is False
    assert snapshot["decision_enabled"] is False
    assert snapshot["output_authorization_enabled"] is False