from runtime.m07_documentary_support_orchestrator import (
    orchestrate_m07_documentary_support,
)


def test_orchestrator_never_enables_decision_or_authorization() -> None:
    def fake_transport(_: dict) -> dict:
        return {
            "request_id": "req_4201",
            "case_id": "case_4201",
            "trace_id": "trace_4201",
            "api_version": "2.0",
            "responder_module": "B16_M07SupportLayer",
            "status": "SUCCESS_WITH_WARNINGS",
            "payload": {
                "documentary_packet": {
                    "source_ids": ["source_1"],
                    "norm_unit_ids": ["unit_1"],
                    "support_only_flag": True,
                    "m07_evidence_pack": {
                        "record_id": "rec_m07_4201",
                        "record_type": "M07EvidencePack",
                        "m07_pack_id": "m07pack_4201",
                        "case_id": "case_4201",
                        "source_ids": ["source_1"],
                        "norm_unit_ids": ["unit_1"],
                        "ordered_reading_sequence": [],
                        "annex_refs": [],
                        "crossref_refs": [],
                        "coverage_ref_id": "cov_4201",
                        "missing_elements": [],
                        "m07_support_status": "READY_FOR_HUMAN_READING",
                        "human_completion_required": True,
                        "created_at": "2026-03-19T19:20:00Z",
                        "updated_at": "2026-03-19T19:20:00Z",
                        "schema_version": "1.0",
                        "record_version": 1,
                        "source_layer": "B",
                        "trace_id": "trace_4201",
                        "active_flag": True
                    }
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
            "timestamp": "2026-03-19T19:20:01Z"
        }

    envelope = orchestrate_m07_documentary_support(
        transport=fake_transport,
        session_id="sess_4201",
        request_id="req_4201",
        case_id="case_4201",
        trace_id="trace_4201",
        timestamp="2026-03-19T19:20:00Z",
        caller_module="A2_CaseClassifier",
        goal_istruttorio="supporto documentale in sola ricognizione",
        domain_target="enti_locali",
        query_text="articolo 107 TUEL",
        source_priority=["corpus_governato"],
    )

    assert envelope["orchestration_status"] == "SUCCESS_WITH_WARNINGS"
    assert envelope["requires_human_m07_completion"] is True
    assert envelope["can_close_m07"] is False
    assert envelope["can_build_rac"] is False
    assert envelope["can_finalize_compliance"] is False
    assert envelope["can_authorize_output"] is False
    assert envelope["can_emit_go_no_go"] is False
    assert envelope["manual_level_a_only"] is True
    assert envelope["runner_federated_touched"] is False