from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlsplit, urlunsplit

JsonDict = Dict[str, Any]


INCOMPLETE = "INCOMPLETE"
COMPLETE = "COMPLETE"
BLOCKS_PRESENT = "BLOCKS_PRESENT"
NO_BLOCKS = "NO_BLOCKS"


SENSITIVE_KEYS = {
    "authorization",
    "bearer",
    "token",
    "access_token",
    "api_key",
    "apikey",
    "secret",
    "password",
    "credential",
}


class LiveObservabilityError(Exception):
    """Errore tecnico nel montaggio del tracciato di osservabilità live."""


def append_live_observability(
    *,
    request_envelope: JsonDict,
    response_envelope: JsonDict,
    transport_name: str,
    transport_endpoint: Optional[str] = None,
    live_mode: bool = False,
) -> JsonDict:
    """
    Arricchisce il response envelope con evidenza tecnica del live path.

    Regole:
    - non decide;
    - non valida in senso metodologico;
    - non modifica i blocchi;
    - non rende opponibile il risultato;
    - produce solo metadati descrittivi per audit e SHADOW.
    """
    if not isinstance(request_envelope, dict):
        raise LiveObservabilityError("request_envelope must be a dict.")
    if not isinstance(response_envelope, dict):
        raise LiveObservabilityError("response_envelope must be a dict.")
    if not isinstance(transport_name, str) or not transport_name.strip():
        raise LiveObservabilityError("transport_name must be a non-empty string.")
    if transport_endpoint is not None and not isinstance(transport_endpoint, str):
        raise LiveObservabilityError("transport_endpoint must be a string when provided.")

    response = deepcopy(response_envelope)
    response.setdefault("audit", {"trail_events": []})
    response.setdefault("shadow", {"fragments": []})
    response.setdefault("payload", {})

    request_identity = _identity_snapshot(request_envelope)
    response_identity = _identity_snapshot(response)
    documentary_summary = _documentary_summary(response)
    block_propagation_state = _block_propagation_state(response)
    endpoint_redacted = _redact_endpoint(transport_endpoint)

    response["payload"]["live_observability"] = {
        "live_path_observed": bool(live_mode),
        "transport_name": transport_name,
        "transport_endpoint_redacted": endpoint_redacted,
        "request_identity": request_identity,
        "response_identity": response_identity,
        "documentary_summary": documentary_summary,
        "block_propagation_state": block_propagation_state,
        "level_b_documentary_only": bool(response.get("payload", {}).get("level_b_documentary_only", True)),
        "opponibility_status": response.get("payload", {}).get(
            "opponibility_status", "NOT_OPPONIBLE_OUTSIDE_LEVEL_A"
        ),
        "level_a_next_step": response.get("payload", {}).get(
            "level_a_next_step", "M07_LPR_GOVERNED_BY_LEVEL_A"
        ),
        "observed_at": _now_iso(),
    }

    audit = response["audit"].setdefault("trail_events", [])
    audit.append(
        {
            "event": "LIVE_PATH_OBSERVED_REQUEST_RESPONSE",
            "transport_name": transport_name,
            "transport_endpoint_redacted": endpoint_redacted,
            "live_mode": bool(live_mode),
            "request_id": request_identity.get("request_id"),
            "case_id": request_identity.get("case_id"),
            "trace_id": request_identity.get("trace_id"),
            "status": response.get("status"),
            "block_propagation_state": block_propagation_state,
            "timestamp": _now_iso(),
        }
    )

    shadow = response["shadow"].setdefault("fragments", [])
    shadow.append(
        {
            "kind": "live_observability",
            "transport_name": transport_name,
            "transport_endpoint_redacted": endpoint_redacted,
            "request_identity": request_identity,
            "response_identity": response_identity,
            "documentary_summary": documentary_summary,
            "block_propagation_state": block_propagation_state,
            "not_opponible_outside_level_a": True,
            "timestamp": _now_iso(),
        }
    )

    return response


def _identity_snapshot(envelope: JsonDict) -> JsonDict:
    required = ["request_id", "case_id", "trace_id", "timestamp"]
    present = {key: envelope.get(key) for key in required}
    completeness = COMPLETE if all(present.values()) else INCOMPLETE
    present["status"] = envelope.get("status")
    present["completeness"] = completeness
    return present


def _documentary_summary(response_envelope: JsonDict) -> JsonDict:
    payload = response_envelope.get("payload", {})
    packet = payload.get("documentary_packet", {}) if isinstance(payload, dict) else {}
    if not isinstance(packet, dict):
        packet = {}

    coverage = packet.get("coverage_assessment", {}) if isinstance(packet.get("coverage_assessment", {}), dict) else {}
    shadow_fragment = packet.get("shadow_fragment", {}) if isinstance(packet.get("shadow_fragment", {}), dict) else {}

    return {
        "sources_count": _safe_len(packet.get("sources")),
        "norm_units_count": _safe_len(packet.get("norm_units")),
        "citations_valid_count": _safe_len(packet.get("citations_valid")),
        "citations_blocked_count": _safe_len(packet.get("citations_blocked")),
        "vigenza_records_count": _safe_len(packet.get("vigenza_records")),
        "cross_reference_records_count": _safe_len(packet.get("cross_reference_records")),
        "warnings_count": _safe_len(packet.get("warnings")),
        "errors_count": _safe_len(packet.get("errors")),
        "blocks_count": _safe_len(packet.get("blocks")),
        "coverage_present": bool(coverage),
        "coverage_critical_gap_flag": bool(coverage.get("critical_gap_flag", False)),
        "shadow_fragment_present": bool(shadow_fragment),
        "documentary_only": True,
    }


def _block_propagation_state(response_envelope: JsonDict) -> str:
    payload = response_envelope.get("payload", {})
    packet = payload.get("documentary_packet", {}) if isinstance(payload, dict) else {}
    envelope_blocks = set(_as_list(response_envelope.get("blocks")))
    packet_blocks = set(_as_list(packet.get("blocks"))) if isinstance(packet, dict) else set()

    if packet_blocks:
        return BLOCKS_PRESENT if packet_blocks.issubset(envelope_blocks) else INCOMPLETE
    return NO_BLOCKS


def _redact_endpoint(endpoint: Optional[str]) -> Optional[str]:
    if endpoint is None:
        return None
    value = endpoint.strip()
    if not value:
        return None

    parts = urlsplit(value)
    if parts.scheme or parts.netloc:
        netloc = parts.hostname or ""
        if parts.port:
            netloc = f"{netloc}:{parts.port}"

        redacted_query = ""
        if parts.query:
            redacted_query = "[REDACTED]"

        sanitized = urlunsplit((parts.scheme, netloc, parts.path, redacted_query, ""))
        if not sanitized:
            return "[REDACTED]"
        return sanitized

    lower_value = value.lower()
    if any(key in lower_value for key in SENSITIVE_KEYS):
        return "[REDACTED]"
    return value


def _safe_len(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _as_list(value: Any) -> List[str]:
    return list(value) if isinstance(value, list) else []


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
