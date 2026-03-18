from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from validators.level_b_release_gate_rules import load_json, validate_manifest_shape


def test_release_gate_manifest_structure_is_valid() -> None:
    manifest_path = ROOT_DIR / "schemas" / "level_b_release_gate_manifest_v1.json"
    manifest = load_json(manifest_path)
    problems = validate_manifest_shape(manifest)
    assert not problems, f"Manifest release gate non valido: {problems}"


def test_release_gate_manifest_includes_non_delegation_clauses() -> None:
    manifest = load_json(ROOT_DIR / "schemas" / "level_b_release_gate_manifest_v1.json")
    clauses = manifest.get("explicit_non_delegation", [])
    assert any("M07-LPR" in clause for clause in clauses)
    assert any("Final Compliance Gate of Level A" in clause for clause in clauses)
    assert any("opposable outputs" in clause for clause in clauses)
