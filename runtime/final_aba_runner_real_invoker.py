from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

JsonDict = Dict[str, Any]
TransportCallable = Callable[[JsonDict], JsonDict]


DEFAULT_FORBIDDEN_LEVEL_B_FIELDS: Set[str] = {
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
    # allineamento ulteriore con baseline v2
    "final_applicability",
    "legal_conclusion",
    "motivazione_finale",
    "ppav_closed",
    "go_finale",
    "decision_status",
    "applicability_final",
    "authorization",
    "approved",
    "compliance_go",
    "rac_approved",
    "signature_ready",
}

REQUIRED_REQUEST_FIELDS: Tuple[str, ...] = (
    "request_id",
    "case_id",
    "trace_id",
    "api_version",
    "caller_module",
    "target_module",
    "timestamp",
    "status",
    "warnings",
    "errors",
    "blocks",
    "payload",
)

REQUIRED_RESPONSE_FIELDS: Tuple[str, ...] = (
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

REQUIRED_DOCUMENTARY_PACKET_FIELDS: Tuple[str, ...] = (
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

REQUEST_DEFAULT_STATUS = "READY_FOR_LEVEL_B"
ERROR_STATUS = "ERROR"
REJECTED_STATUS = "REJECTED"
BLOCKED_STATUS = "BLOCKED"
SUCCESS_STATUS = "SUCCESS"
SUCCESS_WITH_WARNINGS_STATUS = "SUCCESS_WITH_WARNINGS"
DEGRADED_STATUS = "DEGRADED"


class RealInvokerValidationError(Exception):
    """Eccezione interna per errori contrattuali o di perimetro."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        blocks: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.blocks = blocks or []
        self.errors = errors or [code]


@dataclass(slots=True)
class FederatedRunnerRealInvoker:
    """
    Adapter contrattuale A→B→A per il collegamento al runner federato reale.

    Il modulo:
    - normalizza la request;
    - valida il contratto minimo in uscita;
    - chiama un transport reale iniettato;
    - valida la response del Livello B;
    - intercetta campi vietati e tentativi di chiusura M07;
    - restituisce solo envelope documentali, tracciabili e bloccabili.
    """

    transport: TransportCallable
    api_version: str = "1.0"
    responder_module: str = "B_REAL_FEDERATED_RUNNER"
    forbidden_level_b_fields: Set[str] = field(
        default_factory=lambda: set(DEFAULT_FORBIDDEN_LEVEL_B_FIELDS)
    )

    def invoke(self, request_envelope: JsonDict) -> JsonDict:
        normalized_request = self.normalize_request_envelope(request_envelope)

        try:
            self.validate_request_envelope(normalized_request)
        except RealInvokerValidationError as exc:
            return self._build_error_response_from_request(
                request=normalized_request,
                status=REJECTED_STATUS,
                message=str(exc),
                error_code=exc.code,
                blocks=exc.blocks,
                extra_errors=exc.errors,
            )

        try:
            raw_response = self.transport(deepcopy(normalized_request))
        except Exception as exc:  # pragma: no cover - protezione runtime generale
            return self._build_error_response_from_request(
                request=normalized_request,
                status=ERROR_STATUS,
                message=f"Federated runner transport failure: {exc}",
                error_code="FEDERATED_RUNNER_TRANSPORT_ERROR",
                blocks=["CORPUS_MISSING"],
                extra_errors=["FEDERATED_RUNNER_TRANSPORT_ERROR"],
            )

        try:
            return self.validate_response_envelope(raw_response, normalized_request)
        except RealInvokerValidationError as exc:
            return self._build_error_response_from_request(
                request=normalized_request,
                status=REJECTED_STATUS,
                message=str(exc),
                error_code=exc.code,
                blocks=exc.blocks,
                extra_errors=exc.errors,
            )

    def normalize_request_envelope(self, request_envelope: JsonDict) -> JsonDict:
        normalized = deepcopy(request_envelope)
        normalized.setdefault("api_version", self.api_version)
        normalized.setdefault("status", REQUEST_DEFAULT_STATUS)
        normalized.setdefault("warnings", [])
        normalized.setdefault("errors", [])
        normalized.setdefault("blocks", [])
        normalized.setdefault("payload", {})
        return normalized

    def validate_request_envelope(self, request_envelope: JsonDict) -> None:
        missing = [field for field in REQUIRED_REQUEST_FIELDS if field not in request_envelope]
        if missing:
            raise RealInvokerValidationError(
                f"Missing required request fields: {', '.join(missing)}",
                code="INVALID_LEVEL_B_REQUEST",
                blocks=["OUTPUT_NOT_OPPONIBLE"],
            )

        for list_field in ("warnings", "errors", "blocks"):
            if not isinstance(request_envelope[list_field], list):
                raise RealInvokerValidationError(
                    f"Request field '{list_field}' must be a list.",
                    code="INVALID_LEVEL_B_REQUEST",
                    blocks=["OUTPUT_NOT_OPPONIBLE"],
                )

        if not isinstance(request_envelope["payload"], dict):
            raise RealInvokerValidationError(
                "Request payload must be an object/dict.",
                code="INVALID_LEVEL_B_REQUEST",
                blocks=["OUTPUT_NOT_OPPONIBLE"],
            )

        forbidden_hits = self._find_forbidden_fields(request_envelope)
        if forbidden_hits:
            raise RealInvokerValidationError(
                f"Forbidden Level B request fields detected: {', '.join(forbidden_hits)}",
                code="FORBIDDEN_LEVEL_B_REQUEST_FIELD",
                blocks=["RAG_SCOPE_VIOLATION", "OUTPUT_NOT_OPPONIBLE"],
            )

    def validate_response_envelope(
        self,
        response_envelope: JsonDict,
        request_envelope: JsonDict,
    ) -> JsonDict:
        if not isinstance(response_envelope, dict):
            raise RealInvokerValidationError(
                "Federated runner response must be an object/dict.",
                code="INVALID_LEVEL_B_RESPONSE",
                blocks=["OUTPUT_NOT_OPPONIBLE"],
            )

        missing = [field for field in REQUIRED_RESPONSE_FIELDS if field not in response_envelope]
        if missing:
            raise RealInvokerValidationError(
                f"Missing required response fields: {', '.join(missing)}",
                code="INVALID_LEVEL_B_RESPONSE",
                blocks=["AUDIT_INCOMPLETE", "OUTPUT_NOT_OPPONIBLE"],
            )

        self._validate_response_identity(response_envelope, request_envelope)

        for list_field in ("warnings", "errors", "blocks"):
            if not isinstance(response_envelope[list_field], list):
                raise RealInvokerValidationError(
                    f"Response field '{list_field}' must be a list.",
                    code="INVALID_LEVEL_B_RESPONSE",
                    blocks=["AUDIT_INCOMPLETE", "OUTPUT_NOT_OPPONIBLE"],
                )

        if not isinstance(response_envelope["payload"], dict):
            raise RealInvokerValidationError(
                "Response payload must be an object/dict.",
                code="INVALID_LEVEL_B_RESPONSE",
                blocks=["OUTPUT_NOT_OPPONIBLE"],
            )

        forbidden_hits = self._find_forbidden_fields(response_envelope)
        if forbidden_hits:
            derived_blocks = ["RAG_SCOPE_VIOLATION", "OUTPUT_NOT_OPPONIBLE"]
            if any(hit in {"m07_closed", "m07_completed", "m07_approved"} for hit in forbidden_hits):
                derived_blocks.append("M07_REQUIRED")
            raise RealInvokerValidationError(
                f"Forbidden Level B response fields detected: {', '.join(forbidden_hits)}",
                code="FORBIDDEN_LEVEL_B_RESPONSE_FIELD",
                blocks=derived_blocks,
            )

        documentary_packet = self._extract_documentary_packet(response_envelope["payload"])
        self._validate_documentary_packet(documentary_packet)

        # regola prudenziale: i blocchi del packet devono allinearsi a quelli dell'envelope
        packet_blocks = documentary_packet.get("blocks", [])
        envelope_blocks = response_envelope.get("blocks", [])
        for block in packet_blocks:
            if block not in envelope_blocks:
                envelope_blocks.append(block)

        response = deepcopy(response_envelope)
        response["blocks"] = envelope_blocks

        # degradazione automatica prudenziale se esistono blocchi
        if response["blocks"]:
            response["status"] = BLOCKED_STATUS
        elif response["warnings"]:
            response["status"] = SUCCESS_WITH_WARNINGS_STATUS
        else:
            response["status"] = response.get("status") or SUCCESS_STATUS

        return response

    def _validate_response_identity(
        self,
        response_envelope: JsonDict,
        request_envelope: JsonDict,
    ) -> None:
        for field in ("request_id", "case_id", "trace_id"):
            if response_envelope.get(field) != request_envelope.get(field):
                raise RealInvokerValidationError(
                    f"Response field '{field}' does not match the request envelope.",
                    code="RESPONSE_IDENTITY_MISMATCH",
                    blocks=["AUDIT_INCOMPLETE", "OUTPUT_NOT_OPPONIBLE"],
                )

    def _extract_documentary_packet(self, payload: JsonDict) -> JsonDict:
        if "documentary_packet" in payload:
            packet = payload["documentary_packet"]
            if not isinstance(packet, dict):
                raise RealInvokerValidationError(
                    "Payload field 'documentary_packet' must be an object/dict.",
                    code="INVALID_DOCUMENTARY_PACKET",
                    blocks=["OUTPUT_NOT_OPPONIBLE"],
                )
            return packet
        return payload

    def _validate_documentary_packet(self, packet: JsonDict) -> None:
        missing = [field for field in REQUIRED_DOCUMENTARY_PACKET_FIELDS if field not in packet]
        if missing:
            raise RealInvokerValidationError(
                f"Missing documentary packet fields: {', '.join(missing)}",
                code="INVALID_DOCUMENTARY_PACKET",
                blocks=["OUTPUT_NOT_OPPONIBLE", "AUDIT_INCOMPLETE"],
            )

        for list_field in (
            "sources",
            "norm_units",
            "citations_valid",
            "citations_blocked",
            "vigenza_records",
            "cross_reference_records",
            "warnings",
            "errors",
            "blocks",
        ):
            if not isinstance(packet[list_field], list):
                raise RealInvokerValidationError(
                    f"Documentary packet field '{list_field}' must be a list.",
                    code="INVALID_DOCUMENTARY_PACKET",
                    blocks=["OUTPUT_NOT_OPPONIBLE"],
                )

        if not isinstance(packet["coverage_assessment"], dict):
            raise RealInvokerValidationError(
                "Documentary packet field 'coverage_assessment' must be a dict.",
                code="INVALID_DOCUMENTARY_PACKET",
                blocks=["COVERAGE_INADEQUATE", "OUTPUT_NOT_OPPONIBLE"],
            )

        if not isinstance(packet["shadow_fragment"], dict):
            raise RealInvokerValidationError(
                "Documentary packet field 'shadow_fragment' must be a dict.",
                code="INVALID_DOCUMENTARY_PACKET",
                blocks=["AUDIT_INCOMPLETE", "OUTPUT_NOT_OPPONIBLE"],
            )

    def _find_forbidden_fields(self, data: Any) -> List[str]:
        hits: Set[str] = set()
        self._scan_forbidden_fields(data, hits)
        return sorted(hits)

    def _scan_forbidden_fields(self, data: Any, hits: Set[str]) -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                if key in self.forbidden_level_b_fields:
                    hits.add(key)
                self._scan_forbidden_fields(value, hits)
        elif isinstance(data, list):
            for item in data:
                self._scan_forbidden_fields(item, hits)

    def _build_error_response_from_request(
        self,
        *,
        request: JsonDict,
        status: str,
        message: str,
        error_code: str,
        blocks: Optional[List[str]] = None,
        extra_errors: Optional[List[str]] = None,
    ) -> JsonDict:
        block_list = list(dict.fromkeys(blocks or []))
        error_list = list(dict.fromkeys(extra_errors or [error_code]))
        return {
            "request_id": request.get("request_id"),
            "case_id": request.get("case_id"),
            "trace_id": request.get("trace_id"),
            "api_version": request.get("api_version", self.api_version),
            "responder_module": self.responder_module,
            "status": status,
            "payload": {
                "documentary_packet": {
                    "sources": [],
                    "norm_units": [],
                    "citations_valid": [],
                    "citations_blocked": [],
                    "vigenza_records": [],
                    "cross_reference_records": [],
                    "coverage_assessment": {
                        "coverage_status": "UNAVAILABLE",
                        "critical_gap_flag": True,
                        "coverage_scope_notes": message,
                    },
                    "warnings": [],
                    "errors": error_list,
                    "blocks": block_list,
                    "shadow_fragment": {
                        "invoker": self.responder_module,
                        "validation_status": status,
                        "technical_notes": [message],
                    },
                }
            },
            "warnings": [],
            "errors": error_list,
            "blocks": block_list,
            "timestamp": request.get("timestamp"),
        }
