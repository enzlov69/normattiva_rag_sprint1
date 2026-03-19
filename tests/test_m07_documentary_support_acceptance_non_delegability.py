import pytest

from runtime.m07_documentary_support_orchestrator import (
    M07OrchestratorBoundaryError,
    M07OrchestratorUnauthorizedCallerError,
    orchestrate_m07_documentary_support,
)


def test_acceptance_non_delegability_flags_always_false() -> None:
    def fake_transport(_: dict) -> dict:
        return {
            "request_id": "req_5201",
            "case_id": "case_5201",
            "trace_id": "trace_5201",
            "api_version": "2.0",
            "responder_module": "B16_M07SupportLayer",
            "status": "SUCCESS_WITH_WARNINGS",
            "payload": {
                "documentary_packet": {
                    "source_ids": ["source_1"],
                    "norm_unit_ids": ["unit_1"],
                    "support_only_flag": True,
                    "m07_evidence_pack": {
                        "record_id": "rec_m07_5201",
                        "record_type": "M07EvidencePack",
                        "m07_pack_id": "m07pack_5201",
                        "case_id": "case_5201",
                        "source_ids": ["source_1"],
                        "norm_unit_ids": ["unit_1"],
                        "ordered_reading_sequence": [],
                        "annex_refs": [],
                        "crossref_refs": [],
                        "coverage_ref_id": "cov_5201",
                        "missing_elements": [],
                        "m07_support_status": "READY_FOR_HUMAN_READING",
                        "human_completion_required": True,
                        "created_at": "2026-03-19T20:20:00Z",
                        "updated_at": "2026-03-19T20:20:00Z",
                        "schema_version": "1.0",
                        "record_version": 1,
                        "source_layer": "B",
                        "trace_id": "trace_5201",
                        "active_flag": True,
                    },
                }
            },
            "warnings": [
                {
                    "warning_code": "COVERAGE_PARTIAL",
                    "warning_message": "coverage parziale",
                }
            ],
            "errors": [],
            "blocks": [],
            "timestamp": "2026-03-19T20:20:01Z",
        }

    envelope = orchestrate_m07_documentary_support(
        transport=fake_transport,
        session_id="sess_5201",
        request_id="req_5201",
        case_id="case_5201",
        trace_id="trace_5201",
        timestamp="2026-03-19T20:20:00Z",
        caller_module="A2_CaseClassifier",
        goal_istruttorio="ricognizione documentale",
        domain_target="enti_locali",
        query_text="articolo 107 TUEL",
        source_priority=["corpus_governato"],
    )

    assert envelope["requires_human_m07_completion"] is True
    assert envelope["can_close_m07"] is False
    assert envelope["can_build_rac"] is False
    assert envelope["can_finalize_compliance"] is False
    assert envelope["can_authorize_output"] is False
    assert envelope["can_emit_go_no_go"] is False
    assert envelope["manual_level_a_only"] is True
    assert envelope["runner_federated_touched"] is False


def test_acceptance_unauthorized_caller_is_rejected_before_transport() -> None:
    def fake_transport(_: dict) -> dict:
        raise AssertionError("Il transport non deve essere chiamato")

    with pytest.raises(M07OrchestratorUnauthorizedCallerError):
        orchestrate_m07_documentary_support(
            transport=fake_transport,
            session_id="sess_5202",
            request_id="req_5202",
            case_id="case_5202",
            trace_id="trace_5202",
            timestamp="2026-03-19T20:20:00Z",
            caller_module="A9_UnknownCaller",
            goal_istruttorio="caller non autorizzato",
            domain_target="enti_locali",
            query_text="articolo 107 TUEL",
            source_priority=["corpus_governato"],
        )


def test_acceptance_forbidden_decision_semantics_are_blocked() -> None:
    def fake_transport(_: dict) -> dict:
        return {
            "request_id": "req_5203",
            "case_id": "case_5203",
            "trace_id": "trace_5203",
            "api_version": "2.0",
            "responder_module": "B16_M07SupportLayer",
            "status": "SUCCESS",
            "payload": {
                "documentary_packet": {
                    "source_ids": ["source_1"],
                    "norm_unit_ids": ["unit_1"],
                    "support_only_flag": True,
                }
            },
            "warnings": [],
            "errors": [],
            "blocks": [],
            "timestamp": "2026-03-19T20:20:01Z",
            "final_decision": "GO",
        }

    with pytest.raises(M07OrchestratorBoundaryError):
        orchestrate_m07_documentary_support(
            transport=fake_transport,
            session_id="sess_5203",
            request_id="req_5203",
            case_id="case_5203",
            trace_id="trace_5203",
            timestamp="2026-03-19T20:20:00Z",
            caller_module="A1_OrchestratorePPAV",
            goal_istruttorio="tentativo di semantica conclusiva",
            domain_target="enti_locali",
            query_text="articolo 107 TUEL",
            source_priority=["corpus_governato"],
        )