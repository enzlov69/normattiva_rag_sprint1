from runtime.m07_documentary_support_orchestrator import (
    M07OrchestratorUnauthorizedCallerError,
    orchestrate_m07_documentary_support,
)


def test_orchestrator_propagates_blocked_response() -> None:
    def fake_transport(_: dict) -> dict:
        return {
            "request_id": "req_4101",
            "case_id": "case_4101",
            "trace_id": "trace_4101",
            "api_version": "2.0",
            "responder_module": "B16_M07SupportLayer",
            "status": "BLOCKED",
            "payload": {
                "documentary_packet": {
                    "source_ids": [],
                    "norm_unit_ids": [],
                    "support_only_flag": True,
                    "m07_evidence_pack": {
                        "record_id": "rec_m07_4101",
                        "record_type": "M07EvidencePack",
                        "m07_pack_id": "m07pack_4101",
                        "case_id": "case_4101",
                        "source_ids": [],
                        "norm_unit_ids": [],
                        "ordered_reading_sequence": [],
                        "annex_refs": [],
                        "crossref_refs": [],
                        "coverage_ref_id": "cov_4101",
                        "missing_elements": ["citazione mancante"],
                        "m07_support_status": "BLOCKED_SUPPORT",
                        "human_completion_required": True,
                        "created_at": "2026-03-19T19:10:00Z",
                        "updated_at": "2026-03-19T19:10:00Z",
                        "schema_version": "1.0",
                        "record_version": 1,
                        "source_layer": "B",
                        "trace_id": "trace_4101",
                        "active_flag": True
                    }
                }
            },
            "warnings": [],
            "errors": [],
            "blocks": [
                {
                    "block_id": "blk_4101",
                    "case_id": "case_4101",
                    "block_code": "CITATION_INCOMPLETE",
                    "block_category": "CITATION",
                    "block_severity": "CRITICAL",
                    "origin_module": "B15_CitationBuilder",
                    "block_reason": "citazione incompleta",
                    "block_status": "OPEN"
                }
            ],
            "timestamp": "2026-03-19T19:10:01Z"
        }

    envelope = orchestrate_m07_documentary_support(
        transport=fake_transport,
        session_id="sess_4101",
        request_id="req_4101",
        case_id="case_4101",
        trace_id="trace_4101",
        timestamp="2026-03-19T19:10:00Z",
        caller_module="A4_M07Governor",
        goal_istruttorio="supporto documentale M07 con criticità citazionale",
        domain_target="enti_locali",
        query_text="articolo 107 TUEL",
        source_priority=["corpus_governato"],
    )

    assert envelope["orchestration_status"] == "BLOCKED"
    assert any(block["block_code"] == "CITATION_INCOMPLETE" for block in envelope["blocks"])
    assert envelope["can_close_m07"] is False


def test_orchestrator_blocks_when_m07_evidence_pack_missing() -> None:
    def fake_transport(_: dict) -> dict:
        return {
            "request_id": "req_4102",
            "case_id": "case_4102",
            "trace_id": "trace_4102",
            "api_version": "2.0",
            "responder_module": "B16_M07SupportLayer",
            "status": "SUCCESS",
            "payload": {
                "documentary_packet": {
                    "source_ids": ["source_1"],
                    "norm_unit_ids": ["unit_1"],
                    "support_only_flag": True
                }
            },
            "warnings": [],
            "errors": [],
            "blocks": [],
            "timestamp": "2026-03-19T19:10:01Z"
        }

    envelope = orchestrate_m07_documentary_support(
        transport=fake_transport,
        session_id="sess_4102",
        request_id="req_4102",
        case_id="case_4102",
        trace_id="trace_4102",
        timestamp="2026-03-19T19:10:00Z",
        caller_module="A1_OrchestratorePPAV",
        goal_istruttorio="supporto documentale M07 senza evidence pack",
        domain_target="enti_locali",
        query_text="articolo 107 TUEL",
        source_priority=["corpus_governato"],
    )

    assert envelope["orchestration_status"] == "BLOCKED"
    assert any(block["block_code"] == "M07_REQUIRED" for block in envelope["blocks"])


def test_orchestrator_rejects_unauthorized_caller() -> None:
    def fake_transport(_: dict) -> dict:
        raise AssertionError("Il transport non deve essere chiamato")

    try:
        orchestrate_m07_documentary_support(
            transport=fake_transport,
            session_id="sess_4103",
            request_id="req_4103",
            case_id="case_4103",
            trace_id="trace_4103",
            timestamp="2026-03-19T19:10:00Z",
            caller_module="A9_UnknownCaller",
            goal_istruttorio="caller non autorizzato",
            domain_target="enti_locali",
            query_text="articolo 107 TUEL",
            source_priority=["corpus_governato"],
        )
    except M07OrchestratorUnauthorizedCallerError:
        return

    raise AssertionError("Attesa M07OrchestratorUnauthorizedCallerError")