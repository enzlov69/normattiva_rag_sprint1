from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple
import json


RequestEnvelope = Dict[str, Any]
ResponseEnvelope = Dict[str, Any]
BlockRecord = Dict[str, Any]


DEFAULT_REQUIRED_REQUEST_FIELDS: Tuple[str, ...] = (
    "request_id",
    "case_id",
    "trace_id",
    "api_version",
    "caller_module",
    "target_module",
    "timestamp",
    "payload",
)

DEFAULT_REQUIRED_RESPONSE_FIELDS: Tuple[str, ...] = (
    "request_id",
    "case_id",
    "trace_id",
    "api_version",
    "responder_module",
    "status",
    "payload",
    "warnings",
    "errors",
    "blocks",
    "timestamp",
)

DEFAULT_ALLOWED_RESPONSE_STATUSES = {
    "SUCCESS",
    "SUCCESS_WITH_WARNINGS",
    "DEGRADED",
    "BLOCKED",
    "REJECTED",
    "ERROR",
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

DEFAULT_FORBIDDEN_LEVEL_B_FIELDS = {
    "decision",
    "decision_status",
    "final_decision",
    "final_applicability",
    "applicability_final",
    "legal_conclusion",
    "motivazione_finale",
    "output_authorized",
    "authorization",
    "approved",
    "compliance_go",
    "compliance_passed",
    "go_final",
    "go_finale",
    "no_go_final",
    "rac_approved",
    "rac_finalized",
    "signature_ready",
}

DEFAULT_FORBIDDEN_M07_FIELDS = {
    "m07_closed",
    "m07_completed",
    "m07_certified",
    "m07_completion_certified",
    "reading_completed",
    "integral_reading_certified",
}

DEFAULT_FORBIDDEN_TOP_LEVEL_STATUSES = {
    "GO",
    "GO_WITH_SUPPORT",
    "NO_GO",
}


class FrontDoorContractError(ValueError):
    """Raised when the A↔B contract is invalid before runner execution."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json_file(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    candidate = Path(path)
    if not candidate.exists():
        return {}
    return json.loads(candidate.read_text(encoding="utf-8"))


def _required_missing_fields(data: Dict[str, Any], required_fields: Sequence[str]) -> List[str]:
    missing: List[str] = []
    for field_name in required_fields:
        if field_name not in data:
            missing.append(field_name)
        elif data[field_name] is None:
            missing.append(field_name)
    return missing


def _ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _append_unique_block(blocks: List[BlockRecord], block: BlockRecord) -> None:
    new_code = block.get("block_code")
    if any(existing.get("block_code") == new_code for existing in blocks):
        return
    blocks.append(block)


def _build_block(
    *,
    request: RequestEnvelope,
    block_code: str,
    block_reason: str,
    origin_module: str = "FrontDoorRunnerBridge",
    block_severity: str = "CRITICAL",
    block_category: str = "CONTRACT",
    affected_object_type: str = "response",
    affected_object_id: str = "level_b_response",
) -> BlockRecord:
    return {
        "block_id": f"blk_{request['request_id']}_{block_code.lower()}",
        "case_id": request["case_id"],
        "block_code": block_code,
        "block_category": block_category,
        "block_severity": block_severity,
        "origin_module": origin_module,
        "affected_object_type": affected_object_type,
        "affected_object_id": affected_object_id,
        "block_reason": block_reason,
        "block_status": "OPEN",
        "release_condition": "Manual review by Level A",
        "opened_at": _utc_now(),
        "trace_id": request["trace_id"],
        "source_layer": "B",
        "schema_version": "1.0",
    }


def _scan_forbidden_paths(node: Any, forbidden_fields: Iterable[str], prefix: str = "") -> List[str]:
    results: List[str] = []
    forbidden = set(forbidden_fields)

    if isinstance(node, dict):
        for key, value in node.items():
            current_path = f"{prefix}.{key}" if prefix else key
            if key in forbidden:
                results.append(current_path)
            results.extend(_scan_forbidden_paths(value, forbidden, current_path))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            current_path = f"{prefix}[{index}]"
            results.extend(_scan_forbidden_paths(item, forbidden, current_path))

    return results


def _sanitize_rejected_payload(rejected_paths: List[str], original_status: Any) -> Dict[str, Any]:
    return {
        "documentary_packet": None,
        "rejected_field_paths": rejected_paths,
        "original_status": original_status,
        "frontdoor_outcome": "REJECTED",
    }


@dataclass
class FinalABRunnerFrontDoor:
    """
    Front door contrattuale davanti al runner federato.

    Il front door:
    - valida la request del Livello A;
    - usa un adapter bridge già validato come base obbligatoria;
    - lascia il runner sottostante e non decisorio;
    - valida la response documentale del Livello B;
    - blocca campi vietati e sconfinamenti;
    - propaga i blocchi critici al Livello A.
    """

    adapter_bridge: Callable[[RequestEnvelope], ResponseEnvelope]
    runtime_registry_path: Optional[str] = None
    forbidden_fields_registry_path: Optional[str] = None
    required_request_fields: Sequence[str] = field(default_factory=lambda: DEFAULT_REQUIRED_REQUEST_FIELDS)
    required_response_fields: Sequence[str] = field(default_factory=lambda: DEFAULT_REQUIRED_RESPONSE_FIELDS)
    allowed_response_statuses: Sequence[str] = field(default_factory=lambda: sorted(DEFAULT_ALLOWED_RESPONSE_STATUSES))
    critical_block_codes: Sequence[str] = field(default_factory=lambda: sorted(DEFAULT_CRITICAL_BLOCK_CODES))

    def __post_init__(self) -> None:
        self.runtime_registry = _load_json_file(self.runtime_registry_path)
        self.forbidden_registry = _load_json_file(self.forbidden_fields_registry_path)

    def execute(self, request_envelope: RequestEnvelope) -> ResponseEnvelope:
        request = deepcopy(request_envelope)
        self._validate_request_envelope(request)

        raw_response = self.adapter_bridge(deepcopy(request))
        response = deepcopy(raw_response)

        self._validate_response_envelope(request, response)
        response = self._enforce_frontdoor_guards(request, response)
        response = self._propagate_critical_blocks(request, response)
        return response

    def _validate_request_envelope(self, request: RequestEnvelope) -> None:
        missing_fields = _required_missing_fields(request, self.required_request_fields)
        if missing_fields:
            raise FrontDoorContractError(
                f"Request envelope incompleto. Campi mancanti: {', '.join(missing_fields)}"
            )

        if not isinstance(request["payload"], dict):
            raise FrontDoorContractError("Il campo 'payload' deve essere un oggetto/dict.")

        for field_name in ("request_id", "case_id", "trace_id", "api_version", "caller_module", "target_module", "timestamp"):
            if not isinstance(request[field_name], str) or not request[field_name].strip():
                raise FrontDoorContractError(f"Il campo '{field_name}' deve essere una stringa non vuota.")

        allowed_callers = self.runtime_registry.get("allowed_caller_modules", [])
        if allowed_callers and request["caller_module"] not in allowed_callers:
            raise FrontDoorContractError(
                f"caller_module non autorizzato dal registry front door: {request['caller_module']}"
            )

    def _validate_response_envelope(self, request: RequestEnvelope, response: ResponseEnvelope) -> None:
        if not isinstance(response, dict):
            raise FrontDoorContractError("La response dell'adapter bridge deve essere un dict.")

        missing_fields = _required_missing_fields(response, self.required_response_fields)
        if missing_fields:
            raise FrontDoorContractError(
                f"Response envelope incompleto. Campi mancanti: {', '.join(missing_fields)}"
            )

        for echoed_field in ("request_id", "case_id", "trace_id"):
            if response[echoed_field] != request[echoed_field]:
                raise FrontDoorContractError(
                    f"Mismatch sul campo '{echoed_field}': "
                    f"request={request[echoed_field]!r}, response={response[echoed_field]!r}"
                )

        if response["status"] in DEFAULT_FORBIDDEN_TOP_LEVEL_STATUSES:
            raise FrontDoorContractError(
                f"Status vietato per Livello B/front door: {response['status']}"
            )

        if response["status"] not in set(self.allowed_response_statuses):
            raise FrontDoorContractError(
                f"Status non ammesso dal contratto front door: {response['status']}"
            )

        if not isinstance(response["payload"], dict):
            raise FrontDoorContractError("Il campo response['payload'] deve essere un dict.")

        response["warnings"] = _ensure_list(response.get("warnings"))
        response["errors"] = _ensure_list(response.get("errors"))
        response["blocks"] = _ensure_list(response.get("blocks"))

    def _enforce_frontdoor_guards(
        self,
        request: RequestEnvelope,
        response: ResponseEnvelope,
    ) -> ResponseEnvelope:
        forbidden_fields = set(DEFAULT_FORBIDDEN_LEVEL_B_FIELDS)
        forbidden_fields.update(self.forbidden_registry.get("forbidden_fields", []))

        m07_forbidden_fields = set(DEFAULT_FORBIDDEN_M07_FIELDS)
        m07_forbidden_fields.update(self.forbidden_registry.get("forbidden_m07_fields", []))

        forbidden_hits = _scan_forbidden_paths(response["payload"], forbidden_fields)
        m07_hits = _scan_forbidden_paths(response["payload"], m07_forbidden_fields)

        if forbidden_hits or m07_hits:
            rejected_paths = sorted(set(forbidden_hits + m07_hits))
            response["status"] = "REJECTED"
            response["payload"] = _sanitize_rejected_payload(rejected_paths, response.get("status"))
            response["errors"].append(
                "Front door rejection: payload del Livello B con campi vietati o semantica conclusiva."
            )
            _append_unique_block(
                response["blocks"],
                _build_block(
                    request=request,
                    block_code="RAG_SCOPE_VIOLATION",
                    block_reason=(
                        "Campi vietati o boundary M07 violato nel payload del Livello B: "
                        + ", ".join(rejected_paths)
                    ),
                    block_category="SCOPE",
                ),
            )

        return response

    def _propagate_critical_blocks(
        self,
        request: RequestEnvelope,
        response: ResponseEnvelope,
    ) -> ResponseEnvelope:
        block_codes_present = {
            block.get("block_code")
            for block in response.get("blocks", [])
            if isinstance(block, dict)
        }
        critical_present = block_codes_present.intersection(set(self.critical_block_codes))

        if critical_present and response["status"] not in {"REJECTED", "ERROR"}:
            response["status"] = "BLOCKED"
            response["warnings"].append(
                "Front door escalation: critical Level B blocks propagated to Level A."
            )

        if not response.get("blocks") and response["status"] == "BLOCKED":
            _append_unique_block(
                response["blocks"],
                _build_block(
                    request=request,
                    block_code="OUTPUT_NOT_OPPONIBILE",
                    block_reason="Status BLOCKED senza blocchi espliciti: response incoerente normalizzata dal front door.",
                    block_category="CONTRACT",
                ),
            )

        return response
