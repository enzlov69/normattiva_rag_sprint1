from __future__ import annotations

from pathlib import Path

from validators.level_b_runbook_rules import (
    build_preflight_report,
    check_required_paths,
    check_required_suites,
    compute_preflight_decision,
    load_json,
    validate_runbook_checklist_shape,
)


BASE_DIR = Path(__file__).resolve().parents[1]
CHECKLIST_PATH = BASE_DIR / "schemas" / "level_b_runbook_checklist_v1.json"


def test_preflight_decision_hold_on_synthetic_isolated_workspace(tmp_path: Path) -> None:
    checklist = load_json(CHECKLIST_PATH)
    problems = validate_runbook_checklist_shape(checklist)
    path_results = check_required_paths(tmp_path, checklist["required_paths"])
    suite_results = check_required_suites(tmp_path, checklist["required_suites"])

    decision, reasons = compute_preflight_decision(
        checklist_problems=problems,
        path_results=path_results,
        suite_results=suite_results,
        git_status_clean=True,
    )

    assert decision == "HOLD"
    assert "PATH_LB-PATH-GB-DOC-001_MISSING" in reasons
    assert "SUITE_LB-SUITE-001_MISSING" in reasons


def test_preflight_decision_ready_on_synthetic_complete_workspace(tmp_path: Path) -> None:
    checklist = load_json(CHECKLIST_PATH)

    for item in checklist["required_paths"]:
        path = tmp_path / item["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")

    for suite in checklist["required_suites"]:
        path = tmp_path / suite["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")

    problems = validate_runbook_checklist_shape(checklist)
    path_results = check_required_paths(tmp_path, checklist["required_paths"])
    suite_results = check_required_suites(tmp_path, checklist["required_suites"])
    decision, reasons = compute_preflight_decision(
        checklist_problems=problems,
        path_results=path_results,
        suite_results=suite_results,
        git_status_clean=True,
    )

    assert decision == "READY"
    assert reasons == []


def test_preflight_decision_error_for_invalid_checklist() -> None:
    decision, reasons = compute_preflight_decision(
        checklist_problems=["broken checklist"],
        path_results=[],
        suite_results=[],
        git_status_clean=True,
    )
    assert decision == "ERROR"
    assert reasons == ["CHECKLIST_INVALID: broken checklist"]


def test_preflight_report_contains_next_action() -> None:
    checklist = load_json(CHECKLIST_PATH)
    report = build_preflight_report(
        checklist=checklist,
        checklist_problems=[],
        path_results=[],
        suite_results=[],
        decision="READY",
        reasons=[],
        base_dir=BASE_DIR,
        git_status_clean=True,
    )
    assert report["decision"] == "READY"
    assert report["next_action"].startswith("Proceed with the ordered offline runbook execution")