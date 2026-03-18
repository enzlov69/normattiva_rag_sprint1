"""Helper offline per il Release Gate del Livello B.

Il modulo resta fuori da runner, runtime, retrieval e bridge applicativo.
Serve solo a:
- validare il manifest del gate;
- risolvere i percorsi delle suite;
- derivare l'esito GO/SUSPEND/ERROR;
- costruire il report strutturato.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

ALLOWED_OUTCOMES = {"PASSED", "FAILED", "ERROR", "MISSING", "SKIPPED"}
SUSPEND_TRIGGER_OUTCOMES = {"FAILED", "ERROR", "MISSING"}


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest_shape(manifest: Dict[str, Any]) -> List[str]:
    problems: List[str] = []

    required_root = {
        "manifest_id",
        "manifest_version",
        "gate_scope",
        "required_suites",
        "release_rules",
        "report_defaults",
    }
    missing_root = sorted(required_root - set(manifest.keys()))
    if missing_root:
        problems.append(f"Missing root keys: {', '.join(missing_root)}")

    suites = manifest.get("required_suites")
    if not isinstance(suites, list) or not suites:
        problems.append("required_suites must be a non-empty list")
        return problems

    seen_ids = set()
    seen_paths = set()
    golden_present = False
    for idx, suite in enumerate(suites):
        if not isinstance(suite, dict):
            problems.append(f"required_suites[{idx}] must be an object")
            continue
        for key in ("suite_id", "path", "kind", "critical"):
            if key not in suite:
                problems.append(f"required_suites[{idx}] missing key '{key}'")
        suite_id = suite.get("suite_id")
        path = suite.get("path")
        kind = suite.get("kind")
        critical = suite.get("critical")
        if suite_id in seen_ids:
            problems.append(f"Duplicate suite_id: {suite_id}")
        else:
            seen_ids.add(suite_id)
        if path in seen_paths:
            problems.append(f"Duplicate suite path: {path}")
        else:
            seen_paths.add(path)
        if not isinstance(critical, bool):
            problems.append(f"Suite {suite_id} has non-boolean critical flag")
        if kind == "golden_baseline":
            golden_present = True
    if not golden_present:
        problems.append("Manifest must include one golden_baseline suite")

    report_defaults = manifest.get("report_defaults")
    if not isinstance(report_defaults, dict):
        problems.append("report_defaults must be an object")
    else:
        for key in ("report_path", "report_schema_path"):
            if key not in report_defaults:
                problems.append(f"report_defaults missing key '{key}'")

    release_rules = manifest.get("release_rules")
    if not isinstance(release_rules, dict):
        problems.append("release_rules must be an object")
    else:
        outcomes = release_rules.get("admitted_suite_outcomes")
        if not isinstance(outcomes, list) or set(outcomes) != ALLOWED_OUTCOMES:
            problems.append("admitted_suite_outcomes must exactly match the allowed outcome set")

    return problems


def resolve_suite_path(base_dir: Path, relative_path: str) -> Path:
    return (base_dir / relative_path).resolve()


def suite_exists(base_dir: Path, suite_path: str) -> bool:
    return resolve_suite_path(base_dir, suite_path).exists()


def build_suite_result(suite: Dict[str, Any], outcome: str, return_code: int, duration_seconds: float,
                       stdout_excerpt: str = "", stderr_excerpt: str = "") -> Dict[str, Any]:
    if outcome not in ALLOWED_OUTCOMES:
        raise ValueError(f"Unsupported suite outcome: {outcome}")
    return {
        "suite_id": suite["suite_id"],
        "path": suite["path"],
        "kind": suite["kind"],
        "critical": suite["critical"],
        "outcome": outcome,
        "return_code": int(return_code),
        "duration_seconds": round(float(duration_seconds), 6),
        "stdout_excerpt": stdout_excerpt,
        "stderr_excerpt": stderr_excerpt,
    }


def summarize_suite_results(results: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = Counter(result["outcome"] for result in results)
    return {
        "total": len(results),
        "passed": counts.get("PASSED", 0),
        "failed": counts.get("FAILED", 0),
        "errors": counts.get("ERROR", 0),
        "missing": counts.get("MISSING", 0),
        "skipped": counts.get("SKIPPED", 0),
        "critical_failed": sum(
            1 for result in results if result["critical"] and result["outcome"] in SUSPEND_TRIGGER_OUTCOMES
        ),
        "golden_failed": sum(
            1 for result in results if result["kind"] == "golden_baseline" and result["outcome"] in SUSPEND_TRIGGER_OUTCOMES
        ),
    }


def compute_release_decision(manifest: Dict[str, Any], results: List[Dict[str, Any]],
                             manifest_problems: List[str] | None = None,
                             report_schema_exists: bool = True) -> Tuple[str, List[str]]:
    manifest_problems = manifest_problems or []
    reasons: List[str] = []

    if manifest_problems:
        reasons.extend(f"MANIFEST_INVALID: {problem}" for problem in manifest_problems)
        return "ERROR", reasons

    if not report_schema_exists:
        reasons.append("REPORT_SCHEMA_MISSING")
        return "SUSPEND", reasons

    required_suites = manifest.get("required_suites", [])
    if len(results) != len(required_suites):
        reasons.append("SUITE_RESULT_COUNT_MISMATCH")
        return "ERROR", reasons

    for result in results:
        if result["outcome"] in SUSPEND_TRIGGER_OUTCOMES:
            reasons.append(f"SUITE_{result['suite_id']}_{result['outcome']}")

    if reasons:
        return "SUSPEND", reasons
    return "GO", reasons


def trim_output(text: str, limit: int = 2000) -> str:
    text = text or ""
    return text[:limit]
