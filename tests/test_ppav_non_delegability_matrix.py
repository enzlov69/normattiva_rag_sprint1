from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEQUENCE_REGISTRY_PATH = ROOT / "schemas" / "ppav_phase_sequence_registry_v1.json"
GATE_REGISTRY_PATH = ROOT / "schemas" / "ppav_phase_gate_registry_v1.json"

EXPECTED_HARD_NON_DELEGABLE = {
    "S3": {
        "function_contains": "M07",
        "level_a_decides": True,
        "level_b_support_only": True,
        "hard_non_delegable": True,
        "can_produce_opposable_output": False,
    },
    "S4": {
        "function_contains": "RAC",
        "level_a_decides": True,
        "level_b_support_only": True,
        "hard_non_delegable": True,
        "can_produce_opposable_output": False,
    },
    "S5": {
        "function_contains": "LAYER",
        "level_a_decides": True,
        "level_b_support_only": True,
        "hard_non_delegable": True,
        "can_produce_opposable_output": False,
    },
    "S8": {
        "function_contains": "SCM-PRO",
        "level_a_decides": True,
        "level_b_support_only": True,
        "hard_non_delegable": True,
        "can_produce_opposable_output": False,
    },
    "S9": {
        "function_contains": "CRITIC",
        "level_a_decides": True,
        "level_b_support_only": True,
        "hard_non_delegable": True,
        "can_produce_opposable_output": False,
    },
    "S10": {
        "function_contains": "CF-ATTI",
        "level_a_decides": True,
        "level_b_support_only": False,
        "hard_non_delegable": True,
        "can_produce_opposable_output": False,
    },
    "S11": {
        "function_contains": "OUTPUT",
        "level_a_decides": True,
        "level_b_support_only": True,
        "hard_non_delegable": True,
        "can_produce_opposable_output": True,
    },
}


def load_json(path: Path) -> dict:
    assert path.exists(), f"File non trovato: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def load_registries() -> tuple[dict, dict]:
    return load_json(SEQUENCE_REGISTRY_PATH), load_json(GATE_REGISTRY_PATH)


def get_sequence_index(sequence_registry: dict, phase_id: str) -> int:
    for index, phase in enumerate(sequence_registry["phases"]):
        if phase["phase_id"] == phase_id:
            return index
    raise KeyError(f"Fase non trovata nel sequence registry: {phase_id}")


def test_expected_hard_non_delegable_matrix_is_exact() -> None:
    _, gate_registry = load_registries()

    actual = {
        phase_id
        for phase_id, cfg in gate_registry["phases"].items()
        if cfg.get("hard_non_delegable") is True
    }

    assert actual == set(EXPECTED_HARD_NON_DELEGABLE.keys())


def test_each_reserved_phase_matches_expected_non_delegability_contract() -> None:
    _, gate_registry = load_registries()

    for phase_id, expected in EXPECTED_HARD_NON_DELEGABLE.items():
        cfg = gate_registry["phases"][phase_id]

        assert expected["function_contains"] in cfg["function"]
        assert cfg["level_a_decides"] is expected["level_a_decides"]
        assert cfg["level_b_support_only"] is expected["level_b_support_only"]
        assert cfg["hard_non_delegable"] is expected["hard_non_delegable"]
        assert cfg["can_produce_opposable_output"] is expected["can_produce_opposable_output"]


def test_global_non_delegability_rules_are_active() -> None:
    sequence_registry, gate_registry = load_registries()

    seq_invariants = sequence_registry["invariants"]
    gate_rules = gate_registry["global_rules"]

    assert seq_invariants["level_b_cannot_decide"] is True
    assert seq_invariants["level_b_cannot_validate"] is True
    assert seq_invariants["level_b_cannot_close_m07"] is True
    assert seq_invariants["level_b_cannot_authorize_output"] is True

    assert gate_rules["level_b_never_decides"] is True
    assert gate_rules["level_b_never_validates"] is True
    assert gate_rules["level_b_never_closes_m07"] is True
    assert gate_rules["level_b_never_emits_go_no_go"] is True
    assert gate_rules["level_b_never_authorizes_opposable_output"] is True


def test_hard_non_delegable_phases_are_in_the_decisional_tail_of_the_chain() -> None:
    sequence_registry, _ = load_registries()

    phase_positions = {
        phase_id: get_sequence_index(sequence_registry, phase_id)
        for phase_id in EXPECTED_HARD_NON_DELEGABLE
    }

    assert phase_positions["S3"] < phase_positions["S4"] < phase_positions["S5"]
    assert phase_positions["S5"] < phase_positions["S8"] < phase_positions["S9"]
    assert phase_positions["S9"] < phase_positions["S10"] < phase_positions["S11"]


def test_m07_rac_layer_are_reserved_to_level_a_and_never_opposable_by_themselves() -> None:
    _, gate_registry = load_registries()

    for phase_id in ("S3", "S4", "S5"):
        cfg = gate_registry["phases"][phase_id]
        assert cfg["level_a_decides"] is True
        assert cfg["level_b_support_only"] is True
        assert cfg["hard_non_delegable"] is True
        assert cfg["can_produce_opposable_output"] is False


def test_manual_and_defensive_gates_are_reserved_to_level_a() -> None:
    _, gate_registry = load_registries()

    for phase_id in ("S8", "S9", "S10"):
        cfg = gate_registry["phases"][phase_id]
        assert cfg["level_a_decides"] is True
        assert cfg["hard_non_delegable"] is True


def test_s10_is_the_exclusive_final_go_no_go_gate() -> None:
    _, gate_registry = load_registries()
    s10 = gate_registry["phases"]["S10"]

    assert "GO" in s10["positive_outcomes"]
    assert "NO_GO" in s10["negative_outcomes"]
    assert "CF_ATTI_NO_GO_BLOCK" in s10["blocking_outcomes"]
    assert "If NO_GO_then_S11_FIRMA_READY_forbidden" in set(s10["conditional_rules"])

    assert s10["level_a_decides"] is True
    assert s10["level_b_support_only"] is False
    assert s10["hard_non_delegable"] is True


def test_only_s11_can_produce_terminally_opposable_output() -> None:
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


def test_output_remains_reserved_to_level_a_even_when_level_b_supports_documentally() -> None:
    _, gate_registry = load_registries()
    s11 = gate_registry["phases"]["S11"]

    assert s11["level_a_decides"] is True
    assert s11["level_b_support_only"] is True
    assert s11["hard_non_delegable"] is True
    assert s11["can_produce_opposable_output"] is True


def test_no_preparatory_phase_is_marked_hard_non_delegable_by_error() -> None:
    _, gate_registry = load_registries()

    preparatory_phase_ids = {"SPRE_D", "SPRE_F", "S0", "S0_BIS", "S0_TER", "S1", "S2", "S6", "S7"}
    for phase_id in preparatory_phase_ids:
        cfg = gate_registry["phases"][phase_id]
        assert cfg.get("hard_non_delegable") is not True, (
            f"La fase {phase_id} non dovrebbe essere marcata hard_non_delegable"
        )