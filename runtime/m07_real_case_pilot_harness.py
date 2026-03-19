
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

from runtime.m07_documentary_support_orchestrator import (
    orchestrate_m07_documentary_support,
)


class M07PilotHarnessError(Exception):
    """Base exception for the real-case pilot harness."""


class M07PilotCaseValidationError(M07PilotHarnessError):
    """Raised when a pilot case is incomplete or inconsistent."""


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_cases_path() -> Path:
    return _project_root() / "data" / "m07_real_case_pilot_cases_v1.json"


def load_pilot_cases(file_path: str | Path | None = None) -> list[dict[str, Any]]:
    path = Path(file_path) if file_path else _default_cases_path()
    payload = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(payload, list):
        raise M07PilotCaseValidationError("Il file dei casi pilota deve contenere una lista.")

    for case in payload:
        validate_pilot_case(case)

    return payload


def validate_pilot_case(case: dict[str, Any]) -> None:
    required = [
        "case_id",
        "title",
        "caller_module",
        "domain_target",
        "query_text",
        "goal_istruttorio",
        "source_priority",
        "expected_minimum_behavior",
        "expected_blocks_if_any",
        "simulation_profile",
        "include_m07_evidence_pack",
    ]
    missing = [key for key in required if key not in case]
    if missing:
        raise M07PilotCaseValidationError(
            f"Caso pilota incompleto {case.get('case_id', '<unknown>')}: campi mancanti {missing}"
        )

    if case["caller_module"] not in {
        "A1_OrchestratorePPAV",
        "A2_CaseClassifier",
        "A4_M07Governor",
    }:
        raise M07PilotCaseValidationError(
            f"Caller non ammesso per il caso {case['case_id']}: {case['caller_module']}"
        )

    if not isinstance(case["source_priority"], list) or not case["source_priority"]:
        raise M07PilotCaseValidationError(
            f"source_priority non valido per il caso {case['case_id']}"
        )

    if not isinstance(case["expected_blocks_if_any"], list):
        raise M07PilotCaseValidationError(
            f"expected_blocks_if_any deve essere una lista per il caso {case['case_id']}"
        )


def _build_m07_evidence_pack(case: dict[str, Any], trace_id: str) -> dict[str, Any]:
    return {
        "record_id": f"rec_{case['case_id']}",
        "record_type": "M07EvidencePack",
        "m07_pack_id": f"m07pack_{case['case_id']}",
        "case_id": case["case_id"],
        "source_ids": [f"source_{case['case_id']}"],
        "norm_unit_ids": [f"normunit_{case['case_id']}"],
        "ordered_reading_sequence": [],
        "annex_refs": [],
        "crossref_refs": [],
        "coverage_ref_id": f"cov_{case['case_id']}",
        "missing_elements": [],
        "m07_support_status": "READY_FOR_HUMAN_READING",
        "human_completion_required": True,
        "created_at": "2026-03-20T09:00:00Z",
        "updated_at": "2026-03-20T09:00:00Z",
        "schema_version": "1.0",
        "record_version": 1,
        "source_layer": "B",
        "trace_id": trace_id,
        "active_flag": True,
    }


