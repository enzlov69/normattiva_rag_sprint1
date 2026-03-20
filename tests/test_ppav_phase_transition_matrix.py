from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
SEQUENCE_REGISTRY_PATH = ROOT / "schemas" / "ppav_phase_sequence_registry_v1.json"
GATE_REGISTRY_PATH = ROOT / "schemas" / "ppav_phase_gate_registry_v1.json"

EXPECTED_PHASE_ORDER = [
    "SPRE_D",
    "SPRE_F",
    "S0",
    "S0_BIS",
    "S0_TER",
    "S1",
    "S2",
    "S3",
    "S4",
    "S5",
    "S6",
    "S7",
    "S8",
    "S9",
    "S10",
    "S11",
]


def load_json(path: Path) -> dict:
    assert path.exists(), f"File non trovato: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def load_registries() -> tuple[dict, dict]:
    return load_json(SEQUENCE_REGISTRY_PATH), load_json(GATE_REGISTRY_PATH)


def get_phase_order(sequence_registry: dict) -> List[str]:
    return [phase["phase_id"] for phase in sequence_registry["phases"]]


def get_next_phase(sequence_registry: dict, phase_id: str) -> str | None:
    for phase in sequence_registry["phases"]:
        if phase["phase_id"] == phase_id:
            return phase["next_phase_id"]
    raise KeyError(f"Fase non trovata: {phase_id}")


def get_previous_phase(sequence_registry: dict, phase_id: str) -> str | None:
    for phase in sequence_registry["phases"]:
        if phase["phase_id"] == phase_id:
            return phase["previous_phase_id"]
    raise KeyError(f"Fase non trovata: {phase_id}")


def is_positive_status(gate_registry: dict, phase_id: str, status: str) -> bool:
    return status in gate_registry["phases"][phase_id]["positive_outcomes"]


def is_negative_status(gate_registry: dict, phase_id: str, status: str) -> bool:
    return status in gate_registry["phases"][phase_id]["negative_outcomes"]


def can_transition(
    sequence_registry: dict,
    gate_registry: dict,
    from_phase_id: str,
    from_status: str,
    to_phase_id: str,
) -> bool:
    next_phase = get_next_phase(sequence_registry, from_phase_id)
    if next_phase != to_phase_id:
        return False

    phase_gate = gate_registry["phases"][from_phase_id]

    if is_positive_status(gate_registry, from_phase_id, from_status):
        return to_phase_id in phase_gate["successor_phase_rules"]["allowed_if_positive"]

    if is_negative_status(gate_registry, from_phase_id, from_status):
        return to_phase_id not in phase_gate["successor_phase_rules"]["forbidden_if_negative"]

    return False


def test_all_sequence_phases_exist_in_gate_registry() -> None:
    sequence_registry, gate_registry = load_registries()

    sequence_phase_ids = {
        phase["phase_id"]
        for phase in sequence_registry["phases"]
    }
    gate_phase_ids = set(gate_registry["phases"].keys())

    assert sequence_phase_ids == gate_phase_ids


def test_every_non_terminal_phase_has_exactly_one_adjacent_next_phase() -> None:
    sequence_registry, _ = load_registries()
    phase_order = get_phase_order(sequence_registry)

    for index, phase_id in enumerate(phase_order[:-1]):
        expected_next = phase_order[index + 1]
        assert get_next_phase(sequence_registry, phase_id) == expected_next

    assert get_next_phase(sequence_registry, "S11") is None


def test_every_non_initial_phase_has_exactly_one_adjacent_previous_phase() -> None:
    sequence_registry, _ = load_registries()
    phase_order = get_phase_order(sequence_registry)

    for index, phase_id in enumerate(phase_order[1:], start=1):
        expected_previous = phase_order[index - 1]
        assert get_previous_phase(sequence_registry, phase_id) == expected_previous

    assert get_previous_phase(sequence_registry, "SPRE_D") is None


def test_each_non_terminal_phase_allows_only_its_adjacent_successor_when_positive() -> None:
    sequence_registry, gate_registry = load_registries()
    phase_order = get_phase_order(sequence_registry)

    for phase_id in phase_order[:-1]:
        expected_next = get_next_phase(sequence_registry, phase_id)
        allowed_if_positive = gate_registry["phases"][phase_id]["successor_phase_rules"]["allowed_if_positive"]

        assert allowed_if_positive == [expected_next], (
            f"La fase {phase_id} deve consentire solo la transizione adiacente positiva verso {expected_next}"
        )


def test_terminal_phase_s11_has_no_successor_transitions() -> None:
    _, gate_registry = load_registries()
    s11 = gate_registry["phases"]["S11"]["successor_phase_rules"]

    assert s11["allowed_if_positive"] == []
    assert s11["forbidden_if_negative"] == []


def test_all_non_terminal_negative_outcomes_forbid_the_adjacent_next_phase() -> None:
    sequence_registry, gate_registry = load_registries()
    phase_order = get_phase_order(sequence_registry)

    for phase_id in phase_order[:-1]:
        next_phase = get_next_phase(sequence_registry, phase_id)
        forbidden_if_negative = gate_registry["phases"][phase_id]["successor_phase_rules"]["forbidden_if_negative"]

        assert next_phase in forbidden_if_negative, (
            f"La fase {phase_id} deve vietare la fase successiva {next_phase} se l'esito e negativo"
        )


def test_every_phase_has_at_least_one_positive_negative_and_blocking_status_except_terminal_blockshape() -> None:
    _, gate_registry = load_registries()

    for phase_id, config in gate_registry["phases"].items():
        assert config["positive_outcomes"], f"{phase_id} priva di positive_outcomes"
        assert config["negative_outcomes"], f"{phase_id} priva di negative_outcomes"
        assert config["blocking_outcomes"], f"{phase_id} priva di blocking_outcomes"


def test_positive_transition_example_s4_to_s5_is_allowed() -> None:
    sequence_registry, gate_registry = load_registries()

    assert can_transition(
        sequence_registry,
        gate_registry,
        from_phase_id="S4",
        from_status="OK",
        to_phase_id="S5",
    ) is True


def test_negative_transition_example_s4_block_to_s5_is_forbidden() -> None:
    sequence_registry, gate_registry = load_registries()

    assert can_transition(
        sequence_registry,
        gate_registry,
        from_phase_id="S4",
        from_status="BLOCCO",
        to_phase_id="S5",
    ) is False


def test_non_adjacent_transition_example_s4_to_s6_is_always_forbidden() -> None:
    sequence_registry, gate_registry = load_registries()

    assert can_transition(
        sequence_registry,
        gate_registry,
        from_phase_id="S4",
        from_status="OK",
        to_phase_id="S6",
    ) is False


def test_spre_d_can_only_transition_to_spre_f_when_ready() -> None:
    sequence_registry, gate_registry = load_registries()

    assert can_transition(
        sequence_registry,
        gate_registry,
        from_phase_id="SPRE_D",
        from_status="READY",
        to_phase_id="SPRE_F",
    ) is True

    assert can_transition(
        sequence_registry,
        gate_registry,
        from_phase_id="SPRE_D",
        from_status="NOT_READY",
        to_phase_id="SPRE_F",
    ) is False


def test_s10_can_transition_to_s11_only_if_go() -> None:
    sequence_registry, gate_registry = load_registries()

    assert can_transition(
        sequence_registry,
        gate_registry,
        from_phase_id="S10",
        from_status="GO",
        to_phase_id="S11",
    ) is True

    assert can_transition(
        sequence_registry,
        gate_registry,
        from_phase_id="S10",
        from_status="NO_GO",
        to_phase_id="S11",
    ) is False


def test_preconditions_reference_the_expected_previous_phase_family() -> None:
    _, gate_registry = load_registries()
    phases = gate_registry["phases"]

    assert "SPRE_D=READY" in phases["SPRE_F"]["preconditions"]
    assert "SPRE_F=PHASE_READY" in phases["S0"]["preconditions"]
    assert "S0 in stato classificato" in phases["S0_BIS"]["preconditions"]
    assert "S0_BIS non bloccato" in phases["S0_TER"]["preconditions"]
    assert "S0_TER=OK" in phases["S1"]["preconditions"]
    assert "S1 non bloccato" in phases["S2"]["preconditions"]
    assert "S2 valido" in phases["S3"]["preconditions"]
    assert "S3=COMPLETO" in phases["S4"]["preconditions"]
    assert "S4=OK" in phases["S5"]["preconditions"]
    assert "S5 definito" in phases["S6"]["preconditions"]
    assert "S6=MODULES_OK" in phases["S7"]["preconditions"]
    assert "S7 non ROSSO" in phases["S8"]["preconditions"]
    assert "S8 non NO_GO" in phases["S9"]["preconditions"]
    assert "S9 non CRITICO" in phases["S10"]["preconditions"]
    assert "S10=GO" in phases["S11"]["preconditions"]