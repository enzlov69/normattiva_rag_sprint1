from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


S_PRED_PHASE_ID = "S-PRE/D"
S_PRED_PHASE_NAME = "Verifica Integrità Sistema"
S_PRED_METHOD_VERSION = "PPAV_2_2"


@dataclass(frozen=True)
class SPredInput:
    session_id: str
    method_version: str
    corpus_available: bool
    modules_available: bool
    safeguards_available: bool
    retrieval_available: bool
    citations_available: bool
    audit_trail_available: bool
    block_propagation_available: bool
    version_alignment_ok: bool
    indexing_status: str = "UNKNOWN"
    ranking_status: str = "UNKNOWN"
    shadow_store_available: Optional[bool] = None
    details: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SPredCheckResult:
    check_id: str
    label: str
    passed: bool
    severity: str
    reason: Optional[str] = None


def _normalize_bool(value: Any) -> bool:
    return bool(value)


def _build_check(
    check_id: str,
    label: str,
    passed: bool,
    severity: str = "BLOCKING",
    reason: Optional[str] = None,
) -> SPredCheckResult:
    return SPredCheckResult(
        check_id=check_id,
        label=label,
        passed=passed,
        severity=severity,
        reason=reason,
    )


def _validate_input_payload(payload: Dict[str, Any]) -> List[str]:
    required_fields = [
        "session_id",
        "method_version",
        "corpus_available",
        "modules_available",
        "safeguards_available",
        "retrieval_available",
        "citations_available",
        "audit_trail_available",
        "block_propagation_available",
        "version_alignment_ok",
    ]

    errors: List[str] = []

    for field in required_fields:
        if field not in payload:
            errors.append(f"Missing required field: {field}")

    if "indexing_status" in payload and not isinstance(payload["indexing_status"], str):
        errors.append("Field indexing_status must be a string")

    if "ranking_status" in payload and not isinstance(payload["ranking_status"], str):
        errors.append("Field ranking_status must be a string")

    return errors


def _coerce_input(payload: Dict[str, Any]) -> SPredInput:
    return SPredInput(
        session_id=str(payload["session_id"]),
        method_version=str(payload["method_version"]),
        corpus_available=_normalize_bool(payload["corpus_available"]),
        modules_available=_normalize_bool(payload["modules_available"]),
        safeguards_available=_normalize_bool(payload["safeguards_available"]),
        retrieval_available=_normalize_bool(payload["retrieval_available"]),
        citations_available=_normalize_bool(payload["citations_available"]),
        audit_trail_available=_normalize_bool(payload["audit_trail_available"]),
        block_propagation_available=_normalize_bool(payload["block_propagation_available"]),
        version_alignment_ok=_normalize_bool(payload["version_alignment_ok"]),
        indexing_status=str(payload.get("indexing_status", "UNKNOWN")),
        ranking_status=str(payload.get("ranking_status", "UNKNOWN")),
        shadow_store_available=(
            None
            if "shadow_store_available" not in payload
            else _normalize_bool(payload["shadow_store_available"])
        ),
        details=payload.get("details"),
    )


def run_s_pred(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    S-PRE/D – Verifica Integrità Sistema

    Gate assoluto e non derogabile.
    Se l'esito è BLOCKED, non è consentita l'attivazione della FASE 0.
    """

    validation_errors = _validate_input_payload(payload)
    if validation_errors:
        return {
            "phase_id": S_PRED_PHASE_ID,
            "phase_name": S_PRED_PHASE_NAME,
            "method_version": str(payload.get("method_version", "UNKNOWN")),
            "session_id": str(payload.get("session_id", "UNKNOWN")),
            "status": "BLOCKED",
            "can_start_fase0": False,
            "transition_allowed": False,
            "next_phase": None,
            "gate_outcome": "BLOCCO_SISTEMA_ASSOLUTO",
            "blocking_reasons": validation_errors,
            "warnings": [],
            "checks": [],
            "trace": {
                "phase": S_PRED_PHASE_ID,
                "trace_type": "TECHNICAL_GATE",
                "validation_layer": "INPUT_SCHEMA",
            },
        }

    data = _coerce_input(payload)

    checks: List[SPredCheckResult] = [
        _build_check(
            "A1",
            "Corpus disponibili",
            data.corpus_available,
            reason=None if data.corpus_available else "Corpus mancanti o non accessibili",
        ),
        _build_check(
            "A2",
            "Moduli richiamabili",
            data.modules_available,
            reason=None if data.modules_available else "Moduli PPAV non richiamabili",
        ),
        _build_check(
            "A3",
            "Presìdi permanenti disponibili",
            data.safeguards_available,
            reason=None if data.safeguards_available else "Presìdi permanenti non disponibili",
        ),
        _build_check(
            "B1",
            "Allineamento versioni",
            data.version_alignment_ok,
            reason=None if data.version_alignment_ok else "Versioni disallineate o mix di revisioni",
        ),
        _build_check(
            "C1",
            "Retrieval operativo",
            data.retrieval_available,
            reason=None if data.retrieval_available else "Retrieval non operativo",
        ),
        _build_check(
            "C2",
            "Pipeline citazionale disponibile",
            data.citations_available,
            reason=None if data.citations_available else "Citazioni non costruibili",
        ),
        _build_check(
            "D1",
            "Audit trail tecnico disponibile",
            data.audit_trail_available,
            reason=None if data.audit_trail_available else "Audit trail tecnico assente",
        ),
        _build_check(
            "D2",
            "Propagazione blocchi disponibile",
            data.block_propagation_available,
            reason=None if data.block_propagation_available else "Propagazione blocchi non operativa",
        ),
    ]

    if data.shadow_store_available is not None:
        checks.append(
            _build_check(
                "A4",
                "Shadow store disponibile",
                data.shadow_store_available,
                reason=None if data.shadow_store_available else "Shadow store non disponibile",
            )
        )

    warnings: List[str] = []
    degraded_indexing = data.indexing_status.upper() not in {"OK", "ACTIVE", "READY"}
    degraded_ranking = data.ranking_status.upper() not in {"OK", "ACTIVE", "READY"}

    if degraded_indexing:
        warnings.append(f"Indexing status non ottimale: {data.indexing_status}")
    if degraded_ranking:
        warnings.append(f"Ranking status non ottimale: {data.ranking_status}")

    blocking_reasons = [check.reason for check in checks if not check.passed and check.reason]
    is_available = len(blocking_reasons) == 0

    return {
        "phase_id": S_PRED_PHASE_ID,
        "phase_name": S_PRED_PHASE_NAME,
        "method_version": data.method_version,
        "session_id": data.session_id,
        "status": "AVAILABLE" if is_available else "BLOCKED",
        "can_start_fase0": is_available,
        "transition_allowed": is_available,
        "next_phase": "FASE_0" if is_available else None,
        "gate_outcome": "DISPONIBILE" if is_available else "BLOCCO_SISTEMA_ASSOLUTO",
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
        "checks": [asdict(check) for check in checks],
        "trace": {
            "phase": S_PRED_PHASE_ID,
            "trace_type": "TECHNICAL_GATE",
            "validation_layer": "ROOT_RUNTIME",
            "indexing_status": data.indexing_status,
            "ranking_status": data.ranking_status,
            "shadow_store_present": data.shadow_store_available,
            "details_present": bool(data.details),
        },
    }
