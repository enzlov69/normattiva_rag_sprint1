from __future__ import annotations

from pathlib import Path

from validators.level_b_change_control_rules import (
    build_change_control_report,
    evaluate_change_request,
    load_json,
)


BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = BASE_DIR / "schemas" / "level_b_change_request_schema_v1.json"
REGISTRY_PATH = BASE_DIR / "schemas" / "level_b_change_control_registry_v1.json"
FIXTURES_DIR = BASE_DIR / "tests" / "fixtures" / "level_b_change_requests"


def _load(relative_path: str) -> dict:
    return load_json(FIXTURES_DIR / relative_path)


def test_change_control_pass_case_allows_non_fondative_update() -> None:
    schema = load_json(SCHEMA_PATH)
    registry = load_json(REGISTRY_PATH)
    request = _load("pass/cc_pass_001_additive_non_fondative.json")
    decision, reasons, details = evaluate_change_request(
        request=request,
        schema=schema,
        registry=registry,
        base_dir=BASE_DIR,
        git_status_clean=True,
    )
    assert decision == "ALLOW"
    assert reasons == []
    assert details["missing_suites"] == []


def test_change_control_hold_case_when_protected_asset_lacks_required_approval() -> None:
    schema = load_json(SCHEMA_PATH)
    registry = load_json(REGISTRY_PATH)
    request = _load("hold/cc_hold_001_protected_asset_missing_approval.json")
    decision, reasons, details = evaluate_change_request(
        request=request,
        schema=schema,
        registry=registry,
        base_dir=BASE_DIR,
        git_status_clean=True,
    )
    assert decision == "HOLD"
    assert "PROTECTED_ASSET_APPROVALS_INCOMPLETE" in reasons
    assert "metodo_owner" in details["missing_approval_roles"]


def test_change_control_rejects_runner_touch() -> None:
    schema = load_json(SCHEMA_PATH)
    registry = load_json(REGISTRY_PATH)
    request = _load("reject/cc_reject_001_runner_touch.json")
    decision, reasons, _details = evaluate_change_request(
        request=request,
        schema=schema,
        registry=registry,
        base_dir=BASE_DIR,
        git_status_clean=True,
    )
    assert decision == "REJECT"
    assert "TOUCHPOINT_FORBIDDEN_SCOPE" in reasons


def test_change_control_rejects_m07_closure_by_level_b() -> None:
    schema = load_json(SCHEMA_PATH)
    registry = load_json(REGISTRY_PATH)
    request = _load("reject/cc_reject_002_enables_m07_closure.json")
    decision, reasons, _details = evaluate_change_request(
        request=request,
        schema=schema,
        registry=registry,
        base_dir=BASE_DIR,
        git_status_clean=True,
    )
    assert decision == "REJECT"
    assert "ENABLES_M07_CLOSURE_BY_LEVEL_B" in reasons


def test_change_control_report_contains_next_action() -> None:
    schema = load_json(SCHEMA_PATH)
    registry = load_json(REGISTRY_PATH)
    request = _load("pass/cc_pass_001_additive_non_fondative.json")
    decision, reasons, details = evaluate_change_request(
        request=request,
        schema=schema,
        registry=registry,
        base_dir=BASE_DIR,
        git_status_clean=True,
    )
    report = build_change_control_report(
        registry=registry,
        request=request,
        decision=decision,
        reasons=reasons,
        details=details,
    )
    assert report["decision"] == "ALLOW"
    assert report["next_action"].startswith("Apply the offline Level B change")
