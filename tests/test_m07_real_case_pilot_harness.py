
from runtime.m07_real_case_pilot_harness import (
    load_pilot_cases,
    run_pilot_batch,
    run_pilot_case,
    summarize_pilot_batch,
)


def test_pilot_case_file_loads() -> None:
    cases = load_pilot_cases()
    assert len(cases) >= 3
    assert cases[0]["case_id"] == "pilot_case_001"


def test_single_pilot_case_runs_in_support_only_mode() -> None:
    case = load_pilot_cases()[0]
    envelope = run_pilot_case(case)

    assert envelope["pilot_mode"] is True
    assert envelope["real_case_flag"] is True
    assert envelope["decision_disabled"] is True
    assert envelope["manual_level_a_only"] is True
    assert envelope["can_close_m07"] is False
    assert envelope["can_authorize_output"] is False
    assert envelope["runner_federated_touched"] is False


def test_pilot_batch_summary_is_consistent() -> None:
    cases = load_pilot_cases()
    envelopes = run_pilot_batch(cases)
    summary = summarize_pilot_batch(envelopes)

    assert summary["total_cases"] == len(cases)
    assert summary["success"] >= 1
    assert summary["blocked"] >= 1
    assert summary["runner_federated_touched"] is False
    assert summary["decision_enabled"] is False
    assert summary["output_authorization_enabled"] is False
