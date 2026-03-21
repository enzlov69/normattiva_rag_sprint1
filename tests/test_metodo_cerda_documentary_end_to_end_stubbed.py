from runtime.metodo_cerda_documentary_orchestrator import orchestrate_documentary_runtime_slice


def _classified_case():
    return {
        "request_id": "REQ-A1TER-E2E-001",
        "case_id": "CASE-A1TER-E2E-001",
        "trace_id": "TRACE-A1TER-E2E-001",
        "natura_output": "ATTO",
        "tipologia_atto": "DETERMINA",
        "materia_prevalente": "PERSONALE",
        "sensibilita": "MEDIA",
        "rischio_iniziale": "MEDIO",
        "intensita_applicativa": "MEDIA",
        "zone_rosse": [],
        "fast_track": False,
        "moduli_attivati": ["M07-LPR", "RAC"],
        "esigenza_documentale": True,
        "obiettivo_documentale": "supporto documentale a M07 e RAC",
        "query_guidata": "art. 107 TUEL responsabilita gestionale",
        "corpora_preferiti": ["tuel", "l241"],
        "contesto_metodologico": {"fase0_requires_federated_documentary_support": True},
        "caller_module": "A0_FASE0",
    }


def test_documentary_orchestrator_end_to_end_stubbed():
    def _handoff(request):
        assert request["target_module"] == "B_REAL_FEDERATED_RUNNER"
        return {
            "status": "SUCCESS",
            "warnings": [],
            "errors": [],
            "blocks": [],
                "payload": {
                    "documentary_packet": {
                    "sources": [
                        {
                            "source_id": "src_1",
                            "uri_ufficiale": "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2000-08-18;267",
                        }
                    ],
                        "normative_units": [{"norm_unit_id": "art_1"}],
                        "citations": [{"citation_id": "cit_1"}],
                    "incomplete_citations": [],
                    "coverage": {"coverage_status": "ADEQUATE", "critical_gap_flag": False},
                    "vigenza_status": "CONFIRMED",
                    "rinvii_status": "RESOLVED",
                    "audit": {"events_present": True},
                    "shadow": {"executed_modules": ["B21_ReportGenerator"]},
                    "m07_support": {"ordered_reading_sequence": ["art_1"]},
                }
            },
        }

    result = orchestrate_documentary_runtime_slice(
        _classified_case(),
        handoff=_handoff,
        timestamp="2026-03-21T10:00:00Z",
    )

    assert result["handoff_called"] is True
    assert result["orchestrator_status"] == "DOCUMENTARY_ROUTED"
    assert result["gate_output"]["gate_status"] == "PROCEED"
    assert result["routing_output"]["routing_status"] == "ROUTED"
    assert result["can_emit_go_no_go"] is False
    assert result["level_b_documentary_only"] is True
    assert result["gate_output"]["documentary_channel"] == "FEDERATED_ONLY"
    assert "final_decision" not in str(result["level_b_response_envelope"]).lower()
