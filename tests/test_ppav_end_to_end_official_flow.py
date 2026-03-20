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

SUCCESS_PATH_STATUSES = {
    "SPRE_D": "READY",
    "SPRE_F": "PHASE_READY",
    "S0": "CLASSIFIED_STANDARD",
    "S0_BIS": "OK",
    "S0_TER": "OK",
    "S1": "PROVVEDIMENTO_GESTIONALE",
    "S2": "DB_LOCK_OK",
    "S3": "COMPLETO",
    "S4": "OK",
    "S5": "OPPONIBILE",
    "S6": "MODULES_OK",
    "S7": "VERDE",
    "S8": "GO",
    "S9": "OK",
    "S10": "GO",
    "S11": "OUTPUT_OK",
}


def load_json(path: Path) -> dict:
    assert path.exists(), f"File non trovato: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def load_registries() -> tuple[dict, dict]:
    return load_json(SEQUENCE_REGISTRY_PATH), load_json(GATE_REGISTRY_PATH)


def get_phase_order(sequence_registry: dict) -> List[str]:
    return [phase["phase_id"] for phase in sequence_registry["phases"]]


def next_phase_id(sequence_registry: dict, phase_id: str) -> str | None:
    for phase in sequence_registry["phases"]:
        if phase["phase_id"] == phase_id:
            return phase["next_phase_id"]
    raise KeyError(f"Fase non trovata nel sequence registry: {phase_id}")


def is_positive_status(gate_registry: dict, phase_id: str, status: str) -> bool:
    return status in gate_registry["phases"][phase_id]["positive_outcomes"]


def is_negative_status(gate_registry: dict, phase_id: str, status: str) -> bool:
    return status in gate_registry["phases"][phase_id]["negative_outcomes"]


def can_enter_phase(
    sequence_registry: dict,
    gate_registry: dict,
    history: Dict[str, str],
    target_phase_id: str,
) -> bool:
    order = get_phase_order(sequence_registry)

    if target_phase_id not in order:
        return False

    target_index = order.index(target_phase_id)

    if target_index == 0:
        return len(history) == 0

    previous_phase_id = order[target_index - 1]

    if previous_phase_id not in history:
        return False

    previous_status = history[previous_phase_id]
    previous_gate = gate_registry["phases"][previous_phase_id]

    expected_next = next_phase_id(sequence_registry, previous_phase_id)
    if expected_next != target_phase_id:
        return False

    if is_positive_status(gate_registry, previous_phase_id, previous_status):
        return target_phase_id in previous_gate["successor_phase_rules"]["allowed_if_positive"]

    if is_negative_status(gate_registry, previous_phase_id, previous_status):
        return target_phase_id not in previous_gate["successor_phase_rules"]["forbidden_if_negative"]

    return False


def can_emit_firma_ready(history: Dict[str, str]) -> bool:
    required = {
        "SPRE_D": "READY",
        "SPRE_F": "PHASE_READY",
        "S3": "COMPLETO",
        "S4": "OK",
        "S5": "OPPONIBILE",
        "S9": "OK",
        "S10": "GO",
    }

    for phase_id, expected_status in required.items():
        if history.get(phase_id) != expected_status:
            return False

    for phase_id in EXPECTED_PHASE_ORDER:
        if phase_id not in history:
            return False

    return True


def build_success_history() -> Dict[str, str]:
    return dict(SUCCESS_PATH_STATUSES)


def test_success_path_respects_official_sequence_and_reaches_s11() -> None:
    sequence_registry, gate_registry = load_registries()

    history: Dict[str, str] = {}

    for phase_id in EXPECTED_PHASE_ORDER:
        assert can_enter_phase(sequence_registry, gate_registry, history, phase_id), (
            f"Non e possibile entrare nella fase {phase_id} lungo il percorso ufficiale"
        )
        history[phase_id] = SUCCESS_PATH_STATUSES[phase_id]

    assert list(history.keys()) == EXPECTED_PHASE_ORDER
    assert history["S11"] == "OUTPUT_OK"


def test_success_path_allows_firma_ready_only_after_s10_go() -> None:
    history = build_success_history()

    assert history["S10"] == "GO"
    assert can_emit_firma_ready(history) is True


def test_end_to_end_stops_when_s3_is_incomplete() -> None:
    sequence_registry, gate_registry = load_registries()

    history: Dict[str, str] = {}
    for phase_id in EXPECTED_PHASE_ORDER:
        assert can_enter_phase(sequence_registry, gate_registry, history, phase_id)
        history[phase_id] = SUCCESS_PATH_STATUSES[phase_id]
        if phase_id == "S3":
            history["S3"] = "INCOMPLETO"
            break

    assert can_enter_phase(sequence_registry, gate_registry, history, "S4") is False
    assert can_emit_firma_ready(history) is False


def test_end_to_end_denies_firma_ready_when_s5_is_non_opponibile() -> None:
    history = build_success_history()
    history["S5"] = "NON_OPPONIBILE"

    assert can_emit_firma_ready(history) is False


def test_end_to_end_denies_s10_when_s9_is_critico() -> None:
    sequence_registry, gate_registry = load_registries()
    history = build_success_history()
    history["S9"] = "CRITICO"

    assert can_enter_phase(sequence_registry, gate_registry, history, "S10") is False
    assert can_emit_firma_ready(history) is False


def test_end_to_end_denies_firma_ready_when_s10_is_no_go() -> None:
    history = build_success_history()
    history["S10"] = "NO_GO"

    assert can_emit_firma_ready(history) is False


def test_end_to_end_rejects_phase_skip_from_s3_to_s5() -> None:
    sequence_registry, gate_registry = load_registries()

    history: Dict[str, str] = {}
    for phase_id in ["SPRE_D", "SPRE_F", "S0", "S0_BIS", "S0_TER", "S1", "S2", "S3"]:
        assert can_enter_phase(sequence_registry, gate_registry, history, phase_id)
        history[phase_id] = SUCCESS_PATH_STATUSES[phase_id]

    assert can_enter_phase(sequence_registry, gate_registry, history, "S5") is False


def test_end_to_end_rejects_starting_from_phase_other_than_spre_d() -> None:
    sequence_registry, gate_registry = load_registries()
    empty_history: Dict[str, str] = {}

    assert can_enter_phase(sequence_registry, gate_registry, empty_history, "S0") is False
    assert can_enter_phase(sequence_registry, gate_registry, empty_history, "S11") is False
    assert can_enter_phase(sequence_registry, gate_registry, empty_history, "SPRE_D") is True