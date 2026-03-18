from __future__ import annotations

from pathlib import Path

from validators.level_b_baseline_index_rules import load_json, validate_registry_shape

BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "schemas" / "level_b_baseline_index_master_registry_v1.json"


def test_registry_shape_is_valid() -> None:
    registry = load_json(REGISTRY_PATH)
    problems = validate_registry_shape(registry)
    assert problems == []


def test_registry_declares_expected_checkpoint_ids() -> None:
    registry = load_json(REGISTRY_PATH)
    ids = [checkpoint["id"] for checkpoint in registry["checkpoints"]]
    assert ids == ["LB-VAL1", "LB-VAL2", "LB-GOLD", "LB-RUN", "LB-CC", "LB-TRACE", "LB-BIM"]
