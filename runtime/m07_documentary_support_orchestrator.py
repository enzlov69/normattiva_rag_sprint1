from __future__ import annotations

import copy
from typing import Any, Callable

from runtime.m07_documentary_support_adapter import (
    M07AdapterError,
    build_m07_documentary_support_request,
    run_m07_documentary_support_exchange,
)
from runtime.m07_documentary_support_module_registry import (
    M07ModuleRegistryError,
    resolve_m07_documentary_support_dispatch,
)


ORCHESTRATOR_MODULE_ID = "A1_AI_ORCHESTRATOR_M07_FACADE"


class M07OrchestratorError(Exception):
    """Base exception for the Level A local orchestration facade."""


class M07OrchestratorUnauthorizedCallerError(M07OrchestratorError):
    """Raised when the caller is not authorized by the controlled registry."""


class M07OrchestratorBoundaryError(M07OrchestratorError):
    """Raised when orchestration invariants are violated."""


def _build_orchestration_block(
    *,
    case_id: str,
    block_code: str,
    block_reason: str,
    origin_module: str,
    severity: str = "CRITICAL",
    category: str = "ORCHESTRATION",
    status: str = "OPEN",
) -> dict[str, Any]:
    return {
        "block_id": f"blk_{case_id}_{block_code.lower()}",
        "case_id": case_id,
        "block_code": block_code,
        "block_category": category,
        "block_severity": severity,
        "origin_module": origin_module,
        "block_reason": block_reason,
        "block_status": status,
    }


def _normalize_orchestration_status(
    adapter_status: str,
    blocks: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> str:
    if adapter_status == "REJECTED":
        return "REJECTED"
    if adapter_status == "ERROR":
        return "ERROR"
    if adapter_status == "BLOCKED":
        return "BLOCKED"
    if adapter_status == "DEGRADED":
        return "DEGRADED"
    if errors:
        return "ERROR"
    if blocks:
        return "BLOCKED"
    if warnings:
        return "SUCCESS_WITH_WARNINGS"
    return "SUCCESS"


def _ensure_m07_evidence_presence(
    *,
    request_payload: dict[str, Any],
    response_consumption: dict[str, Any],
) -> dict[str, Any]:
    requested_outputs = request_payload["payload"].get("requested_outputs", [])
    documentary_packet = response_consumption["documentary_packet"]

    requires_m07_pack = "m07_evidence_pack" in requested_outputs
    has_m07_pack = "m07_evidence_pack" in documentary_packet

    if requires_m07_pack and not has_m07_pack:
        patched = copy.deepcopy(response_consumption)
        patched["blocks"].append(
            _build_orchestration_block(
                case_id=patched["case_id"],
                block_code="M07_REQUIRED",
                block_reason=(
                    "La response documentale non contiene M07EvidencePack "
                    "nonostante sia stato richiesto."
                ),
                origin_module=ORCHESTRATOR_MODULE_ID,
            )
        )
        patched["adapter_status"] = "BLOCKED"
        patched["requires_human_m07_completion"] = True
        patched["m07_evidence_pack_present"] = False
        return patched

    return response_consumption


def orchestrate_m07_documentary_support(
    *,
    transport: Callable[[dict[str, Any]], dict[str, Any]],
    session_id: str,
    request_id: str,
    case_id: str,
    trace_id: str,
    timestamp: str,
    caller_module: str,
    goal_istruttorio: str,
    domain_target: str,
    query_text: str,
    source_priority: list[str],
    reading_focus: list[str] | None = None,
    metadata_filters: dict[str, Any] | None = None,
    notes: str | None = None,
    requested_outputs: list[str] | None = None,
) -> dict[str, Any]:
    """
    Facade locale del Livello A:
    - risolve il modulo tramite registry controllato
    - costruisce la request documentale
    - esegue il transport A→B→A
    - consuma la response
    - propaga blocchi e warning
    - non decide, non chiude M07, non autorizza output
    """

    try:
        dispatch = resolve_m07_documentary_support_dispatch(caller_module)
    except M07ModuleRegistryError as exc:
        raise M07OrchestratorUnauthorizedCallerError(str(exc)) from exc

    request_payload = build_m07_documentary_support_request(
        request_id=request_id,
        case_id=case_id,
        trace_id=trace_id,
        timestamp=timestamp,
        goal_istruttorio=goal_istruttorio,
        domain_target=domain_target,
        query_text=query_text,
        source_priority=source_priority,
        caller_module=caller_module,
        target_module=dispatch["target_module"],
        requested_outputs=requested_outputs,
        reading_focus=reading_focus,
        metadata_filters=metadata_filters,
        notes=notes,
    )

    try:
        response_consumption = run_m07_documentary_support_exchange(
            transport=transport,
            request_payload=request_payload,
        )
    except M07AdapterError as exc:
        raise M07OrchestratorBoundaryError(str(exc)) from exc

    response_consumption = _ensure_m07_evidence_presence(
        request_payload=request_payload,
        response_consumption=response_consumption,
    )

    warnings = copy.deepcopy(response_consumption["warnings"])
    errors = copy.deepcopy(response_consumption["errors"])
    blocks = copy.deepcopy(response_consumption["blocks"])

    orchestration_status = _normalize_orchestration_status(
        adapter_status=response_consumption["adapter_status"],
        blocks=blocks,
        errors=errors,
        warnings=warnings,
    )

    return {
        "session_id": session_id,
        "request_id": request_id,
        "case_id": case_id,
        "trace_id": trace_id,
        "orchestrator_module": ORCHESTRATOR_MODULE_ID,
        "caller_module": caller_module,
        "resolved_module_id": dispatch["module_id"],
        "dispatch_mode": dispatch["dispatch_mode"],
        "target_module": dispatch["target_module"],
        "request_payload": copy.deepcopy(request_payload),
        "response_consumption": copy.deepcopy(response_consumption),
        "orchestration_status": orchestration_status,
        "warnings": warnings,
        "errors": errors,
        "blocks": blocks,
        "requires_human_m07_completion": True,
        "can_close_m07": False,
        "can_build_rac": False,
        "can_finalize_compliance": False,
        "can_authorize_output": False,
        "can_emit_go_no_go": False,
        "manual_level_a_only": True,
        "runner_federated_touched": False,
    }