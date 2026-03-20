import importlib
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from typing import Any, Callable

import pytest

from runtime.final_aba_runner_real_invoker import FederatedRunnerRealInvoker
from runtime.final_aba_runtime_handoff_service import FinalABARuntimeHandoffService

TransportCallable = Callable[[dict], dict]


def _live_enabled() -> bool:
    return os.getenv("FEDERATED_RUNNER_LIVE_SMOKE") == "1"


def _load_transport() -> TransportCallable:
    if not _live_enabled():
        pytest.skip("Live smoke disabled. Set FEDERATED_RUNNER_LIVE_SMOKE=1 to run live tests.")

    target = os.getenv("FEDERATED_RUNNER_LIVE_TRANSPORT_IMPORT")
    if not target:
        pytest.skip(
            "Live smoke transport not configured. Set FEDERATED_RUNNER_LIVE_TRANSPORT_IMPORT=<module>:<callable>."
        )

    try:
        module_name, callable_name = target.split(":", 1)
    except ValueError as exc:
        raise AssertionError(
            "FEDERATED_RUNNER_LIVE_TRANSPORT_IMPORT must have format <module>:<callable>."
        ) from exc

    module = importlib.import_module(module_name)
    obj: Any = getattr(module, callable_name)
    transport = obj() if callable(obj) and callable(getattr(obj, "__call__", None)) and callable_name.startswith(("build_", "get_")) else obj

    if not callable(transport):
        raise AssertionError("Configured live transport is not callable.")

    return transport


def _request() -> dict:
    return {
        "request_id": os.getenv("FEDERATED_RUNNER_LIVE_REQUEST_ID", "req_live_smoke_002"),
        "case_id": os.getenv("FEDERATED_RUNNER_LIVE_CASE_ID", "case_live_smoke_002"),
        "trace_id": os.getenv("FEDERATED_RUNNER_LIVE_TRACE_ID", "trace_live_smoke_002"),
        "api_version": "1.0",
        "caller_module": "A0_FASE0",
        "target_module": "B_REAL_FEDERATED_RUNNER",
        "timestamp": "2026-03-20T15:05:00Z",
        "status": "READY_FOR_LEVEL_B",
        "warnings": [],
        "errors": [],
        "blocks": [],
        "payload": {
            "documentary_goal": os.getenv(
                "FEDERATED_RUNNER_LIVE_DOCUMENTARY_GOAL", "retrieve documentary packet only"
            ),
            "domain_code": os.getenv("FEDERATED_RUNNER_LIVE_DOMAIN_CODE", "ENTI_LOCALI"),
            "m07_mode": "SUPPORT_ONLY",
            "query_text": os.getenv(
                "FEDERATED_RUNNER_LIVE_QUERY_TEXT",
                "art. 107 TUEL responsabilità gestionale enti locali",
            ),
        },
        "audit": {"trail_events": []},
        "shadow": {"fragments": []},
    }


def test_live_runner_roundtrip_keeps_documentary_only_contract():
    transport = _load_transport()
    real_invoker = FederatedRunnerRealInvoker(transport=transport)
    service = FinalABARuntimeHandoffService(mode="real", real_invoker=real_invoker)

    result = service.handle(_request())

    assert result["request_id"] == _request()["request_id"]
    assert result["case_id"] == _request()["case_id"]
    assert result["trace_id"] == _request()["trace_id"]
    assert result["payload"]["level_b_documentary_only"] is True
    assert result["payload"]["opponibility_status"] == "NOT_OPPONIBLE_OUTSIDE_LEVEL_A"
    assert result["payload"]["level_a_next_step"] in {
        "M07_LPR_GOVERNED_BY_LEVEL_A",
        "M07_LPR_MANDATORY_CONTINUATION_IN_LEVEL_A",
    }

    packet = result["payload"].get("documentary_packet", {})
    assert isinstance(packet.get("sources"), list)
    assert isinstance(packet.get("norm_units"), list)
    assert isinstance(packet.get("citations_valid"), list)
    assert isinstance(packet.get("citations_blocked"), list)
    assert isinstance(packet.get("vigenza_records"), list)
    assert isinstance(packet.get("cross_reference_records"), list)
    assert isinstance(packet.get("coverage_assessment"), dict)
    assert isinstance(packet.get("shadow_fragment"), dict)
    assert result["audit"]["trail_events"]
    assert result["shadow"]["fragments"]
