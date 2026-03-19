import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL_BLOCK_REGISTRY_PATH = ROOT / "schemas" / "final_block_registry_v1.json"
PROPAGATION_REGISTRY_PATH = ROOT / "schemas" / "final_ab_block_propagation_registry_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_final_block_registry_has_required_runtime_fields() -> None:
    registry = _load(FINAL_BLOCK_REGISTRY_PATH)
    required_fields = {
        "block_code",
        "family",
        "severity",
        "origin_layer",
        "runtime_effect",
        "level_a_effect",
        "blocks_opponibility",
        "m07_sensitive",
        "documentary_sensitive",
        "traceability_sensitive",
        "release_rule",
        "notes"
    }
    for block in registry["blocks"]:
        assert required_fields.issubset(block.keys())


def test_final_block_registry_aligns_with_consolidated_critical_blocks() -> None:
    final_registry = _load(FINAL_BLOCK_REGISTRY_PATH)
    propagation_registry = _load(PROPAGATION_REGISTRY_PATH)

    final_codes = {block["block_code"] for block in final_registry["blocks"]}
    propagation_codes = {block["block_code"] for block in propagation_registry["blocks"]}

    assert propagation_codes.issubset(final_codes)


def test_final_block_registry_has_no_improper_downgrade_or_non_propagating_critical_blocks() -> None:
    registry = _load(FINAL_BLOCK_REGISTRY_PATH)
    for block in registry["blocks"]:
        assert block["severity"] == "CRITICAL"
        assert block["release_rule"] == "LEVEL_A_METHOD_ONLY"
        assert block["level_a_effect"] in {
            "STOP_FLOW",
            "HARD_STOP",
            "KEEP_SUPPORT_ONLY",
            "OPEN_OR_CONTINUE_M07_UNDER_LEVEL_A_GOVERNANCE"
        }

