from __future__ import annotations

from pathlib import Path

from validators.level_b_change_control_rules import load_json, validate_registry_shape


BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "schemas" / "level_b_change_control_registry_v1.json"


def test_change_control_registry_shape_is_valid() -> None:
    registry = load_json(REGISTRY_PATH)
    problems = validate_registry_shape(registry)
    assert problems == []


def test_change_control_registry_has_protected_assets_and_forbidden_touchpoints() -> None:
    registry = load_json(REGISTRY_PATH)
    assert "schemas/level_b_golden_baseline_registry_v1.json" in registry["protected_assets"]
    assert "runner_federato" in registry["forbidden_touchpoints"]
