from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from validators.level_b_release_gate_rules import build_suite_result, compute_release_decision, load_json, summarize_suite_results, validate_manifest_shape


def _manifest():
    return load_json(ROOT_DIR / "schemas" / "level_b_release_gate_manifest_v1.json")


def test_release_gate_returns_go_when_all_suites_pass() -> None:
    manifest = _manifest()
    manifest_problems = validate_manifest_shape(manifest)
    results = [
        build_suite_result(suite, "PASSED", 0, 0.01) for suite in manifest["required_suites"]
    ]
    decision, reasons = compute_release_decision(
        manifest=manifest,
        results=results,
        manifest_problems=manifest_problems,
        report_schema_exists=True,
    )
    assert decision == "GO"
    assert reasons == []
    summary = summarize_suite_results(results)
    assert summary["passed"] == len(results)
    assert summary["critical_failed"] == 0
    assert summary["golden_failed"] == 0


def test_release_gate_suspends_when_golden_suite_fails() -> None:
    manifest = _manifest()
    manifest_problems = validate_manifest_shape(manifest)
    results = []
    for suite in manifest["required_suites"]:
        outcome = "FAILED" if suite["kind"] == "golden_baseline" else "PASSED"
        return_code = 1 if outcome == "FAILED" else 0
        results.append(build_suite_result(suite, outcome, return_code, 0.02))
    decision, reasons = compute_release_decision(
        manifest=manifest,
        results=results,
        manifest_problems=manifest_problems,
        report_schema_exists=True,
    )
    assert decision == "SUSPEND"
    assert any("LB-GOLD-001" in reason for reason in reasons)
    summary = summarize_suite_results(results)
    assert summary["golden_failed"] == 1


def test_release_gate_errors_when_manifest_is_invalid() -> None:
    manifest = _manifest()
    broken_manifest = dict(manifest)
    broken_manifest.pop("required_suites", None)
    results = []
    problems = validate_manifest_shape(broken_manifest)
    decision, reasons = compute_release_decision(
        manifest=broken_manifest,
        results=results,
        manifest_problems=problems,
        report_schema_exists=True,
    )
    assert decision == "ERROR"
    assert reasons
