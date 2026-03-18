"""Servizio di handoff runtime A→B→runner→B→A.

Il servizio valida la request contrattuale finale A/B, la traduce nel formato
minimo atteso dal runner, invoca il runner come black-box e restituisce una
ABResponseEnvelope conforme, composta esclusivamente da output tecnici e
strumentali del Livello B.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from runtime.final_ab_runner_invocation_port import RunnerInvocationError, RunnerInvocationPort
from runtime.final_ab_runner_response_mapper import map_runner_response_to_documentary_packet

REQUIRED_REQUEST_FIELDS: Sequence[str] = (
    "request_id",
    "case_id",
    "trace_id",
    "api_version",
    "caller_module",
    "target_module",
    "timestamp",
    "payload",
)

DEFAULT_REQUEST_MAP: Dict[str, Any] = {
    "schema_version": "v1",
    "map_name": "final_ab_runner_request_map_v1",
    "required_envelope_fields": list(REQUIRED_REQUEST_FIELDS),
    "runner_request_fields": {
        "request_id": "request_id",
        "case_id": "case_id",
        "trace_id": "trace_id",
        "query_text": [
            "payload.query_text",
            "payload.query",
            "payload.document_request.query_text",
        ],
        "domain_target": [
            "payload.domain_target",
            "payload.domain",
            "payload.document_request.domain_target",
        ],
        "metadata_filters": [
            "payload.metadata_filters",
            "payload.filters",
        ],
        "top_k": [
            "payload.top_k",
            "payload.limit",
        ],
        "runtime_flags": [
            "payload.runtime_flags",
            "payload.flags",
        ],
    },
}

DEFAULT_CAPABILITY_REGISTRY: Dict[str, Any] = {
    "schema_version": "v1",
    "registry_name": "final_ab_runner_capability_registry_v1",
    "target_modules": ["level_b_runtime_handoff", "level_b_documentary_runtime"],
    "critical_block_codes": [
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
    ],
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _get_by_path(data: Mapping[str, Any], path: str) -> Any:
    current: Any = data
    for chunk in path.split("."):
        if not isinstance(current, Mapping) or chunk not in current:
            return None
        current = current[chunk]
    return current


def _pick_first(data: Mapping[str, Any], candidates: Sequence[str]) -> Any:
    for candidate in candidates:
        value = _get_by_path(data, candidate)
        if value is not None:
            return value
    return None


class FinalABRuntimeHandoffService:
    """Servizio coordinatore del controlled handoff runtime."""

    def __init__(
        self,
        *,
        invocation_port: RunnerInvocationPort,
        request_map: Optional[Mapping[str, Any]] = None,
        capability_registry: Optional[Mapping[str, Any]] = None,
        responder_module: str = "level_b_runtime_handoff",
    ) -> None:
        self.invocation_port = invocation_port
        self.request_map = deepcopy(dict(request_map or DEFAULT_REQUEST_MAP))
        self.capability_registry = deepcopy(dict(capability_registry or DEFAULT_CAPABILITY_REGISTRY))
        self.responder_module = responder_module

    def _validation_errors(self, envelope: Mapping[str, Any]) -> List[str]:
        missing = [field_name for field_name in REQUIRED_REQUEST_FIELDS if field_name not in envelope]
        payload = envelope.get("payload")
        if payload is not None and not isinstance(payload, Mapping):
            missing.append("payload<invalid_type>")
        return missing

    def _build_rejected_response(
        self,
        *,
        envelope: Mapping[str, Any],
        errors: Sequence[Dict[str, Any]],
        blocks: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "request_id": envelope.get("request_id", "unknown_request"),
            "case_id": envelope.get("case_id", "unknown_case"),
            "trace_id": envelope.get("trace_id", "unknown_trace"),
            "api_version": envelope.get("api_version", "v1"),
            "responder_module": self.responder_module,
            "status": "REJECTED",
            "payload": {
                "sources": [],
                "norm_units": [],
                "citations_valid": [],
                "citations_blocked": [],
                "vigenza_records": [],
                "cross_reference_records": [],
                "coverage_assessment": {},
                "warnings": [
                    {
                        "code": "REQUEST_REJECTED",
                        "message": "La request contrattuale non è conforme ai requisiti minimi.",
                    }
                ],
                "errors": list(errors),
                "blocks": list(blocks),
                "shadow_fragment": {
                    "source_layer": "B",
                    "schema_version": "v1",
                    "record_version": "1",
                    "case_id": envelope.get("case_id", "unknown_case"),
                    "trace_id": envelope.get("trace_id", "unknown_trace"),
                    "created_at": _utc_now_iso(),
                    "updated_at": _utc_now_iso(),
                    "mapping_version": self.request_map.get("map_name", "final_ab_runner_request_map_v1"),
                },
            },
            "warnings": [
                {
                    "code": "REQUEST_REJECTED",
                    "message": "La request è stata rigettata dal layer di handoff controllato.",
                }
            ],
            "errors": list(errors),
            "blocks": list(blocks),
            "timestamp": _utc_now_iso(),
        }

    def _build_error_response(
        self,
        *,
        envelope: Mapping[str, Any],
        error_message: str,
    ) -> Dict[str, Any]:
        errors = [{"code": "RUNNER_INVOCATION_ERROR", "message": error_message}]
        return {
            "request_id": envelope.get("request_id", "unknown_request"),
            "case_id": envelope.get("case_id", "unknown_case"),
            "trace_id": envelope.get("trace_id", "unknown_trace"),
            "api_version": envelope.get("api_version", "v1"),
            "responder_module": self.responder_module,
            "status": "ERROR",
            "payload": {
                "sources": [],
                "norm_units": [],
                "citations_valid": [],
                "citations_blocked": [],
                "vigenza_records": [],
                "cross_reference_records": [],
                "coverage_assessment": {},
                "warnings": [],
                "errors": errors,
                "blocks": [],
                "shadow_fragment": {
                    "source_layer": "B",
                    "schema_version": "v1",
                    "record_version": "1",
                    "case_id": envelope.get("case_id", "unknown_case"),
                    "trace_id": envelope.get("trace_id", "unknown_trace"),
                    "created_at": _utc_now_iso(),
                    "updated_at": _utc_now_iso(),
                    "mapping_version": self.request_map.get("map_name", "final_ab_runner_request_map_v1"),
                },
            },
            "warnings": [],
            "errors": errors,
            "blocks": [],
            "timestamp": _utc_now_iso(),
        }

    def _build_runner_request(self, envelope: Mapping[str, Any]) -> Dict[str, Any]:
        field_map = self.request_map.get("runner_request_fields", {})
        runner_request: Dict[str, Any] = {}
        for runner_field, source in field_map.items():
            if isinstance(source, str):
                runner_request[runner_field] = _get_by_path(envelope, source)
            elif isinstance(source, Sequence):
                runner_request[runner_field] = _pick_first(envelope, source)
            else:
                runner_request[runner_field] = None

        runtime_flags = runner_request.get("runtime_flags")
        if not isinstance(runtime_flags, Mapping):
            runtime_flags = {}
            runner_request["runtime_flags"] = runtime_flags
        runtime_flags.setdefault("black_box_runner", True)
        runtime_flags.setdefault("level_b_only", True)
        return runner_request

    def handle(self, envelope: Mapping[str, Any]) -> Dict[str, Any]:
        validation_failures = self._validation_errors(envelope)
        if validation_failures:
            errors = [
                {
                    "code": "INVALID_AB_REQUEST",
                    "message": f"Missing or invalid request fields: {', '.join(validation_failures)}",
                }
            ]
            blocks = [
                {
                    "code": "AUDIT_INCOMPLETE",
                    "block_code": "AUDIT_INCOMPLETE",
                    "block_category": "CONTRACT",
                    "block_severity": "CRITICAL",
                    "message": "ABRequestEnvelope incompleta o non valida.",
                    "block_reason": "ABRequestEnvelope incompleta o non valida.",
                    "block_status": "OPEN",
                }
            ]
            return self._build_rejected_response(envelope=envelope, errors=errors, blocks=blocks)

        allowed_targets = set(self.capability_registry.get("target_modules", []))
        if allowed_targets and envelope.get("target_module") not in allowed_targets:
            errors = [
                {
                    "code": "TARGET_MODULE_MISMATCH",
                    "message": "Il target_module richiesto non è ammesso dal runtime handoff.",
                }
            ]
            blocks = [
                {
                    "code": "RAG_SCOPE_VIOLATION",
                    "block_code": "RAG_SCOPE_VIOLATION",
                    "block_category": "BOUNDARY",
                    "block_severity": "CRITICAL",
                    "message": "Target module non ammesso per il collegamento runtime finale.",
                    "block_reason": "Target module non ammesso per il collegamento runtime finale.",
                    "block_status": "OPEN",
                }
            ]
            return self._build_rejected_response(envelope=envelope, errors=errors, blocks=blocks)

        runner_request = self._build_runner_request(envelope)

        try:
            raw_response = self.invocation_port.invoke(runner_request)
        except RunnerInvocationError as exc:
            return self._build_error_response(envelope=envelope, error_message=str(exc))

        mapping = map_runner_response_to_documentary_packet(
            raw_response=raw_response,
            case_id=str(envelope["case_id"]),
            trace_id=str(envelope["trace_id"]),
            runner_entrypoint=getattr(self.invocation_port, "entrypoint_label", "runner_black_box"),
            mapping_version=str(self.request_map.get("map_name", "final_ab_runner_response_map_v1")),
        )

        return {
            "request_id": envelope["request_id"],
            "case_id": envelope["case_id"],
            "trace_id": envelope["trace_id"],
            "api_version": envelope["api_version"],
            "responder_module": self.responder_module,
            "status": mapping["status"],
            "payload": mapping["documentary_packet"],
            "warnings": mapping["warnings"],
            "errors": mapping["errors"],
            "blocks": mapping["blocks"],
            "timestamp": _utc_now_iso(),
        }
