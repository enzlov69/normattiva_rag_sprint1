from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
import json

from .level_b_result_model import LevelBPayloadResult, ResponseStatus, ValidationReport


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"

FORBIDDEN_FIELD_NAMES = {
    "final_decision",
    "final_applicability",
    "legal_conclusion",
    "motivazione_finale",
    "output_authorized",
    "m07_closed",
    "ppav_closed",
    "go_finale",
    "rac_id",
    "rac_record",
    "final_gate_ref",
    "compliance_final_status",
}

FORBIDDEN_TEXT_MARKERS = {
    "caso risolto",
    "si conclude che",
    "output autorizzato",
    "m07 completato",
    "m07 chiuso",
    "go finale",
}


def load_status_registry() -> Dict[str, Any]:
    return json.loads((SCHEMA_DIR / "level_b_status_registry_v1.json").read_text(encoding="utf-8"))


def load_fail_code_registry() -> Dict[str, Any]:
    return json.loads((SCHEMA_DIR / "level_b_fail_code_registry_v1.json").read_text(encoding="utf-8"))


def load_fail_code_set() -> set[str]:
    data = load_fail_code_registry()
    return {item["code"] for item in data["fail_codes"]}


def load_registered_block_codes() -> set[str]:
    data = json.loads((SCHEMA_DIR / "level_b_payload_schema_v1.json").read_text(encoding="utf-8"))
    return set(data["$defs"]["block"]["properties"]["block_code"]["enum"])


def iter_paths(obj: Any, path: str = "") -> Iterable[Tuple[str, Any]]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            current = f"{path}/{key}"
            yield current, value
            yield from iter_paths(value, current)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            current = f"{path}/{index}"
            yield current, value
            yield from iter_paths(value, current)


def scan_for_forbidden_fields(payload: Dict[str, Any], report: ValidationReport) -> None:
    for path, value in iter_paths(payload):
        key = path.split("/")[-1] if path else ""
        if key in FORBIDDEN_FIELD_NAMES:
            report.add(
                "FORBIDDEN_LEVEL_B_FIELD",
                "CRITICAL",
                f"Campo vietato nel Livello B: {key}",
                path,
            )
        if isinstance(value, str):
            lowered = value.lower()
            for marker in FORBIDDEN_TEXT_MARKERS:
                if marker in lowered:
                    report.add(
                        "FORBIDDEN_LEVEL_B_SEMANTICS",
                        "CRITICAL",
                        f"Semantica conclusiva o validativa rilevata: {marker}",
                        path,
                    )


def validate_timestamp(value: str, report: ValidationReport) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        report.add("INVALID_TIMESTAMP", "ERROR", "timestamp non conforme a ISO 8601", "/timestamp")


def validate_status_coherence(result: LevelBPayloadResult, report: ValidationReport) -> None:
    if result.status == ResponseStatus.SUCCESS:
        if result.errors:
            report.add("BLOCK_PROPAGATION_INCOHERENT", "ERROR", "Status SUCCESS con errors valorizzati.", "/errors")
        if any(block.is_open for block in result.blocks):
            report.add("BLOCK_PROPAGATION_INCOHERENT", "CRITICAL", "Status SUCCESS con blocchi aperti.", "/blocks")

    if result.status == ResponseStatus.SUCCESS_WITH_WARNINGS and not result.warnings:
        report.add("WARNINGS_REQUIRED_FOR_DEGRADED_STATUS", "ERROR", "SUCCESS_WITH_WARNINGS richiede almeno un warning.", "/warnings")

    if result.status == ResponseStatus.DEGRADED and not (result.warnings or result.blocks):
        report.add("WARNINGS_REQUIRED_FOR_DEGRADED_STATUS", "ERROR", "DEGRADED richiede warning o blocchi.", "/warnings")

    if result.status == ResponseStatus.BLOCKED and not any(block.is_open for block in result.blocks):
        report.add("BLOCKS_REQUIRED_FOR_BLOCKED_STATUS", "CRITICAL", "BLOCKED richiede almeno un blocco aperto.", "/blocks")

    if result.status == ResponseStatus.REJECTED and not result.errors:
        report.add("ERRORS_REQUIRED_FOR_REJECTED_STATUS", "ERROR", "REJECTED richiede almeno un errore.", "/errors")

    if any(block.is_critical_open for block in result.blocks):
        if result.status not in {ResponseStatus.BLOCKED, ResponseStatus.REJECTED, ResponseStatus.ERROR}:
            report.add(
                "CRITICAL_BLOCK_STATUS_MISMATCH",
                "CRITICAL",
                "Un blocco critico aperto richiede almeno BLOCKED, REJECTED o ERROR.",
                "/status",
            )


