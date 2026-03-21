from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Dict

from runtime.metodo_cerda_documentary_gate import (
    build_not_required_gate_output,
    evaluate_documentary_gate,
)
from runtime.metodo_cerda_documentary_request_builder import build_documentary_request_envelope
from runtime.metodo_cerda_documentary_router import route_documentary_support
from src.config.settings import OFFICIAL_SOURCE_DOMAINS


JsonDict = Dict[str, Any]
HandoffCallable = Callable[[JsonDict], JsonDict]
InstitutionalWebFetcher = Callable[[JsonDict], JsonDict]


DOCUMENTARY_TRIGGER_TOKENS = (
    "m07",
    "lpr",
    "citazioni",
    "citation",
    "vigenza",
    "rinvii",
    "coverage",
    "rac",
    "documentale",
    "federato",
)

INSTITUTIONAL_DOMAINS = tuple(
    dict.fromkeys(
        OFFICIAL_SOURCE_DOMAINS
        + (
            "www.giustizia-amministrativa.it",
            "www.cortediconti.it",
            "www.anac.it",
            "www.aranagenzia.it",
            "www.rgs.mef.gov.it",
            "www.arconet.rgs.tesoro.it",
            "www.regione.sicilia.it",
            "gurs.regione.sicilia.it",
            "www.ifel.it",
        )
    )
)


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def should_invoke_level_b(classified_case: JsonDict) -> bool:
    if bool(classified_case.get("esigenza_documentale")):
        return True

    modules = [_normalize_text(value) for value in classified_case.get("moduli_attivati", [])]
    if any(token in module for module in modules for token in ("m07", "rac", "ppav")):
        return True

    if bool(classified_case.get("zone_rosse")):
        return True

    objective = _normalize_text(classified_case.get("obiettivo_documentale"))
    query = _normalize_text(classified_case.get("query_guidata"))
    if any(token in objective or token in query for token in DOCUMENTARY_TRIGGER_TOKENS):
        return True

    context = classified_case.get("contesto_metodologico")
    if isinstance(context, dict):
        if bool(context.get("fase0_requires_federated_documentary_support")):
            return True
        if bool(context.get("needs_federated_documentary_support")):
            return True

    return False


def _call_handoff(handoff: Any, request_envelope: JsonDict) -> JsonDict:
    if hasattr(handoff, "handle") and callable(handoff.handle):
        return handoff.handle(request_envelope)
    if hasattr(handoff, "execute") and callable(handoff.execute):
        return handoff.execute(request_envelope)
    if callable(handoff):
        return handoff(request_envelope)
    raise TypeError("handoff must expose handle/execute or be callable")


def _build_institutional_web_context(
    classified_case: JsonDict,
    gate_output: JsonDict,
) -> JsonDict:
    reasons = deepcopy(gate_output.get("institutional_web_reason", []))
    selected_domains = list(INSTITUTIONAL_DOMAINS)
    return {
        "request_id": classified_case["request_id"],
        "case_id": classified_case["case_id"],
        "trace_id": classified_case["trace_id"],
        "status": "NOT_REQUIRED" if not gate_output.get("institutional_web_required") else "PLANNED",
        "documentary_channel": gate_output.get("documentary_channel", "FEDERATED_ONLY"),
        "reasons": reasons,
        "queries": [
            {
                "reason": reason,
                "query": classified_case.get("query_guidata"),
                "domains": selected_domains,
            }
            for reason in reasons
        ],
        "entries": [],
        "warnings": [],
        "errors": [],
        "blocks": [],
        "federated_is_not_official_source": True,
        "official_domains_only": True,
    }


def _run_institutional_web_recovery(
    classified_case: JsonDict,
    gate_output: JsonDict,
    *,
    institutional_web_fetcher: Any = None,
) -> JsonDict:
    recovery = _build_institutional_web_context(classified_case, gate_output)
    if recovery["status"] == "NOT_REQUIRED" or institutional_web_fetcher is None:
        return recovery

    if hasattr(institutional_web_fetcher, "fetch") and callable(institutional_web_fetcher.fetch):
        fetched = institutional_web_fetcher.fetch(deepcopy(recovery))
    elif callable(institutional_web_fetcher):
        fetched = institutional_web_fetcher(deepcopy(recovery))
    else:
        raise TypeError("institutional_web_fetcher must expose fetch(...) or be callable")

    result = deepcopy(recovery)
    if isinstance(fetched, dict):
        result.update(deepcopy(fetched))
    result["status"] = str(result.get("status") or "COMPLETED")
    result.setdefault("entries", [])
    result.setdefault("warnings", [])
    result.setdefault("errors", [])
    result.setdefault("blocks", [])
    result["federated_is_not_official_source"] = True
    result["official_domains_only"] = True
    return result


def orchestrate_documentary_runtime_slice(
    classified_case: JsonDict,
    *,
    handoff: Any,
    institutional_web_fetcher: Any = None,
    timestamp: str | None = None,
) -> JsonDict:
    should_invoke = should_invoke_level_b(classified_case)

    if not should_invoke:
        gate_output = build_not_required_gate_output(classified_case)
        institutional_web_recovery = _build_institutional_web_context(classified_case, gate_output)
        routing_output = route_documentary_support(
            classified_case,
            gate_output,
            None,
            institutional_web_recovery=institutional_web_recovery,
        )
        return {
            "request_id": classified_case["request_id"],
            "case_id": classified_case["case_id"],
            "trace_id": classified_case["trace_id"],
            "orchestrator_status": "NOT_REQUIRED",
            "should_invoke_level_b": False,
            "handoff_called": False,
            "documentary_request_envelope": None,
            "level_b_response_envelope": None,
            "gate_output": gate_output,
            "routing_output": routing_output,
            "institutional_web_recovery": institutional_web_recovery,
            "critical_blocks": [],
            "warning_flags": [],
            "degradation_reasons": [],
            "audit_update": {
                "event_type": "A1_TER_DOCUMENTARY_NOT_REQUIRED",
                "request_id": classified_case["request_id"],
                "trace_id": classified_case["trace_id"],
            },
            "shadow_update": {
                "update_type": "A1_TER_DOCUMENTARY_SHADOW_NOT_REQUIRED",
                "trace_id": classified_case["trace_id"],
                "documentary_only": True,
            },
            "can_finalize_case": False,
            "can_authorize_output": False,
            "can_emit_go_no_go": False,
            "level_b_documentary_only": True,
        }

    request_envelope = build_documentary_request_envelope(classified_case, timestamp=timestamp)
    response_envelope = _call_handoff(handoff, request_envelope)
    gate_output = evaluate_documentary_gate(classified_case, response_envelope)
    institutional_web_recovery = _run_institutional_web_recovery(
        classified_case,
        gate_output,
        institutional_web_fetcher=institutional_web_fetcher,
    )
    routing_output = route_documentary_support(
        classified_case,
        gate_output,
        response_envelope,
        institutional_web_recovery=institutional_web_recovery,
    )

    orchestrator_status_map = {
        "PROCEED": "DOCUMENTARY_ROUTED",
        "DEGRADE": "DOCUMENTARY_DEGRADED",
        "BLOCK": "DOCUMENTARY_BLOCKED",
        "NOT_REQUIRED": "NOT_REQUIRED",
    }

    return {
        "request_id": classified_case["request_id"],
        "case_id": classified_case["case_id"],
        "trace_id": classified_case["trace_id"],
        "orchestrator_status": orchestrator_status_map[gate_output["gate_status"]],
        "should_invoke_level_b": True,
        "handoff_called": True,
        "documentary_request_envelope": deepcopy(request_envelope),
        "level_b_response_envelope": deepcopy(response_envelope),
        "gate_output": deepcopy(gate_output),
        "routing_output": deepcopy(routing_output),
        "institutional_web_recovery": deepcopy(institutional_web_recovery),
        "critical_blocks": deepcopy(gate_output["critical_blocks"]),
        "warning_flags": deepcopy(gate_output["warning_flags"]),
        "degradation_reasons": deepcopy(gate_output["degradation_reasons"]),
        "audit_update": deepcopy(routing_output.get("audit_event_ref")),
        "shadow_update": deepcopy(routing_output.get("shadow_update_ref")),
        "can_finalize_case": False,
        "can_authorize_output": False,
        "can_emit_go_no_go": False,
        "level_b_documentary_only": True,
    }
