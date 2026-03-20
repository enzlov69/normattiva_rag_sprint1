from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_REGISTRY_PATH = ROOT / "schemas" / "ppav_phase_gate_registry_v1.json"


def load_gate_registry() -> dict:
    assert GATE_REGISTRY_PATH.exists(), (
        f"Registry gate non trovato: {GATE_REGISTRY_PATH}"
    )
    return json.loads(GATE_REGISTRY_PATH.read_text(encoding="utf-8"))


def phase(data: dict, phase_id: str) -> dict:
    return data["phases"][phase_id]


def test_gate_registry_file_exists() -> None:
    assert GATE_REGISTRY_PATH.exists(), (
        f"Manca il file registry gate: {GATE_REGISTRY_PATH}"
    )


def test_global_block_rules_are_enabled() -> None:
    data = load_gate_registry()
    rules = data["global_rules"]

    assert rules["no_phase_skips"] is True
    assert rules["adjacent_transitions_only"] is True
    assert rules["useful_successor_output_forbidden_if_previous_invalid_or_incomplete"] is True
    assert rules["no_firma_ready_before_s10_go"] is True
    assert rules["level_b_never_decides"] is True
    assert rules["level_b_never_validates"] is True
    assert rules["level_b_never_closes_m07"] is True
    assert rules["level_b_never_emits_go_no_go"] is True
    assert rules["level_b_never_authorizes_opposable_output"] is True
    assert rules["cotpp_is_summary_only"] is True
    assert rules["root_tests_required"] is True


def test_s3_incomplete_blocks_s4_and_all_useful_downstream() -> None:
    data = load_gate_registry()
    s3 = phase(data, "S3")

    assert "INCOMPLETO" in s3["negative_outcomes"]
    assert "M07_INCOMPLETE_BLOCK" in s3["blocking_outcomes"]

    forbidden = set(s3["successor_phase_rules"]["forbidden_if_negative"])
    assert "S4" in forbidden
    assert "S5" in forbidden
    assert "S10" in forbidden
    assert "S11" in forbidden


def test_s4_requires_s3_complete() -> None:
    data = load_gate_registry()
    s4 = phase(data, "S4")

    assert "S3=COMPLETO" in s4["preconditions"]


def test_s5_non_opponibile_forbids_firma_ready_at_s11() -> None:
    data = load_gate_registry()
    s5 = phase(data, "S5")

    assert "NON_OPPONIBILE" in s5["negative_outcomes"]
    assert "OUTPUT_NOT_OPPONIBILE_BLOCK" in s5["blocking_outcomes"]

    rules = set(s5["conditional_rules"])
    assert "If NON_OPPONIBILE_then_S11_LAYER_ATTO_FIRMA_READY_forbidden" in rules


def test_s9_critico_blocks_s10_go() -> None:
    data = load_gate_registry()
    s9 = phase(data, "S9")

    assert "CRITICO" in s9["negative_outcomes"]
    assert "CRITIC_V4_BLOCK" in s9["blocking_outcomes"]

    rules = set(s9["conditional_rules"])
    assert "If CRITICO_then_S10_GO_forbidden" in rules

    forbidden = set(s9["successor_phase_rules"]["forbidden_if_negative"])
    assert "S10" in forbidden
    assert "S11" in forbidden


def test_s10_no_go_blocks_s11_firma_ready() -> None:
    data = load_gate_registry()
    s10 = phase(data, "S10")

    assert "NO_GO" in s10["negative_outcomes"]
    assert "CF_ATTI_NO_GO_BLOCK" in s10["blocking_outcomes"]

    rules = set(s10["conditional_rules"])
    assert "If NO_GO_then_S11_FIRMA_READY_forbidden" in rules

    forbidden = set(s10["successor_phase_rules"]["forbidden_if_negative"])
    assert "S11" in forbidden


def test_s11_restates_terminal_firma_ready_guards() -> None:
    data = load_gate_registry()
    s11 = phase(data, "S11")

    rules = set(s11["conditional_rules"])
    assert "If any_previous_phase_blocked_then_FIRMA_READY_FALSE" in rules
    assert "If S5=NON_OPPONIBILE_then_LAYER_ATTO_FIRMA_READY_forbidden" in rules
    assert "If S10!=GO_then_FIRMA_READY_TRUE_forbidden" in rules


def test_non_delegable_decisional_phases_are_reserved_to_level_a() -> None:
    data = load_gate_registry()

    reserved_phase_ids = ["S3", "S4", "S5", "S8", "S9", "S10", "S11"]
    for phase_id in reserved_phase_ids:
        current = phase(data, phase_id)
        assert current["level_a_decides"] is True, (
            f"La fase {phase_id} deve restare governata dal Livello A"
        )

    assert phase(data, "S3")["hard_non_delegable"] is True
    assert phase(data, "S4")["hard_non_delegable"] is True
    assert phase(data, "S5")["hard_non_delegable"] is True
    assert phase(data, "S8")["hard_non_delegable"] is True
    assert phase(data, "S9")["hard_non_delegable"] is True
    assert phase(data, "S10")["hard_non_delegable"] is True
    assert phase(data, "S11")["hard_non_delegable"] is True


def test_cf_atti_is_exclusive_final_gate_of_level_a() -> None:
    data = load_gate_registry()
    s10 = phase(data, "S10")

    assert s10["level_a_decides"] is True
    assert s10["level_b_support_only"] is False
    assert s10["can_produce_opposable_output"] is False


def test_only_s11_can_be_terminally_opposable_in_gate_registry() -> None:
    data = load_gate_registry()

    opposable = [
        phase_id
        for phase_id, cfg in data["phases"].items()
        if cfg["can_produce_opposable_output"] is True
    ]
    assert opposable == ["S11"]