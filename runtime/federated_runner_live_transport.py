from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
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
                with effective_opener(http_request, timeout=settings.timeout_seconds) as response:
                    raw = response.read().decode("utf-8")
                return _parse_json_response(raw)
            except error.HTTPError as exc:
                last_error = exc
                if exc.code in settings.retryable_http_statuses and attempt < settings.max_attempts:
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

    if not isinstance(parsed, dict):
        raise FederatedRunnerLiveTransportContractError(
            "Federated runner response must be a JSON object."
        )
    return parsed


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
    except (FederatedRunnerLiveTransportError, FederatedRunnerLiveTransportContractError, RuntimeError, ValueError) as exc:
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
    payload["documentary_evidence_matrix"] = matrix

    audit = response_envelope.setdefault("audit", {})
    trail_events = audit.setdefault("trail_events", [])
    trail_events.append(
        {
            "event": "documentary_evidence_matrix_built",
            "coverage_status": matrix["coverage"]["status"],
            "vigenza_status": matrix["vigenza"]["status"],
            "rinvii_status": matrix["rinvii"]["status"],
        }
    )

    shadow = response_envelope.setdefault("shadow", {})
    fragments = shadow.setdefault("fragments", [])
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
    vigenza_status = str(packet.get("vigenza_status", "UNKNOWN") or "UNKNOWN")
    rinvii_status = str(packet.get("rinvii_status", "UNKNOWN") or "UNKNOWN")
    coverage_raw = str(packet.get("coverage", "UNKNOWN") or "UNKNOWN")

    blocking_reasons: list[str] = []

    coverage_status = coverage_raw.upper()
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
