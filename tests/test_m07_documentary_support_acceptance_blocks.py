from runtime.m07_documentary_support_orchestrator import (
    orchestrate_m07_documentary_support,
)


def test_acceptance_block_propagation_for_citation_incomplete() -> None:
    def fake_transport(_: dict) -> dict:
        return {
            "request_id": "req_5101",
            "case_id": "case_5101",
            "trace_id": "trace_5101",
            "api_version": "2.0",
            "responder_module": "B16_M07SupportLayer",
            "status": "BLOCKED",
            "payload": {
                "documentary_packet": {
                    "source_ids": ["source_1"],
                    "norm_unit_ids": ["unit_1"],
                    "support_only_flag": True,
                    "m07_evidence_pack": {
                        "record_id": "rec_m07_5101",
                        "record_type": "M07EvidencePack",
                        "m07_pack_id": "m07pack_5101",
                        "case_id": "case_5101",
                        "source_ids": ["source_1"],
                        "norm_unit_ids": ["unit_1"],
                        "ordered_reading_sequence": [],
                        "annex_refs": [],
                        "crossref_refs": [],
                        "coverage_ref_id": "cov_5101",
                        "missing_elements": ["citazione incompleta"],
                        "m07_support_status": "BLOCKED_SUPPORT",
                        "human_completion_required": True,
                        "created_at": "2026-03-19T20:10:00Z",
                        "updated_at": "2026-03-19T20:10:00Z",
                        "schema_version": "1.0",
                        "record_version": 1,
                        "source_layer": "B",
                        "trace_id": "trace_5101",
                        "active_flag": True,
                    },
                }
            },
            "warnings": [],
            "errors": [],
            "blocks": [
                {
                    "block_id": "blk_5101",
                    "case_id": "case_5101",
                    "block_code": "CITATION_INCOMPLETE",
                    "block_category": "CITATION",
                    "block_severity": "CRITICAL",
                    "origin_module": "B15_CitationBuilder",
                    "block_reason": "citazione incompleta",
                    "block_status": "OPEN",
                }
            ],
            "timestamp": "2026-03-19T20:10:01Z",
        }

    envelope = orchestrate_m07_documentary_support(
        transport=fake_transport,
        session_id="sess_5101",
        request_id="req_5101",
        case_id="case_5101",
        trace_id="trace_5101",
        timestamp="2026-03-19T20:10:00Z",
        caller_module="A4_M07Governor",
        goal_istruttorio="supporto documentale con blocco citazionale",
        domain_target="enti_locali",
        query_text="articolo 107 TUEL",
        source_priority=["corpus_governato"],
    )

    assert envelope["orchestration_status"] == "BLOCKED"
    assert len(envelope["blocks"]) >= 1
    assert any(block["block_code"] == "CITATION_INCOMPLETE" for block in envelope["blocks"])
    assert envelope["can_close_m07"] is False
    assert envelope["can_authorize_output"] is False


def test_acceptance_m07_required_when_evidence_pack_missing() -> None:
    def fake_transport(_: dict) -> dict:
        return {
            "request_id": "req_5102",
            "case_id": "case_5102",
            "trace_id": "trace_5102",
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
            "timestamp": "2026-03-19T20:10:01Z",
        }

    envelope = orchestrate_m07_documentary_support(
        transport=fake_transport,
        session_id="sess_5102",
        request_id="req_5102",
        case_id="case_5102",
        trace_id="trace_5102",
        timestamp="2026-03-19T20:10:00Z",
        caller_module="A1_OrchestratorePPAV",
        goal_istruttorio="supporto documentale senza evidence pack",
        domain_target="enti_locali",
        query_text="articolo 107 TUEL",
        source_priority=["corpus_governato"],
    )

    assert envelope["orchestration_status"] == "BLOCKED"
    assert any(block["block_code"] == "M07_REQUIRED" for block in envelope["blocks"])