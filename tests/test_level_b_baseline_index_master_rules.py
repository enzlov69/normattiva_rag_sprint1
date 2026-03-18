from __future__ import annotations

from pathlib import Path

from validators.level_b_baseline_index_rules import (
    build_report,
    compute_decision,
    evaluate_checkpoints,
    load_json,
    validate_registry_shape,
)

BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "schemas" / "level_b_baseline_index_master_registry_v1.json"


def test_decision_error_for_invalid_registry() -> None:
    decision, reasons = compute_decision(
        registry_problems=["broken"],
        checkpoint_results=[],
        git_status_clean=True,
    )
    assert decision == "ERROR"
    assert reasons == ["REGISTRY_INVALID: broken"]


def test_decision_hold_for_missing_assets_in_isolated_workspace(tmp_path: Path) -> None:
    registry = load_json(REGISTRY_PATH)
    results = evaluate_checkpoints(tmp_path, registry)
    decision, reasons = compute_decision(
        registry_problems=[],
        checkpoint_results=results,
        git_status_clean=True,
    )
    assert decision == "HOLD"
    assert "CHECKPOINT_LB-VAL1_MISSING_FILES" in reasons
    assert "CHECKPOINT_LB-BIM_MISSING_FILES" in reasons


def test_report_next_action_complete() -> None:
    registry = load_json(REGISTRY_PATH)
    report = build_report(
        registry=registry,
        registry_problems=[],
        checkpoint_results=[],
        decision="COMPLETE",
        reasons=[],
        base_dir=BASE_DIR,
        git_status_clean=True,
    )
    assert report["decision"] == "COMPLETE"
    assert report["next_action"].startswith("Baseline index master is structurally coherent")
