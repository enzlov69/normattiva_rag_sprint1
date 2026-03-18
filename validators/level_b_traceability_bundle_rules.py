"""Helper offline per il Traceability Bundle v1 del Livello B.

Il modulo serve solo a:
- validare il registry della bundle view;
- verificare tag, path e componenti minimi della linea offline Level B;
- costruire un report unitario di tracciabilità;
- distinguere COMPLETE / HOLD / ERROR sul solo piano documentale e tecnico.

Non introduce logica runtime, non modifica il runner federato e non sostituisce
né il Release Gate né il Runbook né il Change Control Pack.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

ALLOWED_DECISIONS = {"COMPLETE", "HOLD", "ERROR"}
ALLOWED_COMPONENT_KINDS = {
    "validation",
    "golden",
    "release_gate",
    "runbook",
    "change_control",
    "traceability",
}


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_registry_shape(data: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    required_root = {
        "bundle_id",
        "bundle_version",
        "scope",
        "principles",
        "required_tags",
        "required_paths",
        "components",
        "execution_chain",
        "decision_policy",
        "stop_conditions",
    }
    missing_root = sorted(required_root - set(data.keys()))
    if missing_root:
        problems.append(f"Missing root keys: {', '.join(missing_root)}")

    principles = data.get("principles")
    if not isinstance(principles, list) or len(principles) < 5:
        problems.append("principles must be a list with at least 5 entries")

    required_tags = data.get("required_tags")
    if not isinstance(required_tags, list) or len(required_tags) < 4:
        problems.append("required_tags must be a list with at least 4 entries")

    required_paths = data.get("required_paths")
    if not isinstance(required_paths, list) or not required_paths:
        problems.append("required_paths must be a non-empty list")
    else:
        path_ids = set()
        paths = set()
        for idx, item in enumerate(required_paths):
            if not isinstance(item, dict):
                problems.append(f"required_paths[{idx}] must be an object")
                continue
            for key in ("path_id", "path", "component_id"):
                if key not in item:
                    problems.append(f"required_paths[{idx}] missing key '{key}'")
            path_id = item.get("path_id")
            if path_id in path_ids:
                problems.append(f"Duplicate path_id: {path_id}")
            else:
                path_ids.add(path_id)
            path_value = item.get("path")
            if path_value in paths:
                problems.append(f"Duplicate required path: {path_value}")
            else:
                paths.add(path_value)

    components = data.get("components")
    component_ids = set()
    if not isinstance(components, list) or not components:
        problems.append("components must be a non-empty list")
    else:
        for idx, component in enumerate(components):
            if not isinstance(component, dict):
                problems.append(f"components[{idx}] must be an object")
                continue
            for key in ("component_id", "title", "kind", "depends_on", "required_tags", "anchor_paths"):
                if key not in component:
                    problems.append(f"components[{idx}] missing key '{key}'")
            component_id = component.get("component_id")
            if component_id in component_ids:
                problems.append(f"Duplicate component_id: {component_id}")
            else:
                component_ids.add(component_id)
            if component.get("kind") not in ALLOWED_COMPONENT_KINDS:
                problems.append(f"Unsupported component kind: {component.get('kind')}")
            anchor_paths = component.get("anchor_paths")
            if not isinstance(anchor_paths, list) or not anchor_paths:
                problems.append(f"Component {component_id} must declare non-empty anchor_paths")
            depends_on = component.get("depends_on")
            if not isinstance(depends_on, list):
                problems.append(f"Component {component_id} must declare depends_on as a list")

        for component in components:
            component_id = component["component_id"]
            for dep in component.get("depends_on", []):
                if dep not in component_ids:
                    problems.append(f"Component {component_id} depends on unknown component: {dep}")

    execution_chain = data.get("execution_chain")
    if not isinstance(execution_chain, list) or not execution_chain:
        problems.append("execution_chain must be a non-empty list")
    else:
        stage_ids = set()
        orders = []
        seen_components = []
        for idx, stage in enumerate(execution_chain):
            if not isinstance(stage, dict):
                problems.append(f"execution_chain[{idx}] must be an object")
                continue
            for key in ("stage_id", "order", "component_id", "objective"):
                if key not in stage:
                    problems.append(f"execution_chain[{idx}] missing key '{key}'")
            stage_id = stage.get("stage_id")
            if stage_id in stage_ids:
                problems.append(f"Duplicate stage_id: {stage_id}")
            else:
                stage_ids.add(stage_id)
            order = stage.get("order")
            if not isinstance(order, int) or order < 1:
                problems.append(f"Invalid chain order at stage {stage_id}")
            else:
                orders.append(order)
            component_id = stage.get("component_id")
            seen_components.append(component_id)
            if component_id not in component_ids:
                problems.append(f"Execution chain references unknown component: {component_id}")
        if orders and sorted(orders) != list(range(1, len(orders) + 1)):
            problems.append("execution_chain must use consecutive order numbers starting from 1")
        if component_ids and set(seen_components) != component_ids:
            problems.append("execution_chain must cover all declared components exactly once")

    decision_policy = data.get("decision_policy")
    if not isinstance(decision_policy, dict):
        problems.append("decision_policy must be an object")
    else:
        values = decision_policy.get("decision_values")
        if not isinstance(values, list) or set(values) != ALLOWED_DECISIONS:
            problems.append("decision_policy.decision_values must exactly match COMPLETE/HOLD/ERROR")
        if decision_policy.get("worktree_clean_required") is not True:
            problems.append("decision_policy.worktree_clean_required must be true")

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
                "component_id": item["component_id"],
                "exists": path.exists(),
            }
        )
    return results


def check_required_tags(required_tags: List[str], available_tags: List[str]) -> List[Dict[str, Any]]:
    tag_set = set(available_tags)
    return [{"tag": tag, "present": tag in tag_set} for tag in required_tags]


def check_components(base_dir: Path, components: List[Dict[str, Any]], available_tags: List[str]) -> List[Dict[str, Any]]:
    tag_set = set(available_tags)
    results: List[Dict[str, Any]] = []
    for component in components:
        anchor_results = []
        for relative_path in component["anchor_paths"]:
            path = resolve_path(base_dir, relative_path)
            anchor_results.append({"path": relative_path, "exists": path.exists()})
        required_component_tags = component.get("required_tags", [])
        tag_results = [{"tag": tag, "present": tag in tag_set} for tag in required_component_tags]
        anchor_complete = all(item["exists"] for item in anchor_results)
        tag_complete = all(item["present"] for item in tag_results) if required_component_tags else True
        results.append(
            {
                "component_id": component["component_id"],
                "title": component["title"],
                "kind": component["kind"],
                "depends_on": component["depends_on"],
                "anchor_results": anchor_results,
                "tag_results": tag_results,
                "anchor_complete": anchor_complete,
                "tag_complete": tag_complete,
                "component_complete": anchor_complete and tag_complete,
            }
        )
    return results


def compute_bundle_decision(
    registry_problems: List[str],
    path_results: List[Dict[str, Any]],
    tag_results: List[Dict[str, Any]],
    component_results: List[Dict[str, Any]],
    git_status_clean: bool | None = None,
) -> Tuple[str, List[str]]:
    reasons: List[str] = []

    if registry_problems:
        reasons.extend(f"REGISTRY_INVALID: {problem}" for problem in registry_problems)
        return "ERROR", reasons

    for item in path_results:
        if not item["exists"]:
            reasons.append(f"PATH_{item['path_id']}_MISSING")

    for tag in tag_results:
        if not tag["present"]:
            reasons.append(f"TAG_{tag['tag']}_MISSING")

    for component in component_results:
        if not component["component_complete"]:
            reasons.append(f"COMPONENT_{component['component_id']}_INCOMPLETE")

    if git_status_clean is False:
        reasons.append("WORKTREE_NOT_CLEAN")

    if reasons:
        return "HOLD", reasons
    return "COMPLETE", reasons


def derive_next_action(decision: str) -> str:
    if decision == "COMPLETE":
        return "Traceability bundle is coherent. You may consolidate the bundle with commit and tag."
    if decision == "HOLD":
        return "Restore missing tags, missing paths, incomplete components or working tree hygiene before consolidation."
    return "Repair the traceability bundle registry before further use."


def build_bundle_report(
    registry: Dict[str, Any],
    registry_problems: List[str],
    path_results: List[Dict[str, Any]],
    tag_results: List[Dict[str, Any]],
    component_results: List[Dict[str, Any]],
    decision: str,
    reasons: List[str],
    base_dir: Path,
    available_tags: List[str],
    git_status_clean: bool | None,
) -> Dict[str, Any]:
    if decision not in ALLOWED_DECISIONS:
        raise ValueError(f"Unsupported decision: {decision}")
    return {
        "bundle_id": registry.get("bundle_id"),
        "bundle_version": registry.get("bundle_version"),
        "base_dir": str(base_dir.resolve()),
        "decision": decision,
        "reasons": reasons,
        "git_status_clean": git_status_clean,
        "available_tags": available_tags,
        "tag_results": tag_results,
        "path_results": path_results,
        "component_results": component_results,
        "execution_chain": registry.get("execution_chain", []),
        "registry_problems": registry_problems,
        "next_action": derive_next_action(decision),
    }


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_git_tags(base_dir: Path) -> List[str]:
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


def get_git_status_clean(base_dir: Path) -> bool | None:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=base_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() == ""
