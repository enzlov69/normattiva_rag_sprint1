from __future__ import annotations

from pathlib import Path

from validators.level_b_readiness_rules import load_json, validate_registry_shape

BASE_DIR = Path(__file__).resolve().parents[1]


def test_registry_shape_is_valid() -> None:
    registry = load_json(BASE_DIR / "schemas" / "level_b_readiness_dossier_registry_v1.json")
    assert validate_registry_shape(registry) == []


def test_registry_declares_offline_scope_and_expected_checkpoints() -> None:
    registry = load_json(BASE_DIR / "schemas" / "level_b_readiness_dossier_registry_v1.json")
    assert registry["scope"] == "offline_only"
    assert len(registry["checkpoints"]) == 6
