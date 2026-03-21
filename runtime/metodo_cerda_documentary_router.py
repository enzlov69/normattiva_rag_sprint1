from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft202012Validator


JsonDict = Dict[str, Any]

_FORBIDDEN_M07_KEYS = {
    "m07_closed",
    "m07_completed",
    "m07_certified",
    "reading_complete_certified",
}

_FORBIDDEN_RAC_KEYS = {
    "rac_finalized",
    "rac_approved",
    "final_applicability",
    "final_norm_prevalence",
    "conclusive_reasoning",
}


class DocumentaryRouterError(ValueError):
    """Raised when the A-side documentary routing would violate Level A boundaries."""


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_schema() -> JsonDict:
    path = _project_root() / "schemas" / "method_documentary_routing_schema_v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_name(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _extract_packet(response_envelope: JsonDict) -> JsonDict:
    payload = response_envelope.get("payload")
    if not isinstance(payload, dict):
        return {}
    packet = payload.get("documentary_packet")
    if isinstance(packet, dict):
        return deepcopy(packet)
    return deepcopy(payload)


def _scan_forbidden_keys(node: Any, forbidden: set[str]) -> list[str]:
    hits: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if _normalize_name(key) in forbidden:
                hits.append(str(key))
            hits.extend(_scan_forbidden_keys(value, forbidden))
    elif isinstance(node, list):
        for item in node:
            hits.extend(_scan_forbidden_keys(item, forbidden))
    return hits


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value not in output:
            output.append(value)
    return output


def _build_m07_support(classified_case: JsonDict, packet: JsonDict) -> JsonDict:
    support = packet.get("m07_support")
    if isinstance(support, dict):
        support = deepcopy(support)
    else:
        support = {
            "ordered_reading_sequence": [],
            "annex_refs": [],
            "crossref_refs": [],
            "missing_elements": [],
            "m07_support_status": "PREPARATORY_ONLY",
        }

    forbidden_hits = _scan_forbidden_keys(support, _FORBIDDEN_M07_KEYS)
    if forbidden_hits:
        raise DocumentaryRouterError(
            "M07 support contains forbidden closure fields: " + ", ".join(_dedupe(forbidden_hits))
        )

    return {
        "record_type": "M07EvidencePack",
        "request_id": classified_case["request_id"],
        "case_id": classified_case["case_id"],
        "trace_id": classified_case["trace_id"],
        "source_layer": "A",
        "documentary_only": True,
        "human_completion_required": True,
        "support_scope": "DOCUMENTARY_ONLY",
        "ordered_reading_sequence": deepcopy(support.get("ordered_reading_sequence", [])),
        "annex_refs": deepcopy(support.get("annex_refs", [])),
        "crossref_refs": deepcopy(support.get("crossref_refs", [])),
        "missing_elements": deepcopy(support.get("missing_elements", [])),
        "normative_source_refs": deepcopy(
            [
                item.get("source_id") or item.get("id") or item.get("uri_ufficiale")
                for item in packet.get("sources", [])
                if isinstance(item, dict)
            ]
        ),
        "m07_support_status": "PREPARATORY_ONLY",
    }


def _build_rac_support(classified_case: JsonDict, packet: JsonDict, gate_output: JsonDict) -> JsonDict:
    rac_support = {
        "record_type": "RACDocumentaryInput",
        "request_id": classified_case["request_id"],
        "case_id": classified_case["case_id"],
        "trace_id": classified_case["trace_id"],
        "documentary_only": True,
        "sources": deepcopy(packet.get("sources", [])),
        "normative_units": deepcopy(packet.get("normative_units", packet.get("norm_units", []))),
        "citations": deepcopy(packet.get("citations", packet.get("citations_valid", []))),
        "coverage": deepcopy(packet.get("coverage")),
        "vigenza_status": deepcopy(packet.get("vigenza_status")),
        "rinvii_status": deepcopy(packet.get("rinvii_status")),
        "warning_flags": deepcopy(gate_output.get("warning_flags", [])),
        "critical_blocks": deepcopy(gate_output.get("critical_blocks", [])),
        "human_validation_required": True,
    }

    forbidden_hits = _scan_forbidden_keys(rac_support, _FORBIDDEN_RAC_KEYS)
    if forbidden_hits:
        raise DocumentaryRouterError(
            "RAC support contains forbidden conclusive fields: " + ", ".join(_dedupe(forbidden_hits))
        )
    return rac_support


