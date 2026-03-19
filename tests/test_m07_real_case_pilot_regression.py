
from runtime.m07_real_case_pilot_harness import (
    load_pilot_cases,
    run_pilot_case,
)


def _find_case(case_id: str) -> dict:
    for case in load_pilot_cases():
        if case["case_id"] == case_id:
            return case
    raise AssertionError(f"Caso non trovato: {case_id}")


def test_regression_citation_incomplete_case_stays_blocked() -> None:
    case = _find_case("pilot_case_002")
    envelope = run_pilot_case(case)

    assert envelope["orchestration_status"] == "BLOCKED"
    assert any(block["block_code"] == "CITATION_INCOMPLETE" for block in envelope["blocks"])
    assert envelope["can_close_m07"] is False
    assert envelope["can_authorize_output"] is False


def test_regression_warning_case_stays_non_decisional() -> None:
    case = _find_case("pilot_case_003")
    envelope = run_pilot_case(case)

    assert envelope["orchestration_status"] == "SUCCESS_WITH_WARNINGS"
    assert len(envelope["warnings"]) >= 1
    assert envelope["manual_level_a_only"] is True
    assert envelope["can_build_rac"] is False
    assert envelope["can_emit_go_no_go"] is False
    assert envelope["can_authorize_output"] is False
