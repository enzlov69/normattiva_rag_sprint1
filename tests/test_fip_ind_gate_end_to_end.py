from runtime.fip_ind_gate import (
    build_question,
    evaluate_gate,
    validate_documentary_support_response,
)


def test_end_to_end_gate_with_documentary_support_and_block() -> None:
    response = {
        "request_id": "req_fip_003",
        "case_id": "case_fip_003",
        "trace_id": "trace_fip_003",
        "api_version": "2.0",
        "responder_module": "B17_FIPINDSupportLayer",
        "status": "BLOCKED",
        "payload": {
            "documentary_packet": {
                "question_ids": ["Q01", "Q03", "Q06", "Q09", "Q10"],
                "support_only_flag": True,
                "fip_ind_evidence_pack": {
                    "record_id": "rec_fip_003",
                    "record_type": "FIPIndEvidencePack",
                    "case_id": "case_fip_003",
                    "trace_id": "trace_fip_003",
                    "source_layer": "B",
                    "human_gate_required": True,
                    "question_support": [
                        {"question_id": "Q01", "support_status": "SUPPORTED", "source_ids": ["source_1"]},
                        {"question_id": "Q03", "support_status": "SUPPORTED", "source_ids": ["source_2"]},
                        {"question_id": "Q06", "support_status": "SUPPORTED", "source_ids": ["source_3"]},
                        {"question_id": "Q09", "support_status": "SUPPORTED", "source_ids": ["source_4"]},
                        {"question_id": "Q10", "support_status": "SUPPORTED", "source_ids": ["source_5"]}
                    ],
                    "fip_ind_support_status": "BLOCKED_SUPPORT"
                }
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [
            {
                "block_id": "blk_fip_003",
                "case_id": "case_fip_003",
                "block_code": "FIP_IND_THRESHOLD_BLOCK",
                "block_category": "FIP_IND",
                "block_severity": "CRITICAL",
                "origin_module": "A_FIP_IND_GATE",
                "block_reason": "soglia di falso indirizzo",
                "block_status": "OPEN"
            }
        ],
        "timestamp": "2026-03-20T10:00:01Z"
    }

    validate_documentary_support_response(response)

    questionnaire = {
        "case_id": "case_fip_003",
        "trace_id": "trace_fip_003",
        "act_type": "DELIBERA_GC",
        "act_title": "Atto formalmente di indirizzo ma sostanzialmente gestionale",
        "compiled_by_module": "A1_OrchestratorePPAV",
        "questions": [
            build_question("Q01", "YES"),
            build_question("Q02", "NO"),
            build_question("Q03", "YES"),
            build_question("Q04", "NO"),
            build_question("Q05", "NO"),
            build_question("Q06", "YES"),
            build_question("Q07", "NO"),
            build_question("Q08", "NO"),
            build_question("Q09", "YES"),
            build_question("Q10", "YES"),
        ],
    }

    result = evaluate_gate(questionnaire)
    assert result["gate_result"] == "FALSO_INDIRIZZO_BLOCKED"
    assert result["blocked"] is True
