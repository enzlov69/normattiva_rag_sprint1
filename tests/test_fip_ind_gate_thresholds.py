from runtime.fip_ind_gate import build_question, evaluate_gate


def _questionnaire_with_answers(case_id: str, answers: list[str]) -> dict:
    return {
        "case_id": case_id,
        "trace_id": f"trace_{case_id}",
        "act_type": "DELIBERA_GC",
        "act_title": "Test FIP-IND",
        "compiled_by_module": "A1_OrchestratorePPAV",
        "questions": [build_question(f"Q{idx:02d}", answer) for idx, answer in enumerate(answers, start=1)],
    }


def test_threshold_zero_yes_is_indirizzo_puro() -> None:
    result = evaluate_gate(_questionnaire_with_answers("case_0", ["NO"] * 10))
    assert result["gate_result"] == "INDIRIZZO_PURO"
    assert result["blocked"] is False


def test_threshold_one_yes_is_rischio() -> None:
    answers = ["YES"] + ["NO"] * 9
    result = evaluate_gate(_questionnaire_with_answers("case_1", answers))
    assert result["gate_result"] == "RISCHIO_FIP_IND"
    assert result["blocked"] is False


def test_threshold_three_yes_is_provvedimento() -> None:
    answers = ["YES", "YES", "YES"] + ["NO"] * 7
    result = evaluate_gate(_questionnaire_with_answers("case_3", answers))
    assert result["gate_result"] == "PROVVEDIMENTO_SOSTANZIALE"
    assert result["requalification_required"] is True


def test_threshold_five_yes_is_false_indirizzo_blocked() -> None:
    answers = ["YES"] * 5 + ["NO"] * 5
    result = evaluate_gate(_questionnaire_with_answers("case_5", answers))
    assert result["gate_result"] == "FALSO_INDIRIZZO_BLOCKED"
    assert result["blocked"] is True
    assert result["triggered_block_code"] == "FIP_IND_THRESHOLD_BLOCK"
