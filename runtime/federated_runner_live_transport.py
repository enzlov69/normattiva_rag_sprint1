from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Optional
from urllib import error, request

JsonDict = Dict[str, Any]
TransportCallable = Callable[[JsonDict], JsonDict]
SleepCallable = Callable[[float], None]
OpenCallable = Callable[..., Any]

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_RETRYABLE_HTTP_STATUSES = (429, 502, 503, 504)
DEFAULT_BACKOFF_SECONDS = 0.5

FALLBACK_BLOCKS = (
    "CRITICAL_DOCUMENTARY_BLOCK",
    "LIVE_TRANSPORT_ERROR",
    "OUTPUT_NOT_OPPONIBLE",
)

REQUIRED_DOCUMENTARY_PACKET_KEYS = (
    "sources",
    "normative_units",
    "citations",
    "incomplete_citations",
    "vigenza_status",
    "rinvii_status",
    "coverage",
)

FORBIDDEN_LEVEL_B_FIELDS = {
    "final_decision",
    "go_no_go",
    "firma_ready",
    "output_authorized",
    "final_opposability",
    "m07_closed",
    "m07_completed",
    "m07_approved",
    "rac_final_outcome",
    "layer_atto_firma_ready",
}


class FederatedRunnerLiveTransportError(RuntimeError):
    """Errore tecnico sul percorso live del runner federato."""


class FederatedRunnerLiveTransportContractError(FederatedRunnerLiveTransportError):
    """Response ricevuta ma non conforme al minimo contrattuale."""


@dataclass(frozen=True)
class LiveTransportSettings:
    endpoint: str
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS
    retryable_http_statuses: tuple[int, ...] = DEFAULT_RETRYABLE_HTTP_STATUSES
    bearer_token: Optional[str] = None


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    value = int(raw)
    if value < 1:
        raise ValueError(f"{name} must be >= 1")
    return value


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    value = float(raw)
    if value < 0:
        raise ValueError(f"{name} must be >= 0")
    return value


def _env_http_statuses(name: str, default: Iterable[int]) -> tuple[int, ...]:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return tuple(default)
    parsed: list[int] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        parsed.append(int(token))
    if not parsed:
        return tuple(default)
    return tuple(parsed)


def load_live_transport_settings() -> LiveTransportSettings:
    endpoint = os.getenv("FEDERATED_RUNNER_LIVE_ENDPOINT")
    if not endpoint:
        raise FederatedRunnerLiveTransportError(
            "Missing environment variable FEDERATED_RUNNER_LIVE_ENDPOINT."
        )

    return LiveTransportSettings(
        endpoint=endpoint,
        timeout_seconds=_env_int(
            "FEDERATED_RUNNER_LIVE_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS
        ),
        max_attempts=_env_int(
            "FEDERATED_RUNNER_LIVE_MAX_ATTEMPTS", DEFAULT_MAX_ATTEMPTS
        ),
        backoff_seconds=_env_float(
            "FEDERATED_RUNNER_LIVE_BACKOFF_SECONDS", DEFAULT_BACKOFF_SECONDS
        ),
        retryable_http_statuses=_env_http_statuses(
            "FEDERATED_RUNNER_LIVE_RETRYABLE_HTTP_STATUSES",
            DEFAULT_RETRYABLE_HTTP_STATUSES,
        ),
        bearer_token=os.getenv("FEDERATED_RUNNER_LIVE_BEARER_TOKEN") or None,
    )


def _default_opener(http_request: request.Request, timeout: int) -> Any:
    return request.urlopen(http_request, timeout=timeout)


