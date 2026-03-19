import json
from pathlib import Path

from jsonschema import Draft202012Validator

from runtime.m07_documentary_support_module_registry import (
    M07_DOCUMENTARY_SUPPORT_MODULE_ID,
    get_m07_documentary_support_module_entry,
    get_m07_documentary_support_module_registry,
    get_m07_documentary_support_registry_snapshot,
)


BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = BASE_DIR / "schemas"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


def test_registry_conforms_to_schema() -> None:
    schema = load_schema("m07_documentary_support_module_registry_v1.json")
    registry = get_m07_documentary_support_module_registry()
    Draft202012Validator(schema).validate(registry)


def test_registry_contains_expected_module() -> None:
    entry = get_m07_documentary_support_module_entry()

    assert entry["module_id"] == M07_DOCUMENTARY_SUPPORT_MODULE_ID
    assert entry["module_layer"] == "A"
    assert entry["support_only"] is True
    assert entry["human_completion_required"] is True


def test_registry_snapshot_is_non_executive() -> None:
    snapshot = get_m07_documentary_support_registry_snapshot()

    assert snapshot["runner_federated_touched"] is False
    assert snapshot["decision_enabled"] is False
    assert snapshot["output_authorization_enabled"] is False
    assert snapshot["requires_manual_level_a_governance"] is True