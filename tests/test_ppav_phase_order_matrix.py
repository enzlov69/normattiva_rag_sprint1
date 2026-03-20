from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEQUENCE_REGISTRY_PATH = ROOT / "schemas" / "ppav_phase_sequence_registry_v1.json"

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

EXPECTED_ALWAYS_ON_PRESIDIA = {
    "OP_ANTI_ALLUCINAZIONI_NORMATIVE",
    "OP_DOPPIA_LENTE_RATIO",
    "OP_COT++",
}


def load_sequence_registry() -> dict:
    assert SEQUENCE_REGISTRY_PATH.exists(), (
        f"Registry non trovato: {SEQUENCE_REGISTRY_PATH}"
    )
    return json.loads(SEQUENCE_REGISTRY_PATH.read_text(encoding="utf-8"))


def test_sequence_registry_file_exists() -> None:
    assert SEQUENCE_REGISTRY_PATH.exists(), (
        f"Manca il file registry: {SEQUENCE_REGISTRY_PATH}"
    )


def test_phase_order_matches_official_canonical_sequence() -> None:
    data = load_sequence_registry()
    phases = data["phases"]

    actual_phase_order = [phase["phase_id"] for phase in phases]
    assert actual_phase_order == EXPECTED_PHASE_ORDER


def test_phase_ordinals_are_contiguous_and_start_from_one() -> None:
    data = load_sequence_registry()
    phases = data["phases"]

    actual_ordinals = [phase["ordinal"] for phase in phases]
    expected_ordinals = list(range(1, len(phases) + 1))

    assert actual_ordinals == expected_ordinals


def test_each_phase_points_to_adjacent_previous_and_next() -> None:
    data = load_sequence_registry()
    phases = data["phases"]

    for index, phase in enumerate(phases):
        expected_previous = None if index == 0 else phases[index - 1]["phase_id"]
        expected_next = None if index == len(phases) - 1 else phases[index + 1]["phase_id"]

        assert phase["previous_phase_id"] == expected_previous, (
            f"La fase {phase['phase_id']} ha previous_phase_id non coerente"
        )
        assert phase["next_phase_id"] == expected_next, (
            f"La fase {phase['phase_id']} ha next_phase_id non coerente"
        )


def test_no_duplicate_phase_ids_exist() -> None:
    data = load_sequence_registry()
    phases = data["phases"]

    phase_ids = [phase["phase_id"] for phase in phases]
    assert len(phase_ids) == len(set(phase_ids))


def test_first_and_last_phase_are_fixed() -> None:
    data = load_sequence_registry()
    phases = data["phases"]

    assert phases[0]["phase_id"] == "SPRE_D"
    assert phases[-1]["phase_id"] == "S11"

    assert phases[0]["previous_phase_id"] is None
    assert phases[-1]["next_phase_id"] is None


def test_only_s11_can_produce_opposable_output() -> None:
    data = load_sequence_registry()
    phases = data["phases"]

    opposable_phases = [
        phase["phase_id"]
        for phase in phases
        if phase["can_produce_opposable_output"] is True
    ]

    assert opposable_phases == ["S11"]


def test_registry_invariants_required_by_cantiere_are_enabled() -> None:
    data = load_sequence_registry()
    invariants = data["invariants"]

    assert invariants["no_phase_skips"] is True
    assert invariants["strict_adjacent_transition_only"] is True
    assert invariants["previous_blocked_forbids_useful_successor_output"] is True
    assert invariants["no_firma_ready_before_s10_go"] is True
    assert invariants["level_b_cannot_decide"] is True
    assert invariants["level_b_cannot_validate"] is True
    assert invariants["level_b_cannot_close_m07"] is True
    assert invariants["level_b_cannot_authorize_output"] is True
    assert invariants["root_tests_mandatory"] is True


def test_always_on_presidia_are_present() -> None:
    data = load_sequence_registry()

    actual_presidia = set(data["always_on_presidia"])
    assert actual_presidia == EXPECTED_ALWAYS_ON_PRESIDIA


def test_registry_baselines_are_declared() -> None:
    data = load_sequence_registry()
    baseline = data["baseline"]

    assert baseline["ab_master"] == "stable-final-ab-master-cycle-v1"
    assert baseline["local_m07"] == "stable-m07-documentary-support-acceptance-pack-v1"
    assert baseline["local_fip_ind"] == "stable-fip-ind-gate-foundation-v1"