from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "MATRICE_TEST_UFFICIALE_PPAV_S0_S11_v1.md"
SEQUENCE_REGISTRY_PATH = ROOT / "schemas" / "ppav_phase_sequence_registry_v1.json"
GATE_REGISTRY_PATH = ROOT / "schemas" / "ppav_phase_gate_registry_v1.json"

CURRENT_TRANCHE_REQUIRED_FILES = [
    ROOT / "docs" / "MATRICE_TEST_UFFICIALE_PPAV_S0_S11_v1.md",
    ROOT / "schemas" / "ppav_phase_sequence_registry_v1.json",
    ROOT / "schemas" / "ppav_phase_gate_registry_v1.json",
    ROOT / "tests" / "test_ppav_phase_order_matrix.py",
    ROOT / "tests" / "test_ppav_gate_block_propagation.py",
    ROOT / "tests" / "test_ppav_end_to_end_official_flow.py",
    ROOT / "tests" / "test_ppav_phase_transition_matrix.py",
    ROOT / "tests" / "test_ppav_output_firma_ready_rules.py",
    ROOT / "tests" / "test_ppav_level_b_subordination.py",
    ROOT / "tests" / "test_ppav_non_delegability_matrix.py",
    ROOT / "tests" / "test_ppav_repo_coverage_integrity.py",
]

EXPECTED_DOC_TOKENS = [
    "MATRICE TEST UFFICIALE PPAV S0–S11",
    "S-PRE/D",
    "S-PRE/F",
    "S0 – FASE 0",
    "S0-bis – FASE 0-bis",
    "S0-ter – FASE 0-ter",
    "S1 – FIP-IND",
    "S2 – RAP-ATTI",
    "S3 – M07-LPR",
    "S4 – RAC",
    "S5 – LAYER",
    "S6 – MODULI PPAV",
    "S7 – CS-PPAV",
    "S8 – SCM-PRO",
    "S9 – CRITIC v4",
    "S10 – CF-ATTI",
    "S11 – OUTPUT",
    "nessun salto di fase",
    "nessuna produzione `FIRMA_READY` prima di `S10 = GO`",
]

ALLOWED_TEST_CLASSES = {"UNIT", "TRN", "E2E", "BLK", "ND", "LB", "REP"}

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


def load_doc() -> str:
    assert DOC_PATH.exists(), f"Documento non trovato: {DOC_PATH}"
    return DOC_PATH.read_text(encoding="utf-8")


def load_registries() -> tuple[dict, dict]:
    return load_json(SEQUENCE_REGISTRY_PATH), load_json(GATE_REGISTRY_PATH)


def test_current_tranche_required_files_exist() -> None:
    missing = [str(path) for path in CURRENT_TRANCHE_REQUIRED_FILES if not path.exists()]
    assert missing == [], f"File obbligatori mancanti: {missing}"


def test_no_misplaced_python_test_file_exists_under_schemas() -> None:
    misplaced = sorted(
        str(path.relative_to(ROOT))
        for path in (ROOT / "schemas").glob("test_*.py")
    )
    assert misplaced == [], f"Trovati test Python fuori posto sotto schemas/: {misplaced}"


def test_matrix_document_contains_canonical_phases_and_core_rules() -> None:
    doc_text = load_doc()

    for token in EXPECTED_DOC_TOKENS:
        assert token in doc_text, f"Token documentale mancante: {token}"


def test_sequence_and_gate_registries_share_the_same_phase_universe() -> None:
    sequence_registry, gate_registry = load_registries()

    sequence_ids = [phase["phase_id"] for phase in sequence_registry["phases"]]
    gate_ids = list(gate_registry["phases"].keys())

    assert sequence_ids == EXPECTED_PHASE_ORDER
    assert sequence_ids == gate_ids


def test_sequence_registry_order_matches_current_tranche_expectation() -> None:
    sequence_registry, _ = load_registries()

    actual = [phase["phase_id"] for phase in sequence_registry["phases"]]
    assert actual == EXPECTED_PHASE_ORDER


def test_gate_registry_test_classes_are_all_officially_allowed() -> None:
    _, gate_registry = load_registries()

    for phase_id, cfg in gate_registry["phases"].items():
        actual_classes = set(cfg["test_classes"])
        assert actual_classes.issubset(ALLOWED_TEST_CLASSES), (
            f"La fase {phase_id} contiene classi di test non ammesse: {actual_classes - ALLOWED_TEST_CLASSES}"
        )
        assert len(actual_classes) >= 1, f"La fase {phase_id} non ha classi di test"


def test_gate_registry_has_minimal_repo_presidia_for_every_phase() -> None:
    _, gate_registry = load_registries()

    for phase_id, cfg in gate_registry["phases"].items():
        repo_presidia = cfg["repo_presidia"]
        assert isinstance(repo_presidia, list)
        assert len(repo_presidia) >= 1, f"La fase {phase_id} non ha repo_presidia dichiarati"


def test_current_root_test_suite_files_are_all_under_tests_directory() -> None:
    expected_relative = {
        "tests/test_ppav_phase_order_matrix.py",
        "tests/test_ppav_gate_block_propagation.py",
        "tests/test_ppav_end_to_end_official_flow.py",
        "tests/test_ppav_phase_transition_matrix.py",
        "tests/test_ppav_output_firma_ready_rules.py",
        "tests/test_ppav_level_b_subordination.py",
        "tests/test_ppav_non_delegability_matrix.py",
        "tests/test_ppav_repo_coverage_integrity.py",
    }

    actual_relative = {
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in (ROOT / "tests").glob("test_ppav_*.py")
    }

    assert expected_relative.issubset(actual_relative), (
        f"Suite ROOT PPAV incompleta. Mancano: {sorted(expected_relative - actual_relative)}"
    )


def test_registry_files_are_referenced_in_current_tranche_assets() -> None:
    doc_text = load_doc()

    assert "schemas/ppav_phase_sequence_registry_v1.json" in doc_text
    assert "schemas/ppav_phase_gate_registry_v1.json" in doc_text


def test_sequence_registry_declares_root_tests_as_mandatory() -> None:
    sequence_registry, _ = load_registries()

    assert sequence_registry["invariants"]["root_tests_mandatory"] is True


def test_gate_registry_declares_root_tests_as_mandatory() -> None:
    _, gate_registry = load_registries()

    assert gate_registry["global_rules"]["root_tests_required"] is True