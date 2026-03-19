from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


M07_DOCUMENTARY_SUPPORT_MODULE_ID = "A_M07_DOCUMENTARY_SUPPORT_ADAPTER"
M07_DOCUMENTARY_SUPPORT_ENTRYPOINT = "runtime.m07_documentary_support_adapter.run_m07_documentary_support_exchange"


class M07ModuleRegistryError(Exception):
    """Base exception for the controlled Level A module registry."""


class M07ModuleNotFoundError(M07ModuleRegistryError):
    """Raised when the requested module is not present in the local registry."""


class M07ModuleDisabledError(M07ModuleRegistryError):
    """Raised when the requested module exists but is not enabled."""


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _schemas_dir() -> Path:
    return _project_root() / "schemas"


def _load_registry_schema() -> dict[str, Any]:
    schema_path = _schemas_dir() / "m07_documentary_support_module_registry_v1.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def get_m07_documentary_support_module_registry() -> dict[str, Any]:
    """
    Registro locale e controllato del modulo M07 Documentary Support Adapter.

    Non aggancia il runner federato.
    Non abilita semantiche conclusive.
    Non modifica il core A/B.
    """
    return {
        "registry_id": "m07_documentary_support_module_registry_v1",
        "registry_type": "LEVEL_A_LOCAL_MODULE_REGISTRY",
        "schema_version": "1.0",
        "baseline_tag": "stable-final-ab-master-cycle-v1",
        "foundation_tag": "stable-m07-documentary-support-foundation-v1",
        "runtime_adapter_tag": "stable-m07-documentary-support-runtime-adapter-v1",
        "modules": [
            {
                "module_id": M07_DOCUMENTARY_SUPPORT_MODULE_ID,
                "module_name": "M07 Documentary Support Adapter",
                "module_layer": "A",
                "module_kind": "CONTROLLED_LOCAL_ADAPTER",
                "enabled": True,
                "entrypoint": M07_DOCUMENTARY_SUPPORT_ENTRYPOINT,
                "dispatch_mode": "MANUAL_LEVEL_A_ONLY",
                "request_schema": "schemas/m07_documentary_support_request_schema_v1.json",
                "response_schema": "schemas/m07_documentary_support_response_schema_v1.json",
                "evidence_schema": "schemas/m07_evidence_pack_schema_v1.json",
                "allowed_callers": [
                    "A1_OrchestratorePPAV",
                    "A2_CaseClassifier",
                    "A4_M07Governor",
                ],
                "target_module": "B16_M07SupportLayer",
                "support_only": True,
                "human_completion_required": True,
                "can_close_m07": False,
                "can_authorize_output": False,
                "can_emit_go_no_go": False,
                "can_build_rac": False,
                "can_modify_runner_federated": False,
                "guardrails": [
                    "NO_DECISION",
                    "NO_GO_NO_GO",
                    "NO_M07_CLOSE",
                    "NO_OUTPUT_AUTH",
                    "NO_RAC_BUILD",
                    "BOUNDARY_ENFORCED",
                    "BLOCK_PROPAGATION_REQUIRED",
                ],
                "notes": (
                    "Modulo registrato solo nel Livello A come adapter locale controllato. "
                    "Non costituisce integrazione nel runner federato e non abilita output opponibili."
                ),
            }
        ],
    }


def get_m07_documentary_support_module_entry() -> dict[str, Any]:
    registry = get_m07_documentary_support_module_registry()
    for module in registry["modules"]:
        if module["module_id"] == M07_DOCUMENTARY_SUPPORT_MODULE_ID:
            return copy.deepcopy(module)
    raise M07ModuleNotFoundError(
        f"Modulo non trovato: {M07_DOCUMENTARY_SUPPORT_MODULE_ID}"
    )


def resolve_m07_documentary_support_dispatch(
    caller_module: str,
) -> dict[str, Any]:
    module = get_m07_documentary_support_module_entry()

    if module["enabled"] is not True:
        raise M07ModuleDisabledError(
            f"Modulo disabilitato: {module['module_id']}"
        )

    if caller_module not in module["allowed_callers"]:
        raise M07ModuleRegistryError(
            f"Caller non autorizzato per il modulo {module['module_id']}: {caller_module}"
        )

    return {
        "module_id": module["module_id"],
        "entrypoint": module["entrypoint"],
        "dispatch_mode": module["dispatch_mode"],
        "target_module": module["target_module"],
        "support_only": module["support_only"],
        "human_completion_required": module["human_completion_required"],
        "can_close_m07": module["can_close_m07"],
        "can_authorize_output": module["can_authorize_output"],
        "can_emit_go_no_go": module["can_emit_go_no_go"],
        "can_build_rac": module["can_build_rac"],
        "can_modify_runner_federated": module["can_modify_runner_federated"],
        "guardrails": copy.deepcopy(module["guardrails"]),
    }


def get_m07_documentary_support_registry_snapshot() -> dict[str, Any]:
    """
    Restituisce uno snapshot tecnico leggibile dal Livello A,
    senza produrre alcuna azione esecutiva.
    """
    registry = get_m07_documentary_support_module_registry()
    module = get_m07_documentary_support_module_entry()

    return {
        "registry_id": registry["registry_id"],
        "baseline_tag": registry["baseline_tag"],
        "module_count": len(registry["modules"]),
        "registered_module_ids": [m["module_id"] for m in registry["modules"]],
        "module_snapshot": module,
        "requires_manual_level_a_governance": True,
        "runner_federated_touched": False,
        "decision_enabled": False,
        "output_authorization_enabled": False,
    }