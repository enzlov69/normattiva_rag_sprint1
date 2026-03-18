from __future__ import annotations

from pathlib import Path

from validators.level_b_readiness_rules import (
    build_readiness_report,
    check_checkpoint_paths,
    compute_readiness_decision,
    load_json,
    validate_registry_shape,
)

BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "schemas" / "level_b_readiness_dossier_registry_v1.json"


def test_readiness_hold_on_empty_workspace(tmp_path: Path) -> None:
    registry = load_json(REGISTRY_PATH)
    problems = validate_registry_shape(registry)
    checkpoint_results = check_checkpoint_paths(tmp_path, registry["checkpoints"])
    decision, reasons = compute_readiness_decision(
        registry_problems=problems,
        checkpoint_results=checkpoint_results,
        repository_clean=True,
        expected_tags_present=[],
        expected_tags_total=[item["expected_tag"] for item in registry["checkpoints"]],
    )
    assert decision == "HOLD"
    assert "CHECKPOINT_LB-VAL-V2_INCOMPLETE" in reasons
    assert "EXPECTED_TAG_MISSING:stable-level-b-validation-v2" in reasons


def test_readiness_complete_on_synthetic_full_workspace(tmp_path: Path) -> None:
    registry = load_json(REGISTRY_PATH)
    for checkpoint in registry["checkpoints"]:
        for rel_path in checkpoint["required_paths"]:
            p = tmp_path / rel_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("placeholder\n", encoding="utf-8")
    checkpoint_results = check_checkpoint_paths(tmp_path, registry["checkpoints"])
    decision, reasons = compute_readiness_decision(
        registry_problems=[],
        checkpoint_results=checkpoint_results,
        repository_clean=True,
        expected_tags_present=[item["expected_tag"] for item in registry["checkpoints"]],
        expected_tags_total=[item["expected_tag"] for item in registry["checkpoints"]],
    )
    assert decision == "COMPLETE"
    assert reasons == []


def test_report_contains_exclusions_and_preconditions() -> None:
    registry = load_json(REGISTRY_PATH)
    report = build_readiness_report(
        registry=registry,
        registry_problems=[],
        checkpoint_results=[],
        repository_clean=True,
        expected_tags_present=[],
        decision="COMPLETE",
        reasons=[],
        base_dir=BASE_DIR,
    )
    assert "runner_federato" in report["excluded_components"]
    assert "working_tree_clean" in report["next_step_preconditions"]
