"""Mapper di normalizzazione della risposta raw del runner.

Il modulo trasforma un payload raw del runner in un DocumentaryPacket conforme
al collegamento finale A/B, senza introdurre semantiche conclusive o
validative nel Livello B.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

REQUIRED_DOCUMENTARY_FIELDS: Tuple[str, ...] = (
    "sources",
    "norm_units",
    "citations_valid",
    "citations_blocked",
    "vigenza_records",
    "cross_reference_records",
    "coverage_assessment",
    "warnings",
    "errors",
    "blocks",
    "shadow_fragment",
)

FORBIDDEN_LEVEL_B_FIELDS = {
    "final_decision",
    "applicability_final",
    "m07_closed",
    "m07_certified",
    "reading_integral_certified",
    "compliance_go",
    "go_no_go",
    "output_authorized",
    "final_validation",
    "opponible_output",
    "rac_opponibile",
    "go_final",
    "no_go",
}

DEFAULT_CRITICAL_BLOCK_CODES = {
    "CORPUS_MISSING",
    "SOURCE_UNVERIFIED",
    "CITATION_INCOMPLETE",
    "VIGENZA_UNCERTAIN",
    "CROSSREF_UNRESOLVED",
    "M07_REQUIRED",
    "RAG_SCOPE_VIOLATION",
    "AUDIT_INCOMPLETE",
    "OUTPUT_NOT_OPPONIBLE",
    "COVERAGE_INADEQUATE",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _normalize_message_items(items: Sequence[Any], *, item_type: str) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            code = item.get("code") or item.get("warning_code") or item.get("error_code") or item.get("block_code")
            message = item.get("message") or item.get("reason") or item.get("detail") or item.get("text")
            entry = deepcopy(item)
            if code:
                entry["code"] = code
            if message:
                entry["message"] = message
            if not entry.get("code"):
                entry["code"] = f"{item_type.upper()}_UNSPECIFIED"
            if not entry.get("message"):
                entry["message"] = f"{item_type} without explicit message"
            normalized.append(entry)
            continue

        if isinstance(item, str):
            normalized.append(
                {
                    "code": item,
                    "message": item.replace("_", " ").title(),
                }
            )
            continue

        normalized.append(
            {
                "code": f"{item_type.upper()}_UNSPECIFIED",
                "message": f"Unrecognized {item_type} entry",
            }
        )
    return normalized


def _normalize_blocks(items: Sequence[Any]) -> List[Dict[str, Any]]:
    normalized = _normalize_message_items(items, item_type="block")
    for entry in normalized:
        entry.setdefault("block_code", entry["code"])
        entry.setdefault("block_category", "DOCUMENTARY")
        entry.setdefault("block_severity", "CRITICAL")
        entry.setdefault("block_reason", entry["message"])
        entry.setdefault("block_status", "OPEN")
    return normalized


def _iter_keys(obj: Any, path: str = "") -> Iterable[Tuple[str, str, Any]]:
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else str(key)
            yield str(key), new_path, value
            yield from _iter_keys(value, new_path)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            new_path = f"{path}[{index}]"
            yield from _iter_keys(value, new_path)


def _find_forbidden_fields(obj: Any) -> List[Dict[str, str]]:
    matches: List[Dict[str, str]] = []
    for key, path, _value in _iter_keys(obj):
        if key in FORBIDDEN_LEVEL_B_FIELDS:
            matches.append({"field": key, "path": path})
    return matches


def _extract_documentary_payload(raw_response: Mapping[str, Any]) -> Dict[str, Any]:
    for candidate in ("documentary_packet", "payload", "result", "results"):
        value = raw_response.get(candidate)
        if isinstance(value, Mapping):
            return deepcopy(dict(value))

    return deepcopy(dict(raw_response))


def _ensure_required_packet_shape(packet: MutableMapping[str, Any]) -> List[str]:
    missing: List[str] = []
    defaults: Dict[str, Any] = {
        "sources": [],
        "norm_units": [],
        "citations_valid": [],
        "citations_blocked": [],
        "vigenza_records": [],
        "cross_reference_records": [],
        "coverage_assessment": {},
        "warnings": [],
        "errors": [],
        "blocks": [],
        "shadow_fragment": {},
    }
    for field_name in REQUIRED_DOCUMENTARY_FIELDS:
        if field_name not in packet:
            missing.append(field_name)
            packet[field_name] = deepcopy(defaults[field_name])
    return missing


def build_scope_violation_block(*, matches: Sequence[Mapping[str, str]]) -> Dict[str, Any]:
    fields = ", ".join(sorted({match["field"] for match in matches}))
    return {
        "code": "RAG_SCOPE_VIOLATION",
        "block_code": "RAG_SCOPE_VIOLATION",
        "block_category": "BOUNDARY",
        "block_severity": "CRITICAL",
        "message": f"Forbidden Level B fields detected: {fields}",
        "block_reason": f"Forbidden Level B fields detected: {fields}",
        "block_status": "OPEN",
        "matches": list(matches),
    }


def build_missing_structure_block(*, missing_fields: Sequence[str]) -> Dict[str, Any]:
    field_list = ", ".join(missing_fields)
    return {
        "code": "OUTPUT_NOT_OPPONIBLE",
        "block_code": "OUTPUT_NOT_OPPONIBLE",
        "block_category": "DOCUMENTARY",
        "block_severity": "CRITICAL",
        "message": f"Incomplete DocumentaryPacket structure: {field_list}",
        "block_reason": f"Incomplete DocumentaryPacket structure: {field_list}",
        "block_status": "OPEN",
        "missing_fields": list(missing_fields),
    }


def map_runner_response_to_documentary_packet(
    *,
    raw_response: Mapping[str, Any],
    case_id: str,
    trace_id: str,
    source_layer: str = "B",
    schema_version: str = "v1",
    mapping_version: str = "final_ab_runner_response_map_v1",
    runner_entrypoint: str = "runner_black_box",
) -> Dict[str, Any]:
    """Normalizza la risposta raw del runner in un DocumentaryPacket.

    Returns:
        Dict con chiavi:
        - documentary_packet
        - warnings
        - errors
        - blocks
        - status
    """
    raw_copy = deepcopy(dict(raw_response))
    forbidden_matches = _find_forbidden_fields(raw_copy)

    documentary_packet = _extract_documentary_payload(raw_copy)
    missing_fields = _ensure_required_packet_shape(documentary_packet)

    documentary_packet["warnings"] = _normalize_message_items(
        _as_list(documentary_packet.get("warnings")), item_type="warning"
    )
    documentary_packet["errors"] = _normalize_message_items(
        _as_list(documentary_packet.get("errors")), item_type="error"
    )
    documentary_packet["blocks"] = _normalize_blocks(_as_list(documentary_packet.get("blocks")))

    top_level_warnings = _normalize_message_items(_as_list(raw_copy.get("warnings")), item_type="warning")
    top_level_errors = _normalize_message_items(_as_list(raw_copy.get("errors")), item_type="error")
    top_level_blocks = _normalize_blocks(_as_list(raw_copy.get("blocks")))

    warnings = documentary_packet["warnings"] + top_level_warnings
    errors = documentary_packet["errors"] + top_level_errors
    blocks = documentary_packet["blocks"] + top_level_blocks

    if missing_fields:
        blocks.append(build_missing_structure_block(missing_fields=missing_fields))
        warnings.append(
            {
                "code": "DOCUMENTARY_PACKET_DEGRADED",
                "message": "Il runner ha restituito una struttura documentale incompleta.",
            }
        )

    if forbidden_matches:
        blocks.append(build_scope_violation_block(matches=forbidden_matches))
        errors.append(
            {
                "code": "FORBIDDEN_LEVEL_B_FIELDS_DETECTED",
                "message": "Il runner ha prodotto campi vietati nel perimetro del Livello B.",
            }
        )

    if blocks and not warnings:
        warnings.append(
            {
                "code": "CRITICALITIES_PRESENT",
                "message": "Sono presenti criticità documentali o di boundary.",
            }
        )

    normalized_block_codes = {
        block.get("block_code") or block.get("code") for block in blocks if isinstance(block, dict)
    }
    normalized_block_codes.discard(None)

    shadow_fragment = deepcopy(documentary_packet.get("shadow_fragment") or {})
    timestamp = _utc_now_iso()
    shadow_fragment.setdefault("source_layer", source_layer)
    shadow_fragment.setdefault("schema_version", schema_version)
    shadow_fragment.setdefault("record_version", "1")
    shadow_fragment.setdefault("case_id", case_id)
    shadow_fragment.setdefault("trace_id", trace_id)
    shadow_fragment.setdefault("created_at", timestamp)
    shadow_fragment["updated_at"] = timestamp
    shadow_fragment.setdefault("runner_entrypoint", runner_entrypoint)
    shadow_fragment.setdefault("mapping_version", mapping_version)
    shadow_fragment.setdefault(
        "normalization_notes",
        [
            "Runner response normalized into DocumentaryPacket.",
            "No conclusory or decision-making semantics admitted in Level B.",
        ],
    )
    documentary_packet["shadow_fragment"] = shadow_fragment
    documentary_packet["warnings"] = warnings
    documentary_packet["errors"] = errors
    documentary_packet["blocks"] = blocks

    if "RAG_SCOPE_VIOLATION" in normalized_block_codes:
        status = "REJECTED"
    elif normalized_block_codes & DEFAULT_CRITICAL_BLOCK_CODES:
        status = "BLOCKED"
    elif missing_fields:
        status = "DEGRADED"
    elif warnings:
        status = "SUCCESS_WITH_WARNINGS"
    else:
        status = "SUCCESS"

    return {
        "documentary_packet": documentary_packet,
        "warnings": warnings,
        "errors": errors,
        "blocks": blocks,
        "status": status,
    }
