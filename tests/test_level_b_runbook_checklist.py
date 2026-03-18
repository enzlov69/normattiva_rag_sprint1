from __future__ import annotations

from pathlib import Path

from validators.level_b_runbook_rules import load_json, validate_runbook_checklist_shape


BASE_DIR = Path(__file__).resolve().parents[1]
CHECKLIST_PATH = BASE_DIR / "schemas" / "level_b_runbook_checklist_v1.json"
REPORT_SCHEMA_PATH = BASE_DIR / "schemas" / "level_b_runbook_preflight_report_schema_v1.json"


def test_runbook_checklist_shape_is_valid() -> None:
    checklist = load_json(CHECKLIST_PATH)
    problems = validate_runbook_checklist_shape(checklist)
    assert problems == []


def test_runbook_schema_files_exist() -> None:
    assert CHECKLIST_PATH.exists()
    assert REPORT_SCHEMA_PATH.exists()