def _build_ppav_supports(classified_case: JsonDict, packet: JsonDict, gate_output: JsonDict) -> list[JsonDict]:
    ppav_modules = [value for value in classified_case.get("moduli_attivati", []) if "PPAV" in str(value).upper()]
    supports: list[JsonDict] = []
    for module in ppav_modules:
        supports.append(
            {
                "record_type": "PPAVDocumentaryInput",
                "target_module": module,
                "request_id": classified_case["request_id"],
                "case_id": classified_case["case_id"],
                "trace_id": classified_case["trace_id"],
                "documentary_only": True,
                "coverage": deepcopy(packet.get("coverage")),
                "vigenza_status": deepcopy(packet.get("vigenza_status")),
                "rinvii_status": deepcopy(packet.get("rinvii_status")),
                "citations": deepcopy(packet.get("citations", packet.get("citations_valid", []))),
                "degraded": gate_output.get("gate_status") == "DEGRADE",
            }
        )
    return supports


def validate_routing_output(routing_output: JsonDict) -> None:
    validator = Draft202012Validator(_load_schema())
    errors = sorted(validator.iter_errors(routing_output), key=lambda error: error.path)
    if errors:
        raise DocumentaryRouterError(errors[0].message)


def route_documentary_support(
    classified_case: JsonDict,
    gate_output: JsonDict,
    response_envelope: JsonDict | None = None,
    institutional_web_recovery: JsonDict | None = None,
) -> JsonDict:
    gate_status = gate_output["gate_status"]
    packet = _extract_packet(response_envelope or {})

    if gate_status == "NOT_REQUIRED":
        output = {
            "request_id": classified_case["request_id"],
            "case_id": classified_case["case_id"],
            "trace_id": classified_case["trace_id"],
            "routing_status": "SKIPPED",
            "destinations": [],
            "m07_evidence_pack_ref": None,
            "rac_documentary_input_ref": None,
            "ppav_documentary_input_refs": [],
            "fascicolo_entry_ref": None,
            "audit_event_ref": None,
            "shadow_update_ref": None,
            "documentary_channel": gate_output.get("documentary_channel", "FEDERATED_ONLY"),
            "institutional_web_refs": [],
        }
        validate_routing_output(output)
        return output

    if gate_status == "BLOCK":
        output = {
            "request_id": classified_case["request_id"],
            "case_id": classified_case["case_id"],
            "trace_id": classified_case["trace_id"],
            "routing_status": "BLOCKED",
            "destinations": [],
            "m07_evidence_pack_ref": None,
            "rac_documentary_input_ref": None,
            "ppav_documentary_input_refs": [],
            "fascicolo_entry_ref": None,
            "audit_event_ref": None,
            "shadow_update_ref": None,
            "documentary_channel": gate_output.get("documentary_channel", "FEDERATED_ONLY"),
            "institutional_web_refs": [],
        }
        validate_routing_output(output)
        return output

    destinations = _dedupe(list(gate_output.get("allowed_routes", [])))
    m07_pack = _build_m07_support(classified_case, packet) if "M07_SUPPORT" in destinations else None
    rac_input = _build_rac_support(classified_case, packet, gate_output) if "RAC_SUPPORT" in destinations else None
    ppav_inputs = _build_ppav_supports(classified_case, packet, gate_output) if "PPAV_SUPPORT" in destinations else []

    output = {
        "request_id": classified_case["request_id"],
        "case_id": classified_case["case_id"],
        "trace_id": classified_case["trace_id"],
        "routing_status": "PARTIAL" if gate_status == "DEGRADE" else "ROUTED",
        "destinations": destinations,
        "m07_evidence_pack_ref": m07_pack,
        "rac_documentary_input_ref": rac_input,
        "ppav_documentary_input_refs": ppav_inputs,
        "fascicolo_entry_ref": {
            "record_type": "FascicoloDocumentaryEntry",
            "request_id": classified_case["request_id"],
            "trace_id": classified_case["trace_id"],
            "documentary_only": True,
            "gate_status": gate_status,
            "documentary_channel": gate_output.get("documentary_channel", "FEDERATED_ONLY"),
            "institutional_web_recovery": deepcopy(institutional_web_recovery),
        },
        "audit_event_ref": {
            "event_type": "A1_TER_DOCUMENTARY_ROUTED",
            "request_id": classified_case["request_id"],
            "trace_id": classified_case["trace_id"],
            "gate_status": gate_status,
            "documentary_channel": gate_output.get("documentary_channel", "FEDERATED_ONLY"),
            "institutional_web_used": bool(institutional_web_recovery and institutional_web_recovery.get("entries")),
        },
        "shadow_update_ref": {
            "update_type": "A1_TER_DOCUMENTARY_SHADOW_UPDATE",
            "trace_id": classified_case["trace_id"],
            "documentary_only": True,
            "gate_status": gate_status,
            "documentary_channel": gate_output.get("documentary_channel", "FEDERATED_ONLY"),
            "institutional_web_recovery_status": None if institutional_web_recovery is None else institutional_web_recovery.get("status"),
        },
        "documentary_channel": gate_output.get("documentary_channel", "FEDERATED_ONLY"),
        "institutional_web_refs": [] if institutional_web_recovery is None else deepcopy(institutional_web_recovery.get("entries", [])),
    }
    validate_routing_output(output)
    return output
