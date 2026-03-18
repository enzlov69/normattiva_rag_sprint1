from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from validators.level_b_traceability_bundle_rules import (  # noqa: E402
    build_bundle_report,
    check_components,
    check_required_paths,
    check_required_tags,
    compute_bundle_decision,
    load_json,
    validate_registry_shape,
)

REGISTRY_PATH = BASE_DIR / "schemas" / "level_b_traceability_bundle_registry_v1.json"


def test_traceability_decision_hold_on_synthetic_incomplete_workspace(tmp_path: Path) -> None:
    registry = load_json(REGISTRY_PATH)
    registry_problems = validate_registry_shape(registry)
    path_results = check_required_paths(tmp_path, registry["required_paths"])
    tag_results = check_required_tags(registry["required_tags"], [])
    component_results = check_components(tmp_path, registry["components"], [])

    decision, reasons = compute_bundle_decision(
        registry_problems=registry_problems,
        path_results=path_results,
        tag_results=tag_results,
        component_results=component_results,
        git_status_clean=True,
    )

    assert decision == "HOLD"
    assert "TAG_stable-level-b-validation-v2_MISSING" in reasons
    assert "COMPONENT_validation_kit_INCOMPLETE" in reasons


def test_traceability_decision_complete_on_synthetic_complete_workspace(tmp_path: Path) -> None:
    registry = load_json(REGISTRY_PATH)

    for item in registry["required_paths"]:
        path = tmp_path / item["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")

    available_tags = registry["required_tags"]
    registry_problems = validate_registry_shape(registry)
    path_results = check_required_paths(tmp_path, registry["required_paths"])
    tag_results = check_required_tags(available_tags, available_tags)
    component_results = check_components(tmp_path, registry["components"], available_tags)

    decision, reasons = compute_bundle_decision(
        registry_problems=registry_problems,
        path_results=path_results,
        tag_results=tag_results,
        component_results=component_results,
        git_status_clean=True,
    )

    assert decision == "COMPLETE"
    assert reasons == []


def test_traceability_report_contains_next_action() -> None:
    registry = load_json(REGISTRY_PATH)
    report = build_bundle_report(
        registry=registry,
        registry_problems=[],
        path_results=[],
        tag_results=[],
        component_results=[],
        decision="COMPLETE",
        reasons=[],
        base_dir=BASE_DIR,
        available_tags=[],
        git_status_clean=True,
    )
    assert report["decision"] == "COMPLETE"
    assert report["next_action"].startswith("Traceability bundle is coherent.")
