from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import subprocess


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_registry_shape(registry: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    required = ["registry_id", "decision_states", "protected_assets", "forbidden_touchpoints", "change_classes", "required_human_approvals", "required_suites_by_asset_prefix", "stop_conditions"]
    for key in required:
        if key not in registry:
            problems.append(f"missing_registry_key:{key}")
    if "decision_states" in registry:
        expected = {"ALLOW", "HOLD", "REJECT", "ERROR"}
        if set(registry["decision_states"]) != expected:
            problems.append("decision_states_mismatch")
    return problems


def validate_change_request_shape(request: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    for key in schema["required_top_level"]:
        if key not in request:
            problems.append(f"missing_request_key:{key}")
    if request.get("scope") not in schema["allowed_scopes"]:
        problems.append("invalid_scope")
    if request.get("change_class") not in schema["allowed_change_classes"]:
        problems.append("invalid_change_class")
    if request.get("change_intent") not in schema["allowed_change_intents"]:
        problems.append("invalid_change_intent")

    risk = request.get("risk_assessment", {})
    for key in schema["required_risk_keys"]:
        if key not in risk:
            problems.append(f"missing_risk_key:{key}")

    approvals = request.get("human_approvals", [])
    if not isinstance(approvals, list):
        problems.append("human_approvals_not_list")
    else:
        for idx, approval in enumerate(approvals):
            for key in schema["approval_shape"]["required_keys"]:
                if key not in approval:
                    problems.append(f"missing_approval_key:{idx}:{key}")

    if not isinstance(request.get("target_assets", []), list) or not request.get("target_assets"):
        problems.append("target_assets_missing_or_invalid")
    if not isinstance(request.get("touchpoints", []), list):
        problems.append("touchpoints_not_list")
    if not isinstance(request.get("evidence", {}), dict):
        problems.append("evidence_not_object")
    return problems


def detect_protected_assets(target_assets: list[str], registry: dict[str, Any]) -> list[str]:
    protected = set(registry["protected_assets"])
    return [asset for asset in target_assets if asset in protected]


def detect_forbidden_touchpoints(touchpoints: list[str], registry: dict[str, Any]) -> list[str]:
    forbidden = set(registry["forbidden_touchpoints"])
    return [item for item in touchpoints if item in forbidden]


def required_approval_roles(change_class: str, registry: dict[str, Any]) -> list[str]:
    return registry["required_human_approvals"].get(change_class, registry["required_human_approvals"]["default"])


def missing_approval_roles(request: dict[str, Any], registry: dict[str, Any]) -> list[str]:
    required_roles = set(required_approval_roles(request["change_class"], registry))
    approvals = request.get("human_approvals", [])
    approved_roles = {a["role"] for a in approvals if a.get("approved") is True}
    return sorted(required_roles - approved_roles)


def required_suites_for_assets(target_assets: list[str], registry: dict[str, Any]) -> list[str]:
    suites: list[str] = []
    mapping = registry["required_suites_by_asset_prefix"]
    for asset in target_assets:
        for prefix, suite_list in mapping.items():
            if asset.startswith(prefix) or asset == prefix:
                for suite in suite_list:
                    if suite not in suites:
                        suites.append(suite)
    return suites


def check_required_suites_exist(base_dir: Path, suite_paths: list[str]) -> list[str]:
    missing: list[str] = []
    for rel in suite_paths:
        if not (base_dir / rel).exists():
            missing.append(rel)
    return missing


def git_worktree_clean(base_dir: Path) -> bool:
    git_dir = base_dir / ".git"
    if not git_dir.exists():
        return True
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=base_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == ""


def evaluate_change_request(
    request: dict[str, Any],
    schema: dict[str, Any],
    registry: dict[str, Any],
    base_dir: Path,
    git_status_clean: bool | None = None,
) -> tuple[str, list[str], dict[str, Any]]:
    reasons: list[str] = []
    request_problems = validate_change_request_shape(request, schema)
    registry_problems = validate_registry_shape(registry)
    if request_problems or registry_problems:
        combined = [f"REQUEST_INVALID:{p}" for p in request_problems] + [f"REGISTRY_INVALID:{p}" for p in registry_problems]
        return "ERROR", combined, {}

    protected_assets = detect_protected_assets(request["target_assets"], registry)
    forbidden_touchpoints = detect_forbidden_touchpoints(request["touchpoints"], registry)
    missing_approvals = missing_approval_roles(request, registry)
    required_suites = required_suites_for_assets(request["target_assets"], registry)
    missing_suites = check_required_suites_exist(base_dir, required_suites)

    if git_status_clean is None:
        git_status_clean = git_worktree_clean(base_dir)

    evidence = request["evidence"]
    required_evidence = registry["change_classes"][request["change_class"]]["required_evidence"]
    missing_evidence = [key for key in required_evidence if not evidence.get(key)]

    weakens_foundational_controls = (
        request["change_class"] == "foundational_weakening"
        or request["change_intent"] in {"weaken", "remove"}
        or bool(request.get("weakens_controls"))
    )
    enables_level_b_conclusion = bool(request.get("enables_level_b_conclusion"))
    enables_m07_closure = bool(request.get("enables_m07_closure"))
    removes_audit_or_shadow = bool(request.get("removes_audit_or_shadow"))
    deletes_foundational_golden_without_supersession = bool(request.get("deletes_foundational_golden_without_supersession"))

    if forbidden_touchpoints:
        reasons.append("TOUCHPOINT_FORBIDDEN_SCOPE")
    if weakens_foundational_controls:
        reasons.append("WEAKENS_FOUNDATIONAL_CONTROLS")
    if enables_level_b_conclusion:
        reasons.append("ENABLES_LEVEL_B_CONCLUSION")
    if enables_m07_closure:
        reasons.append("ENABLES_M07_CLOSURE_BY_LEVEL_B")
    if removes_audit_or_shadow:
        reasons.append("REMOVES_AUDIT_OR_SHADOW")
    if deletes_foundational_golden_without_supersession:
        reasons.append("DELETES_FOUNDATIONAL_GOLDEN_WITHOUT_SUPERSESSION")

    if reasons:
        details = {
            "scope_ok": request["scope"] == "level_b_offline_only",
            "protected_assets_touched": protected_assets,
            "forbidden_touchpoints_found": forbidden_touchpoints,
            "missing_approval_roles": missing_approvals,
            "required_suites": required_suites,
            "missing_suites": missing_suites,
            "git_status_clean": git_status_clean,
            "missing_evidence": missing_evidence,
        }
        return "REJECT", reasons, details

    hold_reasons: list[str] = []
    if protected_assets and missing_evidence:
        hold_reasons.append("PROTECTED_ASSET_EVIDENCE_INCOMPLETE")
    if protected_assets and missing_approvals:
        hold_reasons.append("PROTECTED_ASSET_APPROVALS_INCOMPLETE")
    if missing_suites:
        hold_reasons.append("REQUIRED_SUITES_MISSING")
    if not git_status_clean:
        hold_reasons.append("WORKTREE_NOT_CLEAN")
    if request["human_approval_required"] is True and missing_approvals:
        if "PROTECTED_ASSET_APPROVALS_INCOMPLETE" not in hold_reasons:
            hold_reasons.append("HUMAN_APPROVALS_INCOMPLETE")
    if hold_reasons:
        details = {
            "scope_ok": True,
            "protected_assets_touched": protected_assets,
            "forbidden_touchpoints_found": forbidden_touchpoints,
            "missing_approval_roles": missing_approvals,
            "required_suites": required_suites,
            "missing_suites": missing_suites,
            "git_status_clean": git_status_clean,
            "missing_evidence": missing_evidence,
        }
        return "HOLD", hold_reasons, details

    details = {
        "scope_ok": True,
        "protected_assets_touched": protected_assets,
        "forbidden_touchpoints_found": forbidden_touchpoints,
        "missing_approval_roles": missing_approvals,
        "required_suites": required_suites,
        "missing_suites": missing_suites,
        "git_status_clean": git_status_clean,
        "missing_evidence": missing_evidence,
    }
    return "ALLOW", [], details


def build_change_control_report(
    registry: dict[str, Any],
    request: dict[str, Any],
    decision: str,
    reasons: list[str],
    details: dict[str, Any],
) -> dict[str, Any]:
    next_action = {
        "ALLOW": "Apply the offline Level B change, then rerun the required suites and prechecks before commit/tag.",
        "HOLD": "Do not modify the protected assets yet. Complete evidence, approvals, missing suites or clean the worktree, then rerun the precheck.",
        "REJECT": "Stop the change request. The proposed change violates foundational boundaries or touches forbidden scope.",
        "ERROR": "Fix the malformed request or registry before any repository action.",
    }[decision]
    return {
        "registry_id": registry["registry_id"],
        "change_id": request.get("change_id", ""),
        "title": request.get("title", ""),
        "decision": decision,
        "reasons": reasons,
        "scope_ok": details.get("scope_ok"),
        "protected_assets_touched": details.get("protected_assets_touched", []),
        "forbidden_touchpoints_found": details.get("forbidden_touchpoints_found", []),
        "required_suites": details.get("required_suites", []),
        "missing_suites": details.get("missing_suites", []),
        "git_status_clean": details.get("git_status_clean"),
        "next_action": next_action,
    }
