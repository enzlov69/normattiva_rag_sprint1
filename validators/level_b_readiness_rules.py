from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_registry_shape(registry: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    required_top = [
        "bundle_id",
        "version",
        "title",
        "scope",
        "allowed_decisions",
        "excluded_components",
        "checkpoints",
        "next_step_preconditions",
    ]
    for key in required_top:
        if key not in registry:
            problems.append(f"MISSING_TOP_LEVEL_FIELD:{key}")

    if registry.get("scope") != "offline_only":
        problems.append("INVALID_SCOPE")

    if registry.get("allowed_decisions") != ["COMPLETE", "HOLD", "ERROR"]:
        problems.append("INVALID_ALLOWED_DECISIONS")

    checkpoints = registry.get("checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        problems.append("INVALID_CHECKPOINTS")
    else:
        for idx, checkpoint in enumerate(checkpoints):
            for key in ["checkpoint_id", "label", "expected_tag", "required_paths"]:
                if key not in checkpoint:
                    problems.append(f"CHECKPOINT_{idx}_MISSING:{key}")
            if not isinstance(checkpoint.get("required_paths"), list) or not checkpoint.get("required_paths"):
                problems.append(f"CHECKPOINT_{idx}_INVALID_REQUIRED_PATHS")

    return problems


def check_checkpoint_paths(base_dir: Path, checkpoints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for checkpoint in checkpoints:
        missing = [path for path in checkpoint["required_paths"] if not (base_dir / path).exists()]
        results.append(
            {
                "checkpoint_id": checkpoint["checkpoint_id"],
                "label": checkpoint["label"],
                "expected_tag": checkpoint["expected_tag"],
                "missing_paths": missing,
                "is_complete": len(missing) == 0,
            }
        )
    return results


def detect_git_tags(base_dir: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "tag", "--list"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def is_git_worktree_clean(base_dir: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return False
        return result.stdout.strip() == ""
    except Exception:
        return False


def compute_readiness_decision(
    registry_problems: list[str],
    checkpoint_results: list[dict[str, Any]],
    repository_clean: bool,
    expected_tags_present: list[str],
    expected_tags_total: list[str],
) -> tuple[str, list[str]]:
    if registry_problems:
        return (
            "ERROR",
            [f"REGISTRY_INVALID:{problem}" for problem in registry_problems],
        )

    reasons: list[str] = []

    for item in checkpoint_results:
        if not item["is_complete"]:
            reasons.append(f"CHECKPOINT_{item['checkpoint_id']}_INCOMPLETE")

    missing_tags = sorted(set(expected_tags_total) - set(expected_tags_present))
    for tag in missing_tags:
        reasons.append(f"EXPECTED_TAG_MISSING:{tag}")

    if not repository_clean:
        reasons.append("WORKTREE_NOT_CLEAN")

    if reasons:
        return "HOLD", reasons

    return "COMPLETE", []


def build_readiness_report(
    registry: dict[str, Any],
    registry_problems: list[str],
    checkpoint_results: list[dict[str, Any]],
    repository_clean: bool,
    expected_tags_present: list[str],
    decision: str,
    reasons: list[str],
    base_dir: Path,
) -> dict[str, Any]:
    return {
        "bundle_id": registry["bundle_id"],
        "version": registry["version"],
        "decision": decision,
        "repository_root": str(base_dir),
        "repository_clean": repository_clean,
        "checkpoint_results": checkpoint_results,
        "expected_tags_present": expected_tags_present,
        "excluded_components": registry["excluded_components"],
        "next_step_preconditions": registry["next_step_preconditions"],
        "reasons": reasons,
    }
