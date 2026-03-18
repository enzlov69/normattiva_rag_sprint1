from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from validators.level_b_traceability_bundle_rules import load_json, validate_registry_shape  # noqa: E402


REGISTRY_PATH = BASE_DIR / "schemas" / "level_b_traceability_bundle_registry_v1.json"


def test_traceability_registry_is_valid() -> None:
    data = load_json(REGISTRY_PATH)
    assert validate_registry_shape(data) == []


def test_traceability_registry_declares_change_control_checkpoint() -> None:
    data = load_json(REGISTRY_PATH)
    assert "stable-level-b-change-control-v1" in data["required_tags"]
