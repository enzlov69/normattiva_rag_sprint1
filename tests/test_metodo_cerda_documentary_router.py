from runtime.metodo_cerda_documentary_router import route_documentary_support


def _classified_case(**overrides):
    payload = {
        "request_id": "REQ-A1TER-ROUTER-001",
        "case_id": "CASE-A1TER-ROUTER-001",
        "trace_id": "TRACE-A1TER-ROUTER-001",
        "moduli_attivati": ["M07-LPR", "RAC", "PPAV_ISTRUTTORIA"],
    }
    payload.update(overrides)
    return payload


def _gate_output(status="PROCEED", routes=None):
    return {
        "request_id": "REQ-A1TER-ROUTER-001",
        "case_id": "CASE-A1TER-ROUTER-001",
        "trace_id": "TRACE-A1TER-ROUTER-001",
        "gate_status": status,
        "allowed_routes": routes or [
            "M07_SUPPORT",
            "RAC_SUPPORT",
            "PPAV_SUPPORT",
            "FASCICOLO_SUPPORT",
            "AUDIT_UPDATE",
            "SHADOW_UPDATE",
        ],
        "warning_flags": [],
        "critical_blocks": [],
    }


def _response_envelope():
    return {
        "payload": {
            "documentary_packet": {
                "sources": [{"source_id": "src_1"}],
                "normative_units": [{"norm_unit_id": "art_1"}],
                "citations": [{"citation_id": "cit_1"}],
                "coverage": {"coverage_status": "ADEQUATE", "critical_gap_flag": False},
                "vigenza_status": "CONFIRMED",
                "rinvii_status": "RESOLVED",
                "m07_support": {
                    "ordered_reading_sequence": ["art_1", "art_2"],
                    "annex_refs": [],
                    "crossref_refs": [],
                    "missing_elements": [],
                    "m07_support_status": "SUPPORT_READY",
                },
            }
        }
    }


def test_router_routes_to_m07_support():
    result = route_documentary_support(
        _classified_case(moduli_attivati=["M07-LPR"]),
        _gate_output(routes=["M07_SUPPORT", "FASCICOLO_SUPPORT", "AUDIT_UPDATE", "SHADOW_UPDATE"]),
        _response_envelope(),
    )

    assert result["routing_status"] == "ROUTED"
    assert result["m07_evidence_pack_ref"]["human_completion_required"] is True
    assert "m07_closed" not in result["m07_evidence_pack_ref"]
    assert result["documentary_channel"] == "FEDERATED_ONLY"


def test_router_routes_to_rac_support():
    result = route_documentary_support(
        _classified_case(moduli_attivati=["RAC"]),
        _gate_output(routes=["RAC_SUPPORT", "FASCICOLO_SUPPORT", "AUDIT_UPDATE", "SHADOW_UPDATE"]),
        _response_envelope(),
    )

    assert result["routing_status"] == "ROUTED"
    assert result["rac_documentary_input_ref"]["documentary_only"] is True
    assert "final_applicability" not in result["rac_documentary_input_ref"]


def test_router_handles_multi_destination_routing():
    result = route_documentary_support(
        _classified_case(),
        _gate_output(),
        _response_envelope(),
    )

    assert result["routing_status"] == "ROUTED"
    assert "M07_SUPPORT" in result["destinations"]
    assert "RAC_SUPPORT" in result["destinations"]
    assert "PPAV_SUPPORT" in result["destinations"]


def test_router_traces_institutional_web_recovery_when_present():
    gate_output = _gate_output()
    gate_output["documentary_channel"] = "FEDERATED_PLUS_INSTITUTIONAL_WEB"
    result = route_documentary_support(
        _classified_case(),
        gate_output,
        _response_envelope(),
        institutional_web_recovery={
            "status": "COMPLETED",
            "entries": [
                {
                    "reason": "OFFICIAL_SOURCE_CONFIRMATION_PENDING",
                    "query": "art. 107 TUEL",
                    "domain": "www.normattiva.it",
                    "uri": "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2000-08-18;267",
                    "source_type": "ISTITUZIONALE",
                }
            ],
        },
    )

    assert result["documentary_channel"] == "FEDERATED_PLUS_INSTITUTIONAL_WEB"
    assert result["institutional_web_refs"][0]["domain"] == "www.normattiva.it"


def test_router_blocks_routing_when_gate_is_block():
    result = route_documentary_support(
        _classified_case(),
        _gate_output(status="BLOCK", routes=[]),
        _response_envelope(),
    )

    assert result["routing_status"] == "BLOCKED"
    assert result["destinations"] == []


def test_router_skips_routing_when_gate_is_not_required():
    result = route_documentary_support(
        _classified_case(),
        _gate_output(status="NOT_REQUIRED", routes=[]),
        _response_envelope(),
    )

    assert result["routing_status"] == "SKIPPED"
    assert result["destinations"] == []
