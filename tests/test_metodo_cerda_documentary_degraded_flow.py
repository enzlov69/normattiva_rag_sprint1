from runtime.metodo_cerda_documentary_orchestrator import orchestrate_documentary_runtime_slice


def _classified_case():
    return {
        "request_id": "REQ-A1TER-DEGRADE-001",
        "case_id": "CASE-A1TER-DEGRADE-001",
        "trace_id": "TRACE-A1TER-DEGRADE-001",
        "natura_output": "PARERE",
        "tipologia_atto": None,
        "materia_prevalente": "TRASPARENZA",
        "sensibilita": "MEDIA",
        "rischio_iniziale": "MEDIO",
        "intensita_applicativa": "MEDIA",
        "zone_rosse": [],
        "fast_track": False,
        "moduli_attivati": ["RAC", "PPAV_ANALISI"],
        "esigenza_documentale": True,
        "obiettivo_documentale": "coverage documentale",
        "query_guidata": "dlgs 33 accesso civico",
        "corpora_preferiti": ["dlgs33"],
        "contesto_metodologico": {"fase0_requires_federated_documentary_support": True},
        "caller_module": "A0_FASE0",
    }


def test_degraded_flow_routes_only_as_traced_support():
    def _handoff(_request):
        return {
            "status": "DEGRADED",
            "warnings": [{"code": "COVERAGE_PARTIAL"}],
            "errors": [],
            "blocks": [],
            "payload": {
                "documentary_packet": {
                    "sources": [{"source_id": "src_1"}],
                    "normative_units": [{"norm_unit_id": "art_1"}],
                    "citations": [{"citation_id": "cit_1"}],
                    "incomplete_citations": [],
                    "coverage": {"coverage_status": "PARTIAL", "critical_gap_flag": False},
                    "vigenza_status": "CONFIRMED",
                    "rinvii_status": "RESOLVED",
                    "audit": {"events_present": True},
                    "shadow": {"executed_modules": ["B12_CoverageEstimator"]},
                }
            },
        }

    def _institutional_web_fetcher(recovery_request):
        return {
            "status": "COMPLETED",
            "entries": [
                {
                    "reason": recovery_request["reasons"][0],
                    "query": recovery_request["queries"][0]["query"],
                    "domain": "www.normattiva.it",
                    "uri": "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2013-03-14;33",
                    "source_type": "ISTITUZIONALE",
                    "coverage_status": "PARTIAL",
                    "vigenza_status": "CONFIRMED",
                    "rinvii_status": "RESOLVED",
                    "warnings": [],
                    "errors": [],
                    "blocks": [],
                }
            ],
        }

    result = orchestrate_documentary_runtime_slice(
        _classified_case(),
        handoff=_handoff,
        institutional_web_fetcher=_institutional_web_fetcher,
        timestamp="2026-03-21T10:00:00Z",
    )

    assert result["orchestrator_status"] == "DOCUMENTARY_DEGRADED"
    assert result["routing_output"]["routing_status"] == "PARTIAL"
    assert result["routing_output"]["rac_documentary_input_ref"]["documentary_only"] is True
    assert result["gate_output"]["documentary_channel"] == "FEDERATED_PLUS_INSTITUTIONAL_WEB"
    assert result["institutional_web_recovery"]["status"] == "COMPLETED"
    assert result["institutional_web_recovery"]["entries"][0]["domain"] == "www.normattiva.it"
