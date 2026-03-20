from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

ROOT = Path(__file__).resolve().parents[1]
GATE_REGISTRY_PATH = ROOT / "schemas" / "ppav_phase_gate_registry_v1.json"

SUCCESS_HISTORY = {
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
}


def load_gate_registry() -> dict:
    assert GATE_REGISTRY_PATH.exists(), (
        f"Registry gate non trovato: {GATE_REGISTRY_PATH}"
    )
    return json.loads(GATE_REGISTRY_PATH.read_text(encoding="utf-8"))


def evaluate_output_regime(history: Dict[str, str]) -> Tuple[str, bool]:
    """
    Restituisce:
    - layer regime ammissibile: LAYER_ATTO oppure L_AR_ONLY
    - flag FIRMA_READY
    """
    if history.get("S10") != "GO":
        return "L_AR_ONLY", False

    if history.get("S5") != "OPPONIBILE":
        return "L_AR_ONLY", False

    if history.get("S3") != "COMPLETO":
        return "L_AR_ONLY", False

    if history.get("S4") != "OK":
        return "L_AR_ONLY", False

    if history.get("S9") != "OK":
        return "L_AR_ONLY", False

    return "LAYER_ATTO", True


def test_gate_registry_contains_terminal_output_rules() -> None:
    data = load_gate_registry()
    s11 = data["phases"]["S11"]

    rules = set(s11["conditional_rules"])

    assert "If any_previous_phase_blocked_then_FIRMA_READY_FALSE" in rules
    assert "If S5=NON_OPPONIBILE_then_LAYER_ATTO_FIRMA_READY_forbidden" in rules
    assert "If S10!=GO_then_FIRMA_READY_TRUE_forbidden" in rules


def test_success_case_allows_layer_atto_and_firma_ready() -> None:
    layer, firma_ready = evaluate_output_regime(dict(SUCCESS_HISTORY))

    assert layer == "LAYER_ATTO"
    assert firma_ready is True


def test_s10_no_go_forces_l_ar_only_and_denies_firma_ready() -> None:
    history = dict(SUCCESS_HISTORY)
    history["S10"] = "NO_GO"

    layer, firma_ready = evaluate_output_regime(history)

    assert layer == "L_AR_ONLY"
    assert firma_ready is False


def test_s5_non_opponibile_forces_l_ar_only_and_denies_firma_ready() -> None:
    history = dict(SUCCESS_HISTORY)
    history["S5"] = "NON_OPPONIBILE"

    layer, firma_ready = evaluate_output_regime(history)

    assert layer == "L_AR_ONLY"
    assert firma_ready is False


def test_s3_incomplete_forbids_firma_ready_even_if_s10_is_go() -> None:
    history = dict(SUCCESS_HISTORY)
    history["S3"] = "INCOMPLETO"

    layer, firma_ready = evaluate_output_regime(history)

    assert layer == "L_AR_ONLY"
    assert firma_ready is False


def test_s4_blocco_forbids_firma_ready_even_if_s10_is_go() -> None:
    history = dict(SUCCESS_HISTORY)
    history["S4"] = "BLOCCO"

    layer, firma_ready = evaluate_output_regime(history)

    assert layer == "L_AR_ONLY"
    assert firma_ready is False


def test_s9_critico_forbids_firma_ready() -> None:
    history = dict(SUCCESS_HISTORY)
    history["S9"] = "CRITICO"

    layer, firma_ready = evaluate_output_regime(history)

    assert layer == "L_AR_ONLY"
    assert firma_ready is False


def test_missing_required_phase_result_forbids_firma_ready() -> None:
    history = dict(SUCCESS_HISTORY)
    history.pop("S4")

    layer, firma_ready = evaluate_output_regime(history)

    assert layer == "L_AR_ONLY"
    assert firma_ready is False


def test_only_s11_can_be_terminally_opposable_in_registry() -> None:
    data = load_gate_registry()

    opposable_phase_ids = [
        phase_id
        for phase_id, cfg in data["phases"].items()
        if cfg["can_produce_opposable_output"] is True
    ]

    assert opposable_phase_ids == ["S11"]


def test_s5_registry_explicitly_degrades_to_l_ar_only_when_non_opponibile() -> None:
    data = load_gate_registry()
    s5 = data["phases"]["S5"]

    assert "NON_OPPONIBILE" in s5["negative_outcomes"]
    assert "If NON_OPPONIBILE_then_S11_LAYER_ATTO_FIRMA_READY_forbidden" in set(
        s5["conditional_rules"]
    )


def test_s10_registry_explicitly_blocks_firma_ready_when_no_go() -> None:
    data = load_gate_registry()
    s10 = data["phases"]["S10"]

    assert "NO_GO" in s10["negative_outcomes"]
    assert "If NO_GO_then_S11_FIRMA_READY_forbidden" in set(
        s10["conditional_rules"]
    )