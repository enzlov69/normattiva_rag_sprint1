import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL_REGISTRY_PATH = ROOT / "schemas" / "final_ab_forbidden_level_b_fields_registry_v1.json"
LEVEL_B_REGISTRY_PATH = ROOT / "schemas" / "level_b_forbidden_fields_registry_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_forbidden_registry_covers_essential_fields() -> None:
    registry = _load(FINAL_REGISTRY_PATH)
    names = {entry["field_name"] for entry in registry["entries"]}
    assert {
        "decision",
        "final_decision",
        "approval",
        "human_approval",
        "normative_prevalence_choice",
        "legal_applicability_decision",
        "final_motivation",
        "m07_closed",
        "output_authorized",
        "final_compliance_passed",
        "provvedimento_generato",
        "rac_finale_decisorio",
        "esito_istruttoria_conclusivo"
    }.issubset(names)


def test_forbidden_registry_uses_critical_rejected_propagation_profile() -> None:
    registry = _load(FINAL_REGISTRY_PATH)
    for entry in registry["entries"]:
        assert entry["severity"] == "CRITICAL"
        assert entry["block_level"] == "REJECTED"
        assert entry["propagate_to_level_a"] is True


def test_final_registry_declares_relation_with_preliminary_level_b_registry() -> None:
    final_registry = _load(FINAL_REGISTRY_PATH)
    level_b_registry = _load(LEVEL_B_REGISTRY_PATH)
    assert "schemas/level_b_forbidden_fields_registry_v1.json" in final_registry["derives_from"]
    assert "final_decision" in level_b_registry["forbidden_fields"]