def build_transport(
    opener: Optional[OpenCallable] = None,
    sleep_fn: Optional[SleepCallable] = None,
) -> TransportCallable:
    settings = load_live_transport_settings()
    effective_opener = opener or _default_opener
    effective_sleep = sleep_fn or time.sleep

    def _transport(envelope: JsonDict) -> JsonDict:
        _validate_request_envelope(envelope)
        body = json.dumps(envelope).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if settings.bearer_token:
            headers["Authorization"] = f"Bearer {settings.bearer_token}"

        last_error: Optional[BaseException] = None

        for attempt in range(1, settings.max_attempts + 1):
            http_request = request.Request(
                url=settings.endpoint,
                data=body,
                headers=headers,
                method="POST",
            )
            try:
                with effective_opener(
                    http_request, timeout=settings.timeout_seconds
                ) as response:
                    raw = response.read().decode("utf-8")

                return _parse_json_response(raw)

            except error.HTTPError as exc:
                last_error = exc
                if (
                    exc.code in settings.retryable_http_statuses
                    and attempt < settings.max_attempts
                ):
                    effective_sleep(settings.backoff_seconds * attempt)
                    continue
                detail = _safe_http_error_body(exc)
                raise FederatedRunnerLiveTransportError(
                    f"HTTP error from federated runner: {exc.code} {detail}"
                ) from exc

            except error.URLError as exc:
                last_error = exc
                if attempt < settings.max_attempts:
                    effective_sleep(settings.backoff_seconds * attempt)
                    continue
                raise FederatedRunnerLiveTransportError(
                    f"Connection error to federated runner: {exc}"
                ) from exc

            except TimeoutError as exc:
                last_error = exc
                if attempt < settings.max_attempts:
                    effective_sleep(settings.backoff_seconds * attempt)
                    continue
                raise FederatedRunnerLiveTransportError(
                    f"Timeout error to federated runner: {exc}"
                ) from exc

        raise FederatedRunnerLiveTransportError(
            f"Unexpected live transport exhaustion without response. last_error={last_error!r}"
        )

    return _transport


def _validate_request_envelope(envelope: JsonDict) -> None:
    if not isinstance(envelope, dict):
        raise FederatedRunnerLiveTransportError(
            "Transport input must be a dict request envelope."
        )
    for required_key in ("request_id", "case_id", "trace_id"):
        if not envelope.get(required_key):
            raise FederatedRunnerLiveTransportError(
                f"Missing required request envelope field: {required_key}"
            )


def _parse_json_response(raw: str) -> JsonDict:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FederatedRunnerLiveTransportContractError(
            "Federated runner response is not valid JSON."
        ) from exc

    _maybe_dump_raw_response(parsed)

    if not isinstance(parsed, dict):
        raise FederatedRunnerLiveTransportContractError(
            "Federated runner response must be a JSON object."
        )

    return _normalize_live_response_envelope(parsed)


def _maybe_dump_raw_response(parsed: Any) -> None:
    debug_path = os.getenv("FEDERATED_RUNNER_LIVE_DEBUG_PATH")
    if not debug_path:
        return

    try:
        path = Path(debug_path)
        path.write_text(
            json.dumps(parsed, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        # debug opzionale: non deve mai rompere il transport
        pass


def _normalize_live_response_envelope(parsed: Mapping[str, Any]) -> JsonDict:
    """
    Normalizza in modo minimale la response del Livello B senza attribuire
    funzioni decisorie o validative al runner federato.

    Obiettivi:
    - colmare i campi top-level minimi richiesti dal Livello A;
    - supportare wrapper comuni (response/data/result);
    - supportare alias documentali legacy;
    - preservare la natura documentale e non opponibile del ritorno B.
    """
    candidate = _unwrap_common_response_container(parsed)

    envelope: JsonDict = dict(candidate)

    payload = envelope.get("payload")
    if not isinstance(payload, Mapping):
        payload = {}

    documentary_packet = _extract_and_normalize_documentary_packet(
        candidate=candidate,
        payload=payload,
    )

    normalized_payload: JsonDict = dict(payload)
    normalized_payload["documentary_packet"] = documentary_packet

    envelope["api_version"] = str(envelope.get("api_version") or "1.0")
    envelope["responder_module"] = str(
        envelope.get("responder_module") or "B_REAL_FEDERATED_RUNNER"
    )
    envelope["timestamp"] = str(envelope.get("timestamp") or _utc_now_iso())
    envelope["status"] = str(envelope.get("status") or "COMPLETED")
    envelope["warnings"] = _coerce_list(envelope.get("warnings"))
    envelope["errors"] = _coerce_list(envelope.get("errors"))
    envelope["blocks"] = _coerce_list(envelope.get("blocks"))
    envelope["payload"] = normalized_payload

    audit = envelope.get("audit")
    if not isinstance(audit, Mapping):
        audit = {}
    audit_dict: JsonDict = dict(audit)
    audit_dict["trail_events"] = _coerce_list(audit_dict.get("trail_events"))
    envelope["audit"] = audit_dict

    shadow = envelope.get("shadow")
    if not isinstance(shadow, Mapping):
        shadow = {}
    shadow_dict: JsonDict = dict(shadow)
    shadow_dict["fragments"] = _coerce_list(shadow_dict.get("fragments"))
    shadow_dict["fragments"].append(
        {
            "kind": "live_response_normalization",
            "normalized_top_level_fields": [
                "api_version",
                "responder_module",
                "timestamp",
                "status",
                "warnings",
                "errors",
                "blocks",
            ],
            "documentary_only": True,
            "timestamp": envelope["timestamp"],
        }
    )
    envelope["shadow"] = shadow_dict

    return envelope


def _unwrap_common_response_container(parsed: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("response", "data", "result"):
        value = parsed.get(key)
        if isinstance(value, Mapping):
            return value
    return parsed


def _extract_and_normalize_documentary_packet(
    *,
    candidate: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> JsonDict:
    raw_packet = payload.get("documentary_packet")
    if not isinstance(raw_packet, Mapping):
        raw_packet = {}

    if not raw_packet:
        # supporto a payload documentale già "piatto"
        if _looks_like_documentary_packet(payload):
            raw_packet = payload
        elif _looks_like_documentary_packet(candidate):
            raw_packet = candidate

    packet = dict(raw_packet)

    normative_units = (
        packet.get("normative_units")
        or packet.get("norm_units")
        or packet.get("norm_units_relevant")
        or []
    )
    citations = (
        packet.get("citations")
        or packet.get("citations_valid")
        or packet.get("valid_citations")
        or []
    )
    incomplete_citations = (
        packet.get("incomplete_citations")
        or packet.get("citations_blocked")
        or packet.get("blocked_citations")
        or []
    )

    coverage = packet.get("coverage")
    if coverage in (None, ""):
        coverage = _extract_coverage_alias(packet)

    vigenza_status = packet.get("vigenza_status")
    if vigenza_status in (None, ""):
        vigenza_status = _extract_vigenza_alias(packet)

    rinvii_status = packet.get("rinvii_status")
    if rinvii_status in (None, ""):
        rinvii_status = _extract_rinvii_alias(packet)

    normalized_packet: JsonDict = {
        "sources": _coerce_list(packet.get("sources")),
        "normative_units": _coerce_list(normative_units),
        "citations": _coerce_list(citations),
        "incomplete_citations": _coerce_list(incomplete_citations),
        "vigenza_status": _preserve_documentary_status_value(vigenza_status),
        "rinvii_status": _preserve_documentary_status_value(rinvii_status),
        "coverage": _preserve_documentary_status_value(coverage),
    }

    # preserva eventuali metadati aggiuntivi utili al Livello A
    for extra_key in (
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
    ):
        if extra_key in packet and extra_key not in normalized_packet:
            normalized_packet[extra_key] = packet[extra_key]

    return normalized_packet


def _looks_like_documentary_packet(node: Mapping[str, Any]) -> bool:
    documentary_markers = {
        "sources",
        "normative_units",
        "norm_units",
        "citations",
        "citations_valid",
        "citations_blocked",
        "incomplete_citations",
        "vigenza_status",
        "vigenza_records",
        "rinvii_status",
        "cross_reference_records",
        "coverage",
        "coverage_assessment",
    }
    return any(key in node for key in documentary_markers)


def _extract_coverage_alias(packet: Mapping[str, Any]) -> str:
    coverage_assessment = packet.get("coverage_assessment")
    if isinstance(coverage_assessment, Mapping):
        if coverage_assessment.get("coverage_status"):
            return str(coverage_assessment["coverage_status"])
    return "UNKNOWN"


def _extract_vigenza_alias(packet: Mapping[str, Any]) -> str:
    value = packet.get("vigenza_records")
    if isinstance(value, Mapping) and value.get("status"):
        return str(value["status"])
    return "UNKNOWN"


def _extract_rinvii_alias(packet: Mapping[str, Any]) -> str:
    value = packet.get("cross_reference_records")
    if isinstance(value, Mapping) and value.get("status"):
        return str(value["status"])
    return "UNKNOWN"


def _preserve_documentary_status_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return dict(value)
    if value in (None, ""):
        return "UNKNOWN"
    return str(value)


def _coerce_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _safe_http_error_body(exc: error.HTTPError) -> str:
    try:
        return exc.read().decode("utf-8")
    except Exception:
        return str(exc)


def invoke_transport_with_guarded_fallback(
    request_envelope: JsonDict,
    *,
    transport: Optional[TransportCallable] = None,
    transport_name: str = "federated_runner_live_transport",
    transport_endpoint: Optional[str] = None,
    live_mode: bool = True,
) -> JsonDict:
    effective_transport = transport or build_transport()

    try:
        response_envelope = effective_transport(request_envelope)
        _assert_no_forbidden_level_b_fields(response_envelope)
        return append_documentary_evidence_matrix(response_envelope)
    except (
        FederatedRunnerLiveTransportError,
        FederatedRunnerLiveTransportContractError,
        RuntimeError,
        ValueError,
    ) as exc:
        fallback = _build_blocked_fallback_envelope(
            request_envelope=request_envelope,
            reason=str(exc),
            transport_name=transport_name,
            transport_endpoint=transport_endpoint,
            live_mode=live_mode,
        )
        return append_documentary_evidence_matrix(fallback)


def _assert_no_forbidden_level_b_fields(response_envelope: Mapping[str, Any]) -> None:
    flattened_keys = _collect_nested_keys(response_envelope)
    illegal = sorted(FORBIDDEN_LEVEL_B_FIELDS.intersection(flattened_keys))
    if illegal:
        raise FederatedRunnerLiveTransportContractError(
            f"Forbidden Level B fields detected in live response: {', '.join(illegal)}"
        )


def _collect_nested_keys(node: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(node, Mapping):
        for key, value in node.items():
            found.add(str(key))
            found.update(_collect_nested_keys(value))
    elif isinstance(node, list):
        for item in node:
            found.update(_collect_nested_keys(item))
    return found


def _build_blocked_fallback_envelope(
    *,
    request_envelope: Mapping[str, Any],
    reason: str,
    transport_name: str,
    transport_endpoint: Optional[str],
    live_mode: bool,
) -> JsonDict:
    request_id = request_envelope.get("request_id")
    case_id = request_envelope.get("case_id")
    trace_id = request_envelope.get("trace_id")

    return {
        "request_id": request_id,
        "case_id": case_id,
        "trace_id": trace_id,
        "status": "BLOCKED",
        "warnings": ["LIVE_PATH_DEGRADED_TO_FALLBACK"],
        "errors": [reason],
        "blocks": list(FALLBACK_BLOCKS),
        "payload": {
            "documentary_packet": {
                "sources": [],
                "normative_units": [],
                "citations": [],
                "incomplete_citations": [],
                "vigenza_status": "UNKNOWN",
                "rinvii_status": "UNKNOWN",
                "coverage": "INADEQUATE",
                "warnings": ["DOCUMENTARY_PACKET_UNAVAILABLE_FROM_LIVE_TRANSPORT"],
                "errors": [reason],
                "blocks": list(FALLBACK_BLOCKS),
            },
            "live_transport": {
                "transport_name": transport_name,
                "transport_endpoint_redacted": redact_endpoint(transport_endpoint),
                "live_mode": bool(live_mode),
                "fallback_triggered": True,
            },
            "non_opponibility": {
                "outside_level_a": True,
                "reason": "LIVE_TRANSPORT_FAILURE_BLOCKED",
            },
        },
        "audit": {
            "trail_events": [
                {
                    "event": "live_transport_fallback_triggered",
                    "severity": "error",
                    "reason": reason,
                }
            ]
        },
        "shadow": {
            "fragments": [
                {
                    "kind": "live_transport_fallback",
                    "reason": reason,
                    "transport_name": transport_name,
                }
            ]
        },
    }


def append_documentary_evidence_matrix(response_envelope: JsonDict) -> JsonDict:
    packet = _get_documentary_packet(response_envelope)
    matrix = build_documentary_evidence_matrix(packet)

    payload = response_envelope.setdefault("payload", {})
    if not isinstance(payload, dict):
        payload = {}
        response_envelope["payload"] = payload

    payload["documentary_evidence_matrix"] = matrix

    audit = response_envelope.setdefault("audit", {})
    if not isinstance(audit, dict):
        audit = {}
        response_envelope["audit"] = audit

    trail_events = audit.setdefault("trail_events", [])
    if not isinstance(trail_events, list):
        trail_events = []
        audit["trail_events"] = trail_events

    trail_events.append(
        {
            "event": "documentary_evidence_matrix_built",
            "coverage_status": matrix["coverage"]["status"],
            "vigenza_status": matrix["vigenza"]["status"],
            "rinvii_status": matrix["rinvii"]["status"],
        }
    )

    shadow = response_envelope.setdefault("shadow", {})
    if not isinstance(shadow, dict):
        shadow = {}
        response_envelope["shadow"] = shadow

    fragments = shadow.setdefault("fragments", [])
    if not isinstance(fragments, list):
        fragments = []
        shadow["fragments"] = fragments

    fragments.append(
        {
            "kind": "documentary_evidence_matrix",
            "blocking_reasons": matrix["blocking_reasons"],
        }
    )

    payload.setdefault(
        "non_opponibility",
        {
            "outside_level_a": True,
            "reason": "DOCUMENTARY_OUTPUT_REQUIRES_LEVEL_A_GOVERNANCE",
        },
    )
    return response_envelope


def build_documentary_evidence_matrix(packet: Mapping[str, Any]) -> JsonDict:
    sources = _as_list(packet.get("sources"))
    normative_units = _as_list(packet.get("normative_units"))
    citations = _as_list(packet.get("citations"))
    incomplete_citations = _as_list(packet.get("incomplete_citations"))
    vigenza_status = _extract_documentary_status(packet.get("vigenza_status"))
    rinvii_status = _extract_documentary_status(packet.get("rinvii_status"))
    coverage_status = _extract_documentary_status(packet.get("coverage"))

    blocking_reasons: list[str] = []

    if coverage_status in {"INADEQUATE", "UNKNOWN"}:
        blocking_reasons.append("COVERAGE_NOT_ADEQUATE")
    if vigenza_status.upper() in {"UNKNOWN", "UNCERTAIN", "BLOCKED"}:
        blocking_reasons.append("VIGENZA_NOT_CONFIRMED")
    if rinvii_status.upper() in {"UNKNOWN", "UNRESOLVED", "BLOCKED"}:
        blocking_reasons.append("RINVII_NOT_RESOLVED")
    if incomplete_citations:
        blocking_reasons.append("INCOMPLETE_CITATIONS_PRESENT")

    missing_keys = [key for key in REQUIRED_DOCUMENTARY_PACKET_KEYS if key not in packet]
    if missing_keys:
        blocking_reasons.append("DOCUMENTARY_PACKET_KEYS_MISSING")

    return {
        "sources_count": len(sources),
        "normative_units_count": len(normative_units),
        "citations_count": len(citations),
        "incomplete_citations_count": len(incomplete_citations),
        "coverage": {
            "status": coverage_status,
            "adequate": coverage_status == "ADEQUATE",
        },
        "vigenza": {
            "status": vigenza_status.upper(),
            "confirmed": vigenza_status.upper() == "CONFIRMED",
        },
        "rinvii": {
            "status": rinvii_status.upper(),
            "resolved": rinvii_status.upper() == "RESOLVED",
        },
        "blocking_reasons": blocking_reasons,
        "documentary_only": True,
        "non_opponible_outside_level_a": True,
    }


def _extract_documentary_status(value: Any) -> str:
    if isinstance(value, Mapping):
        nested_status = value.get("status")
        if nested_status not in (None, ""):
            return str(nested_status).upper()
        return "UNKNOWN"
    return str(value or "UNKNOWN").upper()


def _get_documentary_packet(response_envelope: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = response_envelope.get("payload")
    if isinstance(payload, Mapping):
        packet = payload.get("documentary_packet")
        if isinstance(packet, Mapping):
            return packet
    return {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def redact_endpoint(endpoint: Optional[str]) -> Optional[str]:
    if not endpoint:
        return None

    try:
        from urllib.parse import urlsplit, urlunsplit

        parts = urlsplit(endpoint)
        if not parts.scheme or not parts.netloc:
            return "***"
        return urlunsplit((parts.scheme, parts.netloc, parts.path or "", "", ""))
    except Exception:
        return "***"
