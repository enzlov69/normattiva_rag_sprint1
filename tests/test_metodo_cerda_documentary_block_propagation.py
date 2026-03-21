from runtime.metodo_cerda_documentary_orchestrator import orchestrate_documentary_runtime_slice


def _classified_case():
    return {
        "request_id": "REQ-A1TER-BLOCK-001",
        "case_id": "CASE-A1TER-BLOCK-001",
        "trace_id": "TRACE-A1TER-BLOCK-001",
        "natura_output": "ATTO",
        "tipologia_atto": "DETERMINA",
        "materia_prevalente": "CONTRATTI",
        "sensibilita": "ALTA",
        "rischio_iniziale": "ALTO",
        "intensita_applicativa": "ALTA",
        "zone_rosse": ["ALLEGATO_MANCANTE"],
        "fast_track": False,
        "moduli_attivati": ["M07-LPR", "RAC"],
        "esigenza_documentale": True,
        "obiettivo_documentale": "supporto M07 e verifica vigenza",
        "query_guidata": "art. 107 TUEL",
        "corpora_preferiti": ["tuel"],
        "contesto_metodologico": {"fase0_requires_federated_documentary_support": True},
        "caller_module": "A0_FASE0",
    }


def test_level_a_propagates_critical_block_from_level_b():
    def _handoff(_request):
        return {
            "status": "BLOCKED",
            "warnings": [],
            "errors": [],
            "blocks": [{"block_code": "M07_REQUIRED"}],
            "payload": {
                "documentary_packet": {
                    "sources": [{"source_id": "src_1"}],
                    "normative_units": [{"norm_unit_id": "art_1"}],
                    "citations": [{"citation_id": "cit_1", "stato_vigenza": "VIGENTE_VERIFICATA"}],
                    "incomplete_citations": [],
                    "coverage": {"coverage_status": "ADEQUATE", "critical_gap_flag": False},
                    "vigenza_status": "CONFIRMED",
                    "rinvii_status": "RESOLVED",
                    "audit": {"events_present": True},
                    "shadow": {"executed_modules": ["B16_M07SupportLayer"]},
                }
            },
        }

    result = orchestrate_documentary_runtime_slice(
        _classified_case(),
        handoff=_handoff,
        timestamp="2026-03-21T10:00:00Z",
    )

    assert result["orchestrator_status"] == "DOCUMENTARY_BLOCKED"
    assert "M07_REQUIRED" in result["critical_blocks"]
    assert result["routing_output"]["routing_status"] == "BLOCKED"
