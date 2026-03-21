from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from runtime.final_aba_runner_real_invoker import FederatedRunnerRealInvoker

JsonDict = Dict[str, Any]
InvokerCallable = Callable[[JsonDict], JsonDict]


class HandoffConfigurationError(Exception):
    pass


@dataclass(slots=True)
class FinalABARuntimeHandoffService:
    """
    Layer contrattuale A→B→A.

    Funzioni:
    - mantiene il primo punto di accoppiamento nel layer di orchestrazione;
    - seleziona invoker mock o reale senza bypass del servizio di handoff;
    - propaga blocchi, errori e warning del Livello B verso il Livello A;
    - arricchisce audit trail e SHADOW tecnico;
    - impedisce che il pacchetto documentale venga scambiato per esito opponibile.
    """

    mode: str = "mock"
    mock_invoker: Optional[InvokerCallable] = None
    real_invoker: Optional[FederatedRunnerRealInvoker] = None

    def handle(self, request_envelope: JsonDict) -> JsonDict:
        request = self._normalize_request(request_envelope)
        self._append_audit_event(request, event="HANDOFF_REQUEST_RECEIVED")

        invoker = self._select_invoker()
        self._append_audit_event(request, event=f"LEVEL_B_INVOKER_SELECTED:{self.mode.upper()}")

        response = invoker(deepcopy(request))
        response = self._normalize_response(response, request)
        response = self._propagate_documentary_blocks(response)
        response = self._enforce_level_a_governance(response)
        response = self._enrich_shadow(response, request)
        response = self._enrich_audit(response)
        return response

    def _select_invoker(self) -> InvokerCallable:
        if self.mode == "real":
            if self.real_invoker is None:
                raise HandoffConfigurationError("Real invoker is required when mode='real'.")
            return self.real_invoker.invoke
        if self.mode == "mock":
            if self.mock_invoker is None:
                raise HandoffConfigurationError("Mock invoker is required when mode='mock'.")
            return self.mock_invoker
        raise HandoffConfigurationError(f"Unsupported handoff mode: {self.mode}")

    def _normalize_request(self, request_envelope: JsonDict) -> JsonDict:
        request = deepcopy(request_envelope)
        request.setdefault("status", "READY_FOR_LEVEL_B")
        request.setdefault("warnings", [])
        request.setdefault("errors", [])
        request.setdefault("blocks", [])
        request.setdefault("payload", {})
        request.setdefault("timestamp", self._now_iso())
        request.setdefault("audit", {"trail_events": []})
        request.setdefault("shadow", {"fragments": []})
        return request

    def _normalize_response(self, response_envelope: JsonDict, request_envelope: JsonDict) -> JsonDict:
        response = deepcopy(response_envelope)
        response.setdefault("request_id", request_envelope.get("request_id"))
        response.setdefault("case_id", request_envelope.get("case_id"))
        response.setdefault("trace_id", request_envelope.get("trace_id"))
        response.setdefault("timestamp", self._now_iso())
        response.setdefault("warnings", [])
        response.setdefault("errors", [])
        response.setdefault("blocks", [])
        response.setdefault("payload", {})
        response.setdefault("audit", {"trail_events": []})
        response.setdefault("shadow", {"fragments": []})
        return response

    def _propagate_documentary_blocks(self, response_envelope: JsonDict) -> JsonDict:
        response = deepcopy(response_envelope)
        packet = response.get("payload", {}).get("documentary_packet", {})
        packet_blocks = packet.get("blocks", []) if isinstance(packet, dict) else []
        packet_errors = packet.get("errors", []) if isinstance(packet, dict) else []
        packet_warnings = packet.get("warnings", []) if isinstance(packet, dict) else []

        response["blocks"] = self._dedupe(response.get("blocks", []) + packet_blocks)
        response["errors"] = self._dedupe(response.get("errors", []) + packet_errors)
        response["warnings"] = self._dedupe(response.get("warnings", []) + packet_warnings)

        if response["blocks"] and response.get("status") not in {"REJECTED", "ERROR"}:
            response["status"] = "BLOCKED"
        elif response["warnings"] and response.get("status") == "SUCCESS":
            response["status"] = "SUCCESS_WITH_WARNINGS"

        return response

    def _enforce_level_a_governance(self, response_envelope: JsonDict) -> JsonDict:
        response = deepcopy(response_envelope)
        packet = response.get("payload", {}).get("documentary_packet", {})
        coverage = packet.get("coverage_assessment", {}) if isinstance(packet, dict) else {}

        # Nessun pacchetto del Livello B è opponibile di per sé.
        response["payload"].setdefault("level_a_next_step", "M07_LPR_GOVERNED_BY_LEVEL_A")
        response["payload"]["level_b_documentary_only"] = True
        response["payload"]["opponibility_status"] = "NOT_OPPONIBLE_OUTSIDE_LEVEL_A"

        if coverage.get("critical_gap_flag") is True:
            response["blocks"] = self._dedupe(response.get("blocks", []) + ["COVERAGE_INADEQUATE"])
            if response.get("status") not in {"REJECTED", "ERROR"}:
                response["status"] = "BLOCKED"

        if any(block in response.get("blocks", []) for block in ["M07_REQUIRED", "M07_DOCUMENTARY_INCOMPLETE"]):
            response["payload"]["level_a_next_step"] = "M07_LPR_MANDATORY_CONTINUATION_IN_LEVEL_A"

        return response

    def _enrich_shadow(self, response_envelope: JsonDict, request_envelope: JsonDict) -> JsonDict:
        response = deepcopy(response_envelope)
        shadow = response.setdefault("shadow", {"fragments": []})
        fragments = shadow.setdefault("fragments", [])
        fragments.append(
            {
                "trace_id": request_envelope.get("trace_id"),
                "handoff_mode": self.mode,
                "documentary_only": True,
                "opponibility": "forbidden_in_level_b",
                "timestamp": response.get("timestamp"),
            }
        )
        return response

    def _enrich_audit(self, response_envelope: JsonDict) -> JsonDict:
        response = deepcopy(response_envelope)
        audit = response.setdefault("audit", {"trail_events": []})
        events = audit.setdefault("trail_events", [])
        events.append(
            {
                "event": "LEVEL_B_RESPONSE_ACCEPTED_BY_HANDOFF",
                "status": response.get("status"),
                "blocks": list(response.get("blocks", [])),
                "errors": list(response.get("errors", [])),
                "timestamp": response.get("timestamp"),
            }
        )
        return response

    def _append_audit_event(self, envelope: JsonDict, *, event: str) -> None:
        audit = envelope.setdefault("audit", {"trail_events": []})
        events = audit.setdefault("trail_events", [])
        events.append({"event": event, "timestamp": envelope.get("timestamp", self._now_iso())})

    @staticmethod
    def _dedupe(values: list[Any]) -> list[Any]:
        deduped: list[Any] = []
        for value in values:
            if value not in deduped:
                deduped.append(value)
        return deduped

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