def build_controlled_transport(case: dict[str, Any]) -> Callable[[dict[str, Any]], dict[str, Any]]:
    validate_pilot_case(case)
    profile = case["simulation_profile"]

    def fake_transport(request_payload: dict[str, Any]) -> dict[str, Any]:
        documentary_packet: dict[str, Any] = {
            "source_ids": [f"source_{case['case_id']}"],
            "norm_unit_ids": [f"normunit_{case['case_id']}"],
            "support_only_flag": True,
        }

        if case.get("include_m07_evidence_pack", True):
            documentary_packet["m07_evidence_pack"] = _build_m07_evidence_pack(
                case=case,
                trace_id=request_payload["trace_id"],
            )

        response = {
            "request_id": request_payload["request_id"],
            "case_id": request_payload["case_id"],
            "trace_id": request_payload["trace_id"],
            "api_version": "2.0",
            "responder_module": "B16_M07SupportLayer",
            "status": "SUCCESS",
            "payload": {"documentary_packet": documentary_packet},
            "warnings": [],
            "errors": [],
            "blocks": [],
            "timestamp": "2026-03-20T09:00:01Z",
        }

        if profile == "success":
            return response

        if profile == "success_with_warnings":
            response["status"] = "SUCCESS_WITH_WARNINGS"
            response["warnings"].append(
                {
                    "warning_code": "COVERAGE_PARTIAL",
                    "warning_message": "coverage non piena sul caso pilota",
                }
            )
            return response

        if profile == "blocked_citation_incomplete":
            response["status"] = "BLOCKED"
            response["blocks"].append(
                {
                    "block_id": f"blk_{case['case_id']}_citation_incomplete",
                    "case_id": request_payload["case_id"],
                    "block_code": "CITATION_INCOMPLETE",
                    "block_category": "CITATION",
                    "block_severity": "CRITICAL",
                    "origin_module": "B15_CitationBuilder",
                    "block_reason": "citazione incompleta nel caso pilota",
                    "block_status": "OPEN",
                }
            )
            if "m07_evidence_pack" in documentary_packet:
                documentary_packet["m07_evidence_pack"]["missing_elements"] = ["citazione incompleta"]
                documentary_packet["m07_evidence_pack"]["m07_support_status"] = "BLOCKED_SUPPORT"
            return response

        raise M07PilotHarnessError(
            f"Simulation profile non riconosciuto per il caso {case['case_id']}: {profile}"
        )

    return fake_transport


def run_pilot_case(
    case: dict[str, Any],
    *,
    session_id_prefix: str = "pilot_session",
    transport: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    validate_pilot_case(case)

    selected_transport = transport or build_controlled_transport(case)

    envelope = orchestrate_m07_documentary_support(
        transport=selected_transport,
        session_id=f"{session_id_prefix}_{case['case_id']}",
        request_id=f"req_{case['case_id']}",
        case_id=case["case_id"],
        trace_id=f"trace_{case['case_id']}",
        timestamp="2026-03-20T09:00:00Z",
        caller_module=case["caller_module"],
        goal_istruttorio=case["goal_istruttorio"],
        domain_target=case["domain_target"],
        query_text=case["query_text"],
        source_priority=case["source_priority"],
        reading_focus=case.get("reading_focus"),
        metadata_filters=case.get("metadata_filters"),
        notes=case.get("notes"),
    )

    envelope["pilot_mode"] = True
    envelope["real_case_flag"] = True
    envelope["case_title"] = case["title"]
    envelope["expected_minimum_behavior"] = case["expected_minimum_behavior"]
    envelope["expected_blocks_if_any"] = copy.deepcopy(case["expected_blocks_if_any"])
    envelope["decision_disabled"] = True
    envelope["runner_federated_touched"] = False
    return envelope


def run_pilot_batch(
    cases: list[dict[str, Any]],
    *,
    session_id_prefix: str = "pilot_batch",
) -> list[dict[str, Any]]:
    return [run_pilot_case(case, session_id_prefix=session_id_prefix) for case in cases]


def summarize_pilot_batch(envelopes: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "total_cases": len(envelopes),
        "success": 0,
        "success_with_warnings": 0,
        "degraded": 0,
        "blocked": 0,
        "rejected": 0,
        "error": 0,
        "runner_federated_touched": False,
        "decision_enabled": False,
        "output_authorization_enabled": False,
    }

    for envelope in envelopes:
        status = envelope["orchestration_status"].lower()
        if status in summary:
            summary[status] += 1

        if envelope.get("runner_federated_touched") is True:
            summary["runner_federated_touched"] = True
        if envelope.get("can_emit_go_no_go") is True:
            summary["decision_enabled"] = True
        if envelope.get("can_authorize_output") is True:
            summary["output_authorization_enabled"] = True

    return summary
