import os

import pytest

from runtime.federated_runner_live_transport import build_transport
from runtime.final_aba_runner_real_invoker import FederatedRunnerRealInvoker
from runtime.final_aba_runtime_handoff_service import FinalABARuntimeHandoffService
from runtime.metodo_cerda_documentary_orchestrator import orchestrate_documentary_runtime_slice


def _classified_case():
    return {
        "request_id": os.getenv("A1_TER_REAL_REQUEST_ID", "REQ-A1TER-REAL-001"),
        "case_id": os.getenv("A1_TER_REAL_CASE_ID", "CASE-A1TER-REAL-001"),
        "trace_id": os.getenv("A1_TER_REAL_TRACE_ID", "TRACE-A1TER-REAL-001"),
        "natura_output": "ATTO",
        "tipologia_atto": "DETERMINA",
        "materia_prevalente": "CONTRATTI",
        "sensibilita": "MEDIA",
        "rischio_iniziale": "MEDIO",
        "intensita_applicativa": "MEDIA",
        "zone_rosse": [],
        "fast_track": False,
        "moduli_attivati": ["M07-LPR", "RAC"],
        "esigenza_documentale": True,
        "obiettivo_documentale": "verifica vigenza, rinvii e supporto M07/RAC",
        "query_guidata": os.getenv(
            "A1_TER_REAL_QUERY_GUIDATA",
            "art. 107 TUEL responsabilita gestionale e separazione indirizzo gestione",
        ),
        "corpora_preferiti": ["tuel", "l241"],
        "contesto_metodologico": {"fase0_requires_federated_documentary_support": True},
        "caller_module": "A0_FASE0",
    }


@pytest.mark.real_local_bridge
def test_documentary_orchestrator_end_to_end_real_local():
    if not os.getenv("FEDERATED_RUNNER_LIVE_ENDPOINT"):
        pytest.skip("FEDERATED_RUNNER_LIVE_ENDPOINT non configurato per il bridge locale reale.")

    transport = build_transport()
    handoff = FinalABARuntimeHandoffService(
        mode="real",
        real_invoker=FederatedRunnerRealInvoker(transport=transport),
    )

    result = orchestrate_documentary_runtime_slice(
        _classified_case(),
        handoff=handoff,
    )

    assert result["handoff_called"] is True
    assert result["gate_output"]["gate_status"] in {"PROCEED", "DEGRADE", "BLOCK"}
    assert result["routing_output"]["routing_status"] in {"ROUTED", "PARTIAL", "BLOCKED"}
    assert result["level_b_documentary_only"] is True

    m07_pack = result["routing_output"].get("m07_evidence_pack_ref")
    if m07_pack is not None:
        assert m07_pack["human_completion_required"] is True
        assert "m07_closed" not in m07_pack

    rac_input = result["routing_output"].get("rac_documentary_input_ref")
    if rac_input is not None:
        assert "rac_finalized" not in rac_input
