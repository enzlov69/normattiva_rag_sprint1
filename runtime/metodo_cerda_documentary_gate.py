from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable

from jsonschema import Draft202012Validator
from src.config.settings import OFFICIAL_SOURCE_DOMAINS


JsonDict = Dict[str, Any]

_RAC_FORBIDDEN_FIELDS = {
    "rac_finalized",
    "rac_approved",
    "final_applicability",
    "final_norm_prevalence",
    "conclusive_reasoning",
}

_M07_SEMANTIC_TOKENS = (
    "m07_closed",
    "m07_completed",
    "m07_certified",
    "reading_complete_certified",
)

_RAC_SEMANTIC_TOKENS = (
    "rac_finalized",
    "rac_approved",
    "final_applicability",
    "final_norm_prevalence",
    "conclusive_reasoning",
)

_DEGRADE_COVERAGE_STATUSES = {"PARTIAL", "LIMITED", "DEGRADED"}
_PROCEED_COVERAGE_STATUSES = {"ADEQUATE", "SUFFICIENT", "FULL", "CONFIRMED", "OK"}
_BLOCK_COVERAGE_STATUSES = {"INADEQUATE", "INSUFFICIENT", "UNAVAILABLE"}
_BLOCK_VIGENZA_STATUSES = {"UNCERTAIN", "NOT_CONFIRMED", "BLOCKED"}
_PROCEED_VIGENZA_STATUSES = {"CONFIRMED", "VIGENTE", "VIGENTE_VERIFICATA", "OK"}
_BLOCK_RINVII_STATUSES = {"UNRESOLVED", "BLOCKED"}
_PROCEED_RINVII_STATUSES = {"RESOLVED", "OK", "CONFIRMED"}
_INSTITUTIONAL_WEB_TRIGGER_CODES = {
    "COVERAGE_INADEQUATE",
    "VIGENZA_UNCERTAIN",
    "CROSSREF_UNRESOLVED",
    "DOCUMENTARY_PACKET_INCOMPLETE",
}


class DocumentaryGateError(ValueError):
    """Raised when the Level A documentary gate cannot evaluate a packet coherently."""


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_json(filename: str) -> JsonDict:
    path = _project_root() / "schemas" / filename
    return json.loads(path.read_text(encoding="utf-8"))


def _load_gate_schema() -> JsonDict:
    return _load_json("method_documentary_gate_output_schema_v1.json")


def _load_forbidden_fields() -> set[str]:
    forbidden: set[str] = set()

    for entry in _load_json("level_b_forbidden_fields_registry_v1.json").get("forbidden_fields", []):
        forbidden.add(str(entry))

    for entry in _load_json("final_ab_forbidden_level_b_fields_registry_v1.json").get("entries", []):
        if isinstance(entry, dict) and entry.get("field_name"):
            forbidden.add(str(entry["field_name"]))

    forbidden.update(_load_json("final_ab_m07_boundary_registry_v1.json").get("forbidden_fields", []))
    forbidden.update(_RAC_FORBIDDEN_FIELDS)
    return {value.strip() for value in forbidden if str(value).strip()}


def _load_critical_block_codes() -> set[str]:
    registry = _load_json("final_block_registry_v1.json")
    return {
        str(entry.get("block_code")).strip()
        for entry in registry.get("blocks", [])
        if isinstance(entry, dict) and entry.get("block_code")
    }


def _normalize_name(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _uri_has_official_domain(uri: str) -> bool:
    normalized = str(uri or "").strip().lower()
    return any(domain in normalized for domain in OFFICIAL_SOURCE_DOMAINS)


def _scan_keys(node: Any, *, path: str = "$") -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            current = f"{path}.{key}"
            findings.append((str(key), current))
            findings.extend(_scan_keys(value, path=current))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            findings.extend(_scan_keys(item, path=f"{path}[{index}]"))
    return findings


def _scan_strings(node: Any) -> Iterable[str]:
    if isinstance(node, dict):
        for value in node.values():
            yield from _scan_strings(value)
    elif isinstance(node, list):
        for item in node:
            yield from _scan_strings(item)
    elif isinstance(node, str):
        yield node


def _extract_status(value: Any, *, nested_keys: tuple[str, ...] = ("status",)) -> str:
    if isinstance(value, dict):
        for key in nested_keys:
            nested = value.get(key)
            if nested not in (None, ""):
                return str(nested).upper()
        for key in ("coverage_status", "state", "result"):
            nested = value.get(key)
            if nested not in (None, ""):
                return str(nested).upper()
        return "UNKNOWN"
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                extracted = _extract_status(item, nested_keys=nested_keys)
                if extracted != "UNKNOWN":
                    return extracted
        return "UNKNOWN"
    if value in (None, ""):
        return "UNKNOWN"
    return str(value).upper()


def _extract_documentary_packet(response_envelope: JsonDict) -> JsonDict:
    payload = response_envelope.get("payload")
    if not isinstance(payload, dict):
        return {}
    packet = payload.get("documentary_packet")
    if isinstance(packet, dict):
        packet = deepcopy(packet)
    else:
        packet = deepcopy(payload)

    packet.setdefault("sources", packet.get("sources", []))
    packet.setdefault("normative_units", packet.get("normative_units", packet.get("norm_units", [])))
    packet.setdefault("citations", packet.get("citations", packet.get("citations_valid", [])))
    packet.setdefault(
        "incomplete_citations",
        packet.get("incomplete_citations", packet.get("citations_blocked", [])),
    )
    if "coverage" not in packet:
        if "coverage_assessment" in packet:
            packet["coverage"] = packet.get("coverage_assessment", "UNKNOWN")
        elif packet.get("sources") or packet.get("citations") or packet.get("citations_valid"):
            packet["coverage"] = "UNSPECIFIED"
        else:
            packet["coverage"] = "UNKNOWN"
    if "vigenza_status" not in packet:
        if "vigenza_records" in packet:
            packet["vigenza_status"] = packet.get("vigenza_records", "UNKNOWN")
        else:
            citations = packet.get("citations") or packet.get("citations_valid") or []
            citation_statuses = [
                item.get("stato_vigenza")
                for item in citations
                if isinstance(item, dict) and item.get("stato_vigenza")
            ]
            packet["vigenza_status"] = citation_statuses[0] if citation_statuses else "UNSPECIFIED"
    if "rinvii_status" not in packet:
        if "cross_reference_records" in packet:
            packet["rinvii_status"] = packet.get("cross_reference_records", "UNKNOWN")
        else:
            packet["rinvii_status"] = "UNSPECIFIED"
    if "audit" not in packet and isinstance(payload.get("audit"), dict):
        packet["audit"] = deepcopy(payload["audit"])
    if "shadow" not in packet and isinstance(payload.get("shadow"), dict):
        packet["shadow"] = deepcopy(payload["shadow"])
    return packet


def _contains_semantic_forbidden_text(packet: JsonDict) -> bool:
    normalized_text = " ".join(_normalize_name(value) for value in _scan_strings(packet))
    return any(token in normalized_text for token in _M07_SEMANTIC_TOKENS + _RAC_SEMANTIC_TOKENS)


def _detect_forbidden_fields(response_envelope: JsonDict, packet: JsonDict) -> list[str]:
    forbidden = {_normalize_name(value) for value in _load_forbidden_fields()}
    hits: list[str] = []
    for key, path in _scan_keys(response_envelope):
        normalized_key = _normalize_name(key)
        if normalized_key in forbidden:
            hits.append(path)
    if _contains_semantic_forbidden_text(packet):
        hits.append("$.payload.documentary_packet::<semantic_token>")
    deduped: list[str] = []
    for hit in hits:
        if hit not in deduped:
            deduped.append(hit)
    return deduped


def _normalize_issue_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return deepcopy(value)
    if value is None:
        return []
    return [deepcopy(value)]


def _extract_block_codes(blocks: list[Any]) -> list[str]:
    codes: list[str] = []
    for block in blocks:
        if isinstance(block, dict):
            code = block.get("block_code") or block.get("code")
        else:
            code = block
        if code:
            text = str(code)
            if text not in codes:
                codes.append(text)
    return codes


def _coverage_is_degradable(packet: JsonDict) -> bool:
    coverage = packet.get("coverage")
    if isinstance(coverage, dict):
        return coverage.get("critical_gap_flag") is False
    coverage_assessment = packet.get("coverage_assessment")
    if isinstance(coverage_assessment, dict):
        return coverage_assessment.get("critical_gap_flag") is False
    return False


def _packet_complete(packet: JsonDict) -> bool:
    required = (
        "sources",
        "normative_units",
        "citations",
        "incomplete_citations",
        "vigenza_status",
        "rinvii_status",
        "coverage",
    )
    return all(key in packet for key in required)


def _packet_has_verified_official_source(packet: JsonDict) -> bool:
    sources = packet.get("sources", [])
    citations = packet.get("citations", [])
    for item in list(sources) + list(citations):
        if not isinstance(item, dict):
            continue
        uri = item.get("uri_ufficiale") or item.get("uri")
        if uri and _uri_has_official_domain(str(uri)):
            return True
    return False


def _audit_shadow_complete(packet: JsonDict, response_envelope: JsonDict) -> bool:
    audit = packet.get("audit", response_envelope.get("audit"))
    shadow = packet.get("shadow", response_envelope.get("shadow"))
    return isinstance(audit, dict) and bool(audit) and isinstance(shadow, dict) and bool(shadow)


def _resolve_allowed_routes(classified_case: JsonDict, gate_status: str) -> list[str]:
    if gate_status in {"BLOCK", "NOT_REQUIRED"}:
        return []

    modules = {_normalize_name(value) for value in classified_case.get("moduli_attivati", [])}
    routes = ["FASCICOLO_SUPPORT", "AUDIT_UPDATE", "SHADOW_UPDATE"]

    if any("m07" in module for module in modules):
        routes.append("M07_SUPPORT")
    if any("rac" in module for module in modules):
        routes.append("RAC_SUPPORT")

    ppav_modules = [module for module in classified_case.get("moduli_attivati", []) if "PPAV" in str(module).upper()]
    if ppav_modules:
        routes.append("PPAV_SUPPORT")

    deduped: list[str] = []
    for route in routes:
        if route not in deduped:
            deduped.append(route)
    return deduped


def validate_gate_output_schema(gate_output: JsonDict) -> None:
    validator = Draft202012Validator(_load_gate_schema())
    errors = sorted(validator.iter_errors(gate_output), key=lambda error: error.path)
    if errors:
        raise DocumentaryGateError(errors[0].message)


def build_not_required_gate_output(classified_case: JsonDict) -> JsonDict:
    output = {
        "request_id": classified_case["request_id"],
        "case_id": classified_case["case_id"],
        "trace_id": classified_case["trace_id"],
        "gate_status": "NOT_REQUIRED",
        "level_b_status": "NOT_INVOKED",
        "critical_blocks": [],
        "warning_flags": [],
        "degradation_reasons": [],
        "forbidden_field_detected": False,
        "forbidden_fields": [],
        "packet_complete": False,
        "allowed_routes": [],
        "audit_required": True,
        "shadow_required": True,
        "documentary_channel": "FEDERATED_ONLY",
        "institutional_web_required": False,
        "institutional_web_reason": [],
    }
    validate_gate_output_schema(output)
    return output


def evaluate_documentary_gate(
    classified_case: JsonDict,
    response_envelope: JsonDict,
) -> JsonDict:
    packet = _extract_documentary_packet(response_envelope)
    warnings = _normalize_issue_list(response_envelope.get("warnings")) + _normalize_issue_list(packet.get("warnings"))
    errors = _normalize_issue_list(response_envelope.get("errors")) + _normalize_issue_list(packet.get("errors"))
    blocks = _normalize_issue_list(response_envelope.get("blocks")) + _normalize_issue_list(packet.get("blocks"))
    forbidden_fields = _detect_forbidden_fields(response_envelope, packet)
    critical_block_codes = _load_critical_block_codes()
    block_codes = _extract_block_codes(blocks)
    sensitivity = _normalize_name(classified_case.get("sensibilita"))
    intensity = _normalize_name(classified_case.get("intensita_applicativa"))
    sensitive_case = sensitivity in {"alta", "high", "critica", "critical"}
    high_intensity_case = intensity in {"alta", "high", "elevata"}

    critical_blocks = [
        code
        for code in block_codes
        if code in critical_block_codes
        and not (
            code == "COVERAGE_INADEQUATE"
            and _coverage_is_degradable(packet)
            and not high_intensity_case
            and not sensitive_case
        )
    ]

    packet_complete = _packet_complete(packet)
    audit_shadow_complete = _audit_shadow_complete(packet, response_envelope)
    verified_official_source = _packet_has_verified_official_source(packet)
    coverage_status = _extract_status(packet.get("coverage"))
    vigenza_status = _extract_status(packet.get("vigenza_status"))
    rinvii_status = _extract_status(packet.get("rinvii_status"))

    degradation_reasons: list[str] = []

    if not packet_complete:
        critical_blocks.append("DOCUMENTARY_PACKET_INCOMPLETE")
    if not audit_shadow_complete:
        critical_blocks.append("AUDIT_INCOMPLETE")
    if forbidden_fields:
        critical_blocks.append("RAG_SCOPE_VIOLATION")
    if coverage_status in _BLOCK_COVERAGE_STATUSES:
        critical_blocks.append("COVERAGE_INADEQUATE")
    elif coverage_status in _DEGRADE_COVERAGE_STATUSES:
        degradation_reasons.append(f"COVERAGE_{coverage_status}")

    if vigenza_status in _BLOCK_VIGENZA_STATUSES and sensitive_case:
        critical_blocks.append("VIGENZA_UNCERTAIN")
    elif vigenza_status not in _PROCEED_VIGENZA_STATUSES and vigenza_status != "UNSPECIFIED":
        degradation_reasons.append(f"VIGENZA_{vigenza_status}")

    if rinvii_status in _BLOCK_RINVII_STATUSES and high_intensity_case:
        critical_blocks.append("CROSSREF_UNRESOLVED")
    elif rinvii_status not in _PROCEED_RINVII_STATUSES and rinvii_status != "UNSPECIFIED":
        degradation_reasons.append(f"RINVII_{rinvii_status}")

    if warnings:
        degradation_reasons.append("LEVEL_B_WARNINGS_PRESENT")
    if not verified_official_source:
        degradation_reasons.append("OFFICIAL_SOURCE_CONFIRMATION_PENDING")

    deduped_critical: list[str] = []
    for code in critical_blocks:
        if code not in deduped_critical:
            deduped_critical.append(code)

    deduped_degradation: list[str] = []
    for reason in degradation_reasons:
        if reason not in deduped_degradation:
            deduped_degradation.append(reason)

    if deduped_critical:
        gate_status = "BLOCK"
    elif deduped_degradation or str(response_envelope.get("status")).upper() in {"DEGRADED", "SUCCESS_WITH_WARNINGS"}:
        gate_status = "DEGRADE"
    else:
        gate_status = "PROCEED"

    institutional_web_reason = [
        code for code in deduped_critical if code in _INSTITUTIONAL_WEB_TRIGGER_CODES
    ]
    if not verified_official_source:
        institutional_web_reason.append("OFFICIAL_SOURCE_CONFIRMATION_PENDING")
    if coverage_status in _DEGRADE_COVERAGE_STATUSES:
        institutional_web_reason.append("COVERAGE_COMPLETION_REQUIRED")
    institutional_web_reason = _dedupe(institutional_web_reason)

    if gate_status == "PROCEED":
        documentary_channel = "FEDERATED_ONLY" if verified_official_source else "FEDERATED_PLUS_INSTITUTIONAL_WEB"
    elif institutional_web_reason and not packet.get("sources"):
        documentary_channel = "INSTITUTIONAL_WEB_ONLY"
    elif institutional_web_reason:
        documentary_channel = "FEDERATED_PLUS_INSTITUTIONAL_WEB"
    else:
        documentary_channel = "FEDERATED_ONLY"

    output = {
        "request_id": classified_case["request_id"],
        "case_id": classified_case["case_id"],
        "trace_id": classified_case["trace_id"],
        "gate_status": gate_status,
        "level_b_status": str(response_envelope.get("status") or "UNKNOWN").upper(),
        "critical_blocks": deduped_critical,
        "warning_flags": [str(item.get("code") or item) for item in warnings],
        "degradation_reasons": deduped_degradation,
        "forbidden_field_detected": bool(forbidden_fields),
        "forbidden_fields": forbidden_fields,
        "packet_complete": bool(packet_complete and audit_shadow_complete),
        "allowed_routes": _resolve_allowed_routes(classified_case, gate_status),
        "audit_required": True,
        "shadow_required": True,
        "documentary_channel": documentary_channel,
        "institutional_web_required": bool(institutional_web_reason),
        "institutional_web_reason": institutional_web_reason,
    }
    validate_gate_output_schema(output)
    return output


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value not in output:
            output.append(value)
    return output
