from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator, RefResolver
from jsonschema.exceptions import ValidationError


FORBIDDEN_DECISION_KEYS = {
    "final_decision",
    "final_applicability",
    "legal_conclusion",
    "motivazione_finale",
    "output_authorized",
    "m07_closed",
    "ppav_closed",
    "go_finale",
}

ALLOWED_RESPONSE_STATUSES = {
    "SUCCESS",
    "SUCCESS_WITH_WARNINGS",
    "DEGRADED",
    "BLOCKED",
    "REJECTED",
    "ERROR",
}


class M07AdapterError(Exception):
    """Base exception for the M07 documentary support adapter."""


class M07RequestValidationError(M07AdapterError):
    """Raised when the outbound request is invalid."""


class M07ResponseValidationError(M07AdapterError):
    """Raised when the inbound response is invalid."""


class M07BoundaryViolationError(M07AdapterError):
    """Raised when Level B attempts conclusive/forbidden semantics."""


class M07TransportError(M07AdapterError):
    """Raised when the transport callable fails."""


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _schemas_dir() -> Path:
    return _project_root() / "schemas"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_bundle() -> dict[str, dict[str, Any]]:
    schemas_dir = _schemas_dir()
    request_name = "m07_documentary_support_request_schema_v1.json"
    response_name = "m07_documentary_support_response_schema_v1.json"
    m07_name = "m07_evidence_pack_schema_v1.json"

    return {
        request_name: _load_json(schemas_dir / request_name),
        response_name: _load_json(schemas_dir / response_name),
        m07_name: _load_json(schemas_dir / m07_name),
    }


def _build_validator(schema_name: str) -> Draft202012Validator:
    schemas = _schema_bundle()
    if schema_name not in schemas:
        raise M07AdapterError(f"Schema non trovato: {schema_name}")

    schema = schemas[schema_name]
    schemas_dir = _schemas_dir()

    store: dict[str, Any] = {}
    for name, loaded_schema in schemas.items():
        schema_path = (schemas_dir / name).resolve()
        file_uri = schema_path.as_uri()
        schema_id = loaded_schema.get("$id")

        store[file_uri] = loaded_schema
        if schema_id:
            store[schema_id] = loaded_schema

    base_uri = (schemas_dir / schema_name).resolve().as_uri()
    resolver = RefResolver(base_uri=base_uri, referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


def _scan_for_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []

    if isinstance(value, dict):
        for key, nested_value in value.items():
            current_path = f"{path}.{key}"
            if key in FORBIDDEN_DECISION_KEYS:
                found.append(current_path)
            found.extend(_scan_for_forbidden_keys(nested_value, current_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current_path = f"{path}[{index}]"
            found.extend(_scan_for_forbidden_keys(item, current_path))

    return found


def _extract_documentary_packet(response_payload: dict[str, Any]) -> dict[str, Any]:
    payload = response_payload.get("payload")
    if not isinstance(payload, dict):
        return {}

    documentary_packet = payload.get("documentary_packet")
    if not isinstance(documentary_packet, dict):
        return {}

    return documentary_packet


def _precheck_response_boundary_rules(response_payload: dict[str, Any]) -> None:
    forbidden_paths = _scan_for_forbidden_keys(response_payload)
    if forbidden_paths:
        raise M07BoundaryViolationError(
            "Campi conclusivi o vietati rilevati nella response del Livello B: "
            + ", ".join(forbidden_paths)
        )

    documentary_packet = _extract_documentary_packet(response_payload)

    if documentary_packet:
        support_only_flag = documentary_packet.get("support_only_flag")
        if support_only_flag is not True:
            raise M07BoundaryViolationError(
                "Il documentary packet del Livello B deve avere support_only_flag = true."
            )

        m07_evidence_pack = documentary_packet.get("m07_evidence_pack")
        if m07_evidence_pack is not None:
            if not isinstance(m07_evidence_pack, dict):
                raise M07BoundaryViolationError(
                    "m07_evidence_pack deve essere un oggetto valido del Livello B."
                )

            if m07_evidence_pack.get("human_completion_required") is not True:
                raise M07BoundaryViolationError(
                    "M07EvidencePack deve imporre human_completion_required = true."
                )

            if m07_evidence_pack.get("source_layer") != "B":
                raise M07BoundaryViolationError(
                    "M07EvidencePack deve dichiarare source_layer = 'B'."
                )


def _normalize_adapter_status(
    response_status: str,
    blocks: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> str:
    if response_status not in ALLOWED_RESPONSE_STATUSES:
        raise M07ResponseValidationError(
            f"Status di response non ammesso: {response_status}"
        )

    if response_status == "REJECTED":
        return "REJECTED"
    if response_status == "ERROR":
        return "ERROR"
    if response_status == "BLOCKED":
        return "BLOCKED"
    if response_status == "DEGRADED":
        return "DEGRADED"
    if errors:
        return "ERROR"
    if blocks:
        return "BLOCKED"
    if warnings or response_status == "SUCCESS_WITH_WARNINGS":
        return "SUCCESS_WITH_WARNINGS"
    return "SUCCESS"


def validate_m07_documentary_support_request(request_payload: dict[str, Any]) -> None:
    validator = _build_validator("m07_documentary_support_request_schema_v1.json")
    try:
        validator.validate(request_payload)
    except ValidationError as exc:
        raise M07RequestValidationError(str(exc)) from exc


def validate_m07_documentary_support_response(response_payload: dict[str, Any]) -> None:
    _precheck_response_boundary_rules(response_payload)

    validator = _build_validator("m07_documentary_support_response_schema_v1.json")
    try:
        validator.validate(response_payload)
    except ValidationError as exc:
        raise M07ResponseValidationError(str(exc)) from exc


def build_m07_documentary_support_request(
    *,
    request_id: str,
    case_id: str,
    trace_id: str,
    timestamp: str,
    goal_istruttorio: str,
    domain_target: str,
    query_text: str,
    source_priority: list[str],
    caller_module: str = "A1_OrchestratorePPAV",
    target_module: str = "B16_M07SupportLayer",
    requested_outputs: list[str] | None = None,
    reading_focus: list[str] | None = None,
    metadata_filters: dict[str, Any] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    if requested_outputs is None:
        requested_outputs = [
            "documentary_packet",
            "citation_packets",
            "vigenza_status",
            "crossref_status",
            "coverage_status",
            "m07_evidence_pack",
            "warnings",
            "errors",
            "blocks",
            "technical_trace",
        ]

    request_payload: dict[str, Any] = {
        "request_id": request_id,
        "case_id": case_id,
        "trace_id": trace_id,
        "api_version": "2.0",
        "caller_module": caller_module,
        "target_module": target_module,
        "timestamp": timestamp,
        "payload": {
            "goal_istruttorio": goal_istruttorio,
            "domain_target": domain_target,
            "query_text": query_text,
            "documentary_scope": {
                "source_priority": source_priority,
                "require_official_uri": True,
                "require_vigenza_check": True,
                "require_crossref_check": True,
                "require_coverage_check": True,
                "include_annexes": True,
            },
            "m07_context": {
                "m07_opened": True,
                "human_reading_required": True,
            },
            "requested_outputs": requested_outputs,
        },
    }

    if reading_focus:
        request_payload["payload"]["m07_context"]["reading_focus"] = reading_focus
    if notes:
        request_payload["payload"]["m07_context"]["notes"] = notes
    if metadata_filters:
        request_payload["payload"]["metadata_filters"] = metadata_filters

    validate_m07_documentary_support_request(request_payload)
    return request_payload


def consume_m07_documentary_support_response(
    response_payload: dict[str, Any],
) -> dict[str, Any]:
    validate_m07_documentary_support_response(response_payload)

    documentary_packet = response_payload["payload"]["documentary_packet"]
    warnings = copy.deepcopy(response_payload.get("warnings", []))
    errors = copy.deepcopy(response_payload.get("errors", []))
    blocks = copy.deepcopy(response_payload.get("blocks", []))
    m07_evidence_pack = copy.deepcopy(documentary_packet.get("m07_evidence_pack"))

    adapter_status = _normalize_adapter_status(
        response_status=response_payload["status"],
        blocks=blocks,
        warnings=warnings,
        errors=errors,
    )

    return {
        "request_id": response_payload["request_id"],
        "case_id": response_payload["case_id"],
        "trace_id": response_payload["trace_id"],
        "adapter_status": adapter_status,
        "response_status": response_payload["status"],
        "documentary_packet": copy.deepcopy(documentary_packet),
        "warnings": warnings,
        "errors": errors,
        "blocks": blocks,
        "requires_human_m07_completion": True,
        "decision_fields_detected": False,
        "can_close_m07": False,
        "can_authorize_output": False,
        "m07_evidence_pack_present": m07_evidence_pack is not None,
    }


def run_m07_documentary_support_exchange(
    *,
    transport: Callable[[dict[str, Any]], dict[str, Any]],
    request_payload: dict[str, Any],
) -> dict[str, Any]:
    validate_m07_documentary_support_request(request_payload)

    try:
        response_payload = transport(request_payload)
    except Exception as exc:
        raise M07TransportError(f"Errore del transport M07 documentary support: {exc}") from exc

    return consume_m07_documentary_support_response(response_payload)