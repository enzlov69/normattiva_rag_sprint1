from runtime.metodo_cerda_documentary_gate import evaluate_documentary_gate
from runtime.metodo_cerda_documentary_router import route_documentary_support


def _classified_case():
    return {
        "request_id": "REQ-A1TER-M07-001",
        "case_id": "CASE-A1TER-M07-001",
        "trace_id": "TRACE-A1TER-M07-001",
        "sensibilita": "MEDIA",
        "intensita_applicativa": "MEDIA",
        "moduli_attivati": ["M07-LPR"],
    }


def test_m07_forbidden_names_produce_block():
    response = {
        "status": "SUCCESS",
        "warnings": [],
        "errors": [],
        "blocks": [],
        "payload": {
            "documentary_packet": {
                "sources": [{"source_id": "src_1"}],
                "normative_units": [{"norm_unit_id": "art_1"}],
                "citations": [{"citation_id": "cit_1"}],
                "incomplete_citations": [],
                "coverage": {"coverage_status": "ADEQUATE", "critical_gap_flag": False},
                "vigenza_status": "CONFIRMED",
                "rinvii_status": "RESOLVED",
                "audit": {"events_present": True},
                "shadow": {"executed_modules": ["B16_M07SupportLayer"]},
                "m07_support": {"m07_closed": True},
            }
        },
    }

    result = evaluate_documentary_gate(_classified_case(), response)

    assert result["gate_status"] == "BLOCK"
    assert result["forbidden_field_detected"] is True


def test_router_forces_human_completion_required_in_m07_pack():
    gate_output = {
        "request_id": "REQ-A1TER-M07-001",
        "case_id": "CASE-A1TER-M07-001",
        "trace_id": "TRACE-A1TER-M07-001",
        "gate_status": "PROCEED",
        "allowed_routes": ["M07_SUPPORT", "FASCICOLO_SUPPORT", "AUDIT_UPDATE", "SHADOW_UPDATE"],
        "warning_flags": [],
        "critical_blocks": [],
    }
    response = {
        "payload": {
            "documentary_packet": {
                "sources": [{"source_id": "src_1"}],
                "normative_units": [{"norm_unit_id": "art_1"}],
                "citations": [{"citation_id": "cit_1"}],
                "coverage": {"coverage_status": "ADEQUATE", "critical_gap_flag": False},
                "vigenza_status": "CONFIRMED",
                "rinvii_status": "RESOLVED",
                "m07_support": {"ordered_reading_sequence": ["art_1"]},
            }
        }
    }

    result = route_documentary_support(_classified_case(), gate_output, response)

    assert result["m07_evidence_pack_ref"]["human_completion_required"] is True
    assert "m07_closed" not in result["m07_evidence_pack_ref"]
