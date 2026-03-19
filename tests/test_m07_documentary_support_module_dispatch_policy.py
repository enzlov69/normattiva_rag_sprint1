import pytest

from runtime.m07_documentary_support_module_registry import (
    M07ModuleRegistryError,
    resolve_m07_documentary_support_dispatch,
)


def test_dispatch_resolution_allows_authorized_caller() -> None:
    resolved = resolve_m07_documentary_support_dispatch("A1_OrchestratorePPAV")

    assert resolved["module_id"] == "A_M07_DOCUMENTARY_SUPPORT_ADAPTER"
    assert resolved["dispatch_mode"] == "MANUAL_LEVEL_A_ONLY"
    assert resolved["support_only"] is True
    assert resolved["can_close_m07"] is False
    assert resolved["can_authorize_output"] is False
    assert resolved["can_emit_go_no_go"] is False
    assert resolved["can_build_rac"] is False
    assert resolved["can_modify_runner_federated"] is False


def test_dispatch_resolution_rejects_unauthorized_caller() -> None:
    with pytest.raises(M07ModuleRegistryError):
        resolve_m07_documentary_support_dispatch("A9_UnknownCaller")


def test_dispatch_resolution_keeps_guardrails_active() -> None:
    resolved = resolve_m07_documentary_support_dispatch("A4_M07Governor")

    assert "NO_DECISION" in resolved["guardrails"]
    assert "NO_M07_CLOSE" in resolved["guardrails"]
    assert "NO_OUTPUT_AUTH" in resolved["guardrails"]
    assert "BLOCK_PROPAGATION_REQUIRED" in resolved["guardrails"]