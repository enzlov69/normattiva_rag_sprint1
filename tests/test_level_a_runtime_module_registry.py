import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "schemas" / "level_a_runtime_module_registry_v1.json"


def _load() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_level_a_runtime_module_registry_covers_minimum_modules() -> None:
    registry = _load()
    codes = {module["module_code"] for module in registry["modules"]}
    assert {
        "A1_OrchestratorePPAV",
        "A4_M07Governor",
        "A6_RACBuilder",
        "A5_FinalComplianceGate",
        "A7_OutputAuthorizer",
        "A8_AuditLogger",
        "A9_SHADOWTracer"
    }.issubset(codes)


def test_level_a_runtime_modules_keep_decision_validation_and_signature_in_level_a() -> None:
    registry = _load()
    modules = {module["module_code"]: module for module in registry["modules"]}

    assert modules["A5_FinalComplianceGate"]["can_receive_from_level_b"] is True
    assert modules["A7_OutputAuthorizer"]["can_call_level_b"] is False
    assert "move_final_compliance_to_level_b" in modules["A5_FinalComplianceGate"]["forbidden_runtime_actions"]
    assert "accept_output_authorized_from_level_b" in modules["A7_OutputAuthorizer"]["forbidden_runtime_actions"]


def test_level_a_runtime_modules_do_not_allow_forbidden_runtime_actions() -> None:
    registry = _load()
    forbidden_actions = {
        "delegate_final_decision_to_level_b",
        "delegate_m07_closure_to_level_b",
        "delegate_output_authorization_to_level_b",
        "move_final_compliance_to_level_b",
        "accept_output_authorized_from_level_b"
    }
    listed_forbidden = set()
    for module in registry["modules"]:
        listed_forbidden.update(module["forbidden_runtime_actions"])
    assert forbidden_actions.issubset(listed_forbidden)

