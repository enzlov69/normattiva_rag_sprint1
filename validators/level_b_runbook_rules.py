"""Helper offline per il Runbook Offline v1 del Livello B.

Il modulo resta fuori da runner, runtime, retrieval, router e bridge applicativo.
Serve solo a:
- validare la checklist del runbook;
- verificare la presenza dei file minimi richiamati dal runbook;
- costruire un report di preflight operativo;
- distinguere READY / HOLD / ERROR sul solo piano operativo del fascicolo.

Non decide il rilascio del Livello B.
Non sostituisce il Release Gate Offline.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

ALLOWED_PREFLIGHT_DECISIONS = {"READY", "HOLD", "ERROR"}
ALLOWED_STEP_KINDS = {
    "repository_hygiene",
    "baseline_presence",
    "suite_execution",
    "gate_execution",
    "report_review",
    "housekeeping",
    "git_consolidation",
}
ALLOWED_OUTCOME_POLICIES = {"must_pass", "must_exist", "operator_review", "must_be_clean"}


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_runbook_checklist_shape(data: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    required_root = {
        "runbook_id",
        "runbook_version",
        "scope",
        "principles",
        "preflight",
        "execution_order",
        "required_paths",
        "required_suites",
        "report_review",
        "housekeeping",
        "git_consolidation",
        "change_policy",
        "freeze_policy",
        "stop_conditions",
    }
    missing_root = sorted(required_root - set(data.keys()))
    if missing_root:
        problems.append(f"Missing root keys: {', '.join(missing_root)}")

    principles = data.get("principles")
    if not isinstance(principles, list) or len(principles) < 5:
        problems.append("principles must be a list with at least 5 entries")

    execution_order = data.get("execution_order")
    if not isinstance(execution_order, list) or not execution_order:
        problems.append("execution_order must be a non-empty list")
    else:
        seen_ids = set()
        order_numbers = []
        for idx, step in enumerate(execution_order):
            if not isinstance(step, dict):
                problems.append(f"execution_order[{idx}] must be an object")
                continue
            for key in ("step_id", "order", "title", "kind", "outcome_policy"):
                if key not in step:
                    problems.append(f"execution_order[{idx}] missing key '{key}'")
            step_id = step.get("step_id")
            if step_id in seen_ids:
                problems.append(f"Duplicate step_id: {step_id}")
            else:
                seen_ids.add(step_id)
            order = step.get("order")
            if not isinstance(order, int) or order < 1:
                problems.append(f"Step {step_id} has invalid order")
            else:
                order_numbers.append(order)
            kind = step.get("kind")
            if kind not in ALLOWED_STEP_KINDS:
                problems.append(f"Step {step_id} has unsupported kind: {kind}")
            outcome_policy = step.get("outcome_policy")
            if outcome_policy not in ALLOWED_OUTCOME_POLICIES:
                problems.append(f"Step {step_id} has unsupported outcome_policy: {outcome_policy}")
        if order_numbers and sorted(order_numbers) != list(range(1, len(order_numbers) + 1)):
            problems.append("execution_order must use consecutive order numbers starting from 1")

    required_paths = data.get("required_paths")
    if not isinstance(required_paths, list) or not required_paths:
        problems.append("required_paths must be a non-empty list")
    else:
        seen_paths = set()
        for idx, item in enumerate(required_paths):
            if not isinstance(item, dict):
                problems.append(f"required_paths[{idx}] must be an object")
                continue
            for key in ("path_id", "path", "required_for"):
                if key not in item:
                    problems.append(f"required_paths[{idx}] missing key '{key}'")
            path_value = item.get("path")
            if path_value in seen_paths:
                problems.append(f"Duplicate required path: {path_value}")
            else:
                seen_paths.add(path_value)

    required_suites = data.get("required_suites")
    if not isinstance(required_suites, list) or not required_suites:
        problems.append("required_suites must be a non-empty list")
    else:
        suite_ids = set()
        golden_present = False
        for idx, suite in enumerate(required_suites):
            if not isinstance(suite, dict):
                problems.append(f"required_suites[{idx}] must be an object")
                continue
            for key in ("suite_id", "path", "critical", "golden"):
                if key not in suite:
                    problems.append(f"required_suites[{idx}] missing key '{key}'")
            suite_id = suite.get("suite_id")
            if suite_id in suite_ids:
                problems.append(f"Duplicate suite_id: {suite_id}")
            else:
                suite_ids.add(suite_id)
            if not isinstance(suite.get("critical"), bool):
                problems.append(f"Suite {suite_id} has non-boolean critical flag")
            if not isinstance(suite.get("golden"), bool):
                problems.append(f"Suite {suite_id} has non-boolean golden flag")
            if suite.get("golden"):
                golden_present = True
        if not golden_present:
            problems.append("required_suites must include one suite flagged as golden")

    preflight = data.get("preflight")
    if not isinstance(preflight, dict):
        problems.append("preflight must be an object")
    else:
        for key in ("decision_values", "report_default_path"):
            if key not in preflight:
                problems.append(f"preflight missing key '{key}'")
        decision_values = preflight.get("decision_values")
        if not isinstance(decision_values, list) or set(decision_values) != ALLOWED_PREFLIGHT_DECISIONS:
            problems.append("preflight.decision_values must exactly match READY/HOLD/ERROR")

    return problems


def resolve_path(base_dir: Path, relative_path: str) -> Path:
    return (base_dir / relative_path).resolve()


def check_required_paths(base_dir: Path, required_paths: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for item in required_paths:
        path = resolve_path(base_dir, item["path"])
        results.append(
            {
                "path_id": item["path_id"],
                "path": item["path"],
                "required_for": item["required_for"],
                "exists": path.exists(),
            }
        )
    return results


def check_required_suites(base_dir: Path, required_suites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for suite in required_suites:
        path = resolve_path(base_dir, suite["path"])
        results.append(
            {
                "suite_id": suite["suite_id"],
                "path": suite["path"],
                "critical": suite["critical"],
                "golden": suite["golden"],
                "exists": path.exists(),
            }
        )
    return results


def compute_preflight_decision(
    checklist_problems: List[str],
    path_results: List[Dict[str, Any]],
    suite_results: List[Dict[str, Any]],
    git_status_clean: bool | None = None,
) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    if checklist_problems:
        reasons.extend(f"CHECKLIST_INVALID: {problem}" for problem in checklist_problems)
        return "ERROR", reasons

    for item in path_results:
        if not item["exists"]:
            reasons.append(f"PATH_{item['path_id']}_MISSING")

    for suite in suite_results:
        if not suite["exists"]:
            reasons.append(f"SUITE_{suite['suite_id']}_MISSING")

    if git_status_clean is False:
        reasons.append("WORKTREE_NOT_CLEAN")

    if reasons:
        return "HOLD", reasons
    return "READY", reasons


def build_preflight_report(
    checklist: Dict[str, Any],
    checklist_problems: List[str],
    path_results: List[Dict[str, Any]],
    suite_results: List[Dict[str, Any]],
    decision: str,
    reasons: List[str],
    base_dir: Path,
    git_status_clean: bool | None,
) -> Dict[str, Any]:
    if decision not in ALLOWED_PREFLIGHT_DECISIONS:
        raise ValueError(f"Unsupported preflight decision: {decision}")
    return {
        "runbook_id": checklist.get("runbook_id"),
        "runbook_version": checklist.get("runbook_version"),
        "scope": checklist.get("scope"),
        "base_dir": str(base_dir.resolve()),
        "decision": decision,
        "reasons": reasons,
        "git_status_clean": git_status_clean,
        "checklist_problems": checklist_problems,
        "required_paths": path_results,
        "required_suites": suite_results,
        "next_action": derive_next_action(decision),
    }


def derive_next_action(decision: str) -> str:
    if decision == "READY":
        return "Proceed with the ordered offline runbook execution and then run the Release Gate Offline."
    if decision == "HOLD":
        return "Resolve missing files, missing suites or working tree hygiene issues before executing the runbook."
    return "Repair the runbook checklist or preflight configuration before further use."


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