def validate_blocks(result: LevelBPayloadResult, report: ValidationReport) -> None:
    registered = load_registered_block_codes()
    for index, block in enumerate(result.blocks):
        if block.block_code not in registered:
            report.add("INVALID_BLOCK_CODE", "ERROR", f"Codice blocco non registrato: {block.block_code}", f"/blocks/{index}/block_code")


def validate_audit_shadow(payload: Dict[str, Any], report: ValidationReport) -> None:
    audit = payload.get("audit")
    shadow = payload.get("shadow")

    if not audit or not shadow:
        report.add("AUDIT_SHADOW_REQUIRED", "CRITICAL", "Audit e SHADOW sono obbligatori nel payload del Livello B.", "/payload")
        return

    if not audit.get("events_present", False):
        report.add("AUDIT_INCOMPLETE", "CRITICAL", "Audit privo di eventi.", "/payload/audit/events_present")

    if not audit.get("critical_nodes_logged", False):
        report.add("AUDIT_INCOMPLETE", "CRITICAL", "Nodi critici non auditati.", "/payload/audit/critical_nodes_logged")

    if audit.get("missing_nodes"):
        report.add("AUDIT_INCOMPLETE", "CRITICAL", "Audit con nodi mancanti.", "/payload/audit/missing_nodes")

    if not shadow.get("executed_modules"):
        report.add("SHADOW_INCOMPLETE", "CRITICAL", "SHADOW senza executed_modules.", "/payload/shadow/executed_modules")

    if not shadow.get("retrieval_queries"):
        report.add("SHADOW_INCOMPLETE", "CRITICAL", "SHADOW senza retrieval_queries.", "/payload/shadow/retrieval_queries")

    if not shadow.get("documents_seen"):
        report.add("SHADOW_INCOMPLETE", "CRITICAL", "SHADOW senza documents_seen.", "/payload/shadow/documents_seen")


def validate_m07_boundaries(payload: Dict[str, Any], report: ValidationReport) -> None:
    m07 = payload.get("m07_support")
    if not m07:
        return

    if m07.get("human_completion_required") is not True:
        report.add(
            "M07_SUPPORT_HUMAN_COMPLETION_REQUIRED",
            "CRITICAL",
            "Nel supporto M07 il completamento umano è obbligatorio.",
            "/payload/m07_support/human_completion_required",
        )

    if "m07_closed" in m07 or "m07_completion_status" in m07 or "certified_complete" in m07:
        report.add(
            "M07_BOUNDARY_VIOLATION",
            "CRITICAL",
            "Il supporto M07 non può contenere campi di chiusura o certificazione.",
            "/payload/m07_support",
        )


def validate_citations(payload: Dict[str, Any], report: ValidationReport) -> None:
    citations = payload.get("citations_valid", [])
    for index, citation in enumerate(citations):
        if citation.get("citation_status") == "VALID" and not citation.get("uri_ufficiale"):
            report.add(
                "CITATION_VALID_WITHOUT_URI",
                "CRITICAL",
                "Citazione VALID priva di uri_ufficiale.",
                f"/payload/citations_valid/{index}/uri_ufficiale",
            )


def validate_minimum_contract(data: Dict[str, Any], report: ValidationReport) -> None:
    required = [
        ("request_id", "MISSING_REQUEST_ID"),
        ("case_id", "MISSING_CASE_ID"),
        ("trace_id", "MISSING_TRACE_ID"),
        ("api_version", "MISSING_API_VERSION"),
        ("responder_module", "MISSING_RESPONDER_MODULE"),
        ("payload", "MISSING_PAYLOAD"),
        ("status", "INVALID_STATUS"),
    ]
    for field_name, fail_code in required:
        if field_name not in data or data.get(field_name) in ("", None):
            report.add(fail_code, "ERROR", f"{field_name} mancante.", f"/{field_name}")

    if "status" in data:
        try:
            ResponseStatus(data["status"])
        except Exception:
            report.add("INVALID_STATUS", "ERROR", "status non ammesso dal contratto.", "/status")

    if "timestamp" in data and data.get("timestamp"):
        validate_timestamp(data["timestamp"], report)
    else:
        report.add("INVALID_TIMESTAMP", "ERROR", "timestamp mancante.", "/timestamp")
