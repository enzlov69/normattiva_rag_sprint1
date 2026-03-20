from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEQUENCE_REGISTRY_PATH = ROOT / "schemas" / "ppav_phase_sequence_registry_v1.json"
GATE_REGISTRY_PATH = ROOT / "schemas" / "ppav_phase_gate_registry_v1.json"


def load_json(path: Path) -> dict:
    assert path.exists(), f"File non trovato: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def load_registries() -> tuple[dict, dict]:
    return load_json(SEQUENCE_REGISTRY_PATH), load_json(GATE_REGISTRY_PATH)


def test_sequence_registry_declares_level_b_non_decisional_invariants() -> None:
    sequence_registry, _ = load_registries()
    invariants = sequence_registry["invariants"]

    assert invariants["level_b_cannot_decide"] is True
    assert invariants["level_b_cannot_validate"] is True
    assert invariants["level_b_cannot_close_m07"] is True
    assert invariants["level_b_cannot_authorize_output"] is True


def test_gate_registry_declares_level_b_non_decisional_global_rules() -> None:
    _, gate_registry = load_registries()
    rules = gate_registry["global_rules"]

    assert rules["level_b_never_decides"] is True
    assert rules["level_b_never_validates"] is True
    assert rules["level_b_never_closes_m07"] is True
    assert rules["level_b_never_emits_go_no_go"] is True
    assert rules["level_b_never_authorizes_opposable_output"] is True


def test_all_phases_are_governed_by_level_a_decision() -> None:
    _, gate_registry = load_registries()

    for phase_id, cfg in gate_registry["phases"].items():
        assert cfg["level_a_decides"] is True, (
            f"La fase {phase_id} deve restare governata dal Livello A"
        )


def test_non_delegable_phases_are_marked_hard_non_delegable() -> None:
    _, gate_registry = load_registries()

    expected_non_delegable = {"S3", "S4", "S5", "S8", "S9", "S10", "S11"}
    actual_non_delegable = {
        phase_id
        for phase_id, cfg in gate_registry["phases"].items()
        if cfg.get("hard_non_delegable") is True
    }

    assert actual_non_delegable == expected_non_delegable


def test_level_b_cannot_close_m07() -> None:
    _, gate_registry = load_registries()
    s3 = gate_registry["phases"]["S3"]

    assert s3["level_a_decides"] is True
    assert s3["level_b_support_only"] is True
    assert s3["hard_non_delegable"] is True


def test_level_b_cannot_build_rac_as_decisional_output() -> None:
    _, gate_registry = load_registries()
    s4 = gate_registry["phases"]["S4"]

    assert s4["level_a_decides"] is True
    assert s4["level_b_support_only"] is True
    assert s4["hard_non_delegable"] is True
    assert s4["can_produce_opposable_output"] is False


def test_level_b_cannot_decide_layer_opponibility() -> None:
    _, gate_registry = load_registries()
    s5 = gate_registry["phases"]["S5"]

    assert s5["level_a_decides"] is True
    assert s5["level_b_support_only"] is True
    assert s5["hard_non_delegable"] is True
    assert s5["can_produce_opposable_output"] is False


def test_level_b_cannot_emit_go_or_no_go_at_cf_atti() -> None:
    _, gate_registry = load_registries()
    s10 = gate_registry["phases"]["S10"]

    assert s10["level_a_decides"] is True
    assert s10["level_b_support_only"] is False
    assert s10["hard_non_delegable"] is True
    assert s10["can_produce_opposable_output"] is False


def test_only_s11_is_opposable_and_this_does_not_shift_decision_to_level_b() -> None:
    sequence_registry, gate_registry = load_registries()

    opposable_from_sequence = [
        phase["phase_id"]
        for phase in sequence_registry["phases"]
        if phase["can_produce_opposable_output"] is True
    ]
    opposable_from_gate = [
        phase_id
        for phase_id, cfg in gate_registry["phases"].items()
        if cfg["can_produce_opposable_output"] is True
    ]

    assert opposable_from_sequence == ["S11"]
    assert opposable_from_gate == ["S11"]

    s11 = gate_registry["phases"]["S11"]
    assert s11["level_a_decides"] is True
    assert s11["level_b_support_only"] is True
    assert s11["hard_non_delegable"] is True


def test_cotpp_is_summary_only_and_never_replaces_gates() -> None:
    _, gate_registry = load_registries()
    rules = gate_registry["global_rules"]

    assert rules["cotpp_is_summary_only"] is True


def test_no_phase_other_than_s11_can_produce_opposable_output() -> None:
    _, gate_registry = load_registries()

    non_terminal_opposable = [
        phase_id
        for phase_id, cfg in gate_registry["phases"].items()
        if cfg["can_produce_opposable_output"] is True and phase_id != "S11"
    ]

    assert non_terminal_opposable == []