from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_registry_shape(registry: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    if registry.get("registry_id") != "LB-BIM-REG-v1":
        problems.append("registry_id must be LB-BIM-REG-v1")
    checkpoints = registry.get("checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        problems.append("checkpoints must be a non-empty list")
        return problems

    ids = [cp.get("id") for cp in checkpoints]
    if len(ids) != len(set(ids)):
        problems.append("checkpoint ids must be unique")

    orders = [cp.get("order") for cp in checkpoints if isinstance(cp.get("order"), int)]
    if len(orders) != len(checkpoints):
        problems.append("all checkpoints must have integer order")
    elif orders != sorted(orders):
        problems.append("checkpoint orders must be sorted ascending")

    for checkpoint in checkpoints:
        if not checkpoint.get("git_tags"):
            problems.append(f'{checkpoint.get("id")} must declare at least one git tag')
        if not checkpoint.get("key_files"):
            problems.append(f'{checkpoint.get("id")} must declare key files')
        if checkpoint.get("status") not in {"historical_stable", "active_stable", "candidate"}:
            problems.append(f'{checkpoint.get("id")} has invalid status')

    execution = registry.get("canonical_execution_order")
    if not isinstance(execution, list) or not execution:
        problems.append("canonical_execution_order must be a non-empty list")
    else:
        exec_orders = [step.get("order") for step in execution if isinstance(step.get("order"), int)]
        if len(exec_orders) != len(execution):
            problems.append("all canonical execution steps must have integer order")
        elif exec_orders != list(range(1, len(execution) + 1)):
            problems.append("canonical execution order must be contiguous starting at 1")

    return problems


def evaluate_checkpoints(base_dir: Path, registry: Dict[str, Any]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for checkpoint in registry["checkpoints"]:
        missing = [path for path in checkpoint["key_files"] if not (base_dir / path).exists()]
        results.append(
            {
                "id": checkpoint["id"],
                "label": checkpoint["label"],
                "status": checkpoint["status"],
                "git_tags": checkpoint["git_tags"],
                "all_key_files_present": not missing,
                "missing_files": missing,
            }
        )
    return results


def get_git_status_clean(base_dir: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    if result.returncode != 0:
        return False
    return result.stdout.strip() == ""


def compute_decision(
    registry_problems: List[str],
    checkpoint_results: List[Dict[str, Any]],
    git_status_clean: bool,
) -> Tuple[str, List[str]]:
    if registry_problems:
        return "ERROR", [f"REGISTRY_INVALID: {problem}" for problem in registry_problems]

    reasons: List[str] = []
    for checkpoint in checkpoint_results:
        if not checkpoint["all_key_files_present"]:
            reasons.append(f'CHECKPOINT_{checkpoint["id"]}_MISSING_FILES')
    if not git_status_clean:
        reasons.append("WORKTREE_NOT_CLEAN")

    if reasons:
        return "HOLD", reasons
    return "COMPLETE", []


def build_report(
    registry: Dict[str, Any],
    registry_problems: List[str],
    checkpoint_results: List[Dict[str, Any]],
    decision: str,
    reasons: List[str],
    base_dir: Path,
    git_status_clean: bool,
) -> Dict[str, Any]:
    if decision == "COMPLETE":
        next_action = "Baseline index master is structurally coherent. Preserve current checkpoint map and rerun after future Level B offline changes."
    elif decision == "HOLD":
        next_action = "Resolve missing indexed assets and/or restore a clean worktree before treating the baseline index as complete."
    else:
        next_action = "Repair registry structure before relying on the baseline index master."

    return {
        "report_id": "LB-BIM-REPORT-v1",
        "decision": decision,
        "base_dir": str(base_dir),
        "git_status_clean": git_status_clean,
        "registry_problems": registry_problems,
        "checkpoints": checkpoint_results,
        "reasons": reasons,
        "next_action": next_action,
    }
