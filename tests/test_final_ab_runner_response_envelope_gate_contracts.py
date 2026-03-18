from runtime.final_ab_response_envelope_gate import (
    FinalABResponseEnvelopeGate,
    STATUS_BLOCKED,
    STATUS_REJECTED,
)


def _valid_envelope():
    return {
        "request_id": "req-001",
        "case_id": "case-001",
        "trace_id": "trace-001",
        "api_version": "1.0",
        "responder_module": "B21_ResponseMapper",
        "status": "SUCCESS",
        "timestamp": "2026-03-18T10:00:00Z",
        "warnings": [],
        "errors": [],
        "blocks": [],
        "payload": {
            "documentary_packet": {
                "sources": [{"source_id": "src-1"}],
                "norm_units": [{"norm_unit_id": "nu-1"}],
                "citations_valid": [{"citation_id": "cit-1"}],
                "citations_blocked": [],
                "vigenza_records": [{"vigenza_id": "vig-1"}],
                "cross_reference_records": [],
                "coverage_assessment": {"coverage_id": "cov-1"},
                "warnings": [],
                "errors": [],
                "blocks": [],
                "shadow_fragment": {
                    "trace_id": "trace-001",
                    "executed_modules": ["B10_HybridRetriever", "B21_ResponseMapper"],
                },
                "audit_fragment": {
                    "trace_id": "trace-001",
                    "event_type": "response_mapped",
                },
            }
        },
    }


def test_blocks_incomplete_final_envelope():
    gate = FinalABResponseEnvelopeGate()
    envelope = _valid_envelope()
    envelope.pop("timestamp")

    result = gate.validate(envelope)

    assert result["status"] == STATUS_BLOCKED
    assert any(error["code"] == "FINAL_ENVELOPE_INCOMPLETE" for error in result["errors"])
    assert any(block["code"] == "OUTPUT_NOT_OPPONIBLE" for block in result["blocks"])


def test_rejects_forbidden_fields_reappearing_in_final_payload():
    gate = FinalABResponseEnvelopeGate()
    envelope = _valid_envelope()
    envelope["payload"]["documentary_packet"]["output_authorized"] = True

    result = gate.validate(envelope)

    assert result["status"] == STATUS_REJECTED
    assert any(error["code"] == "FORBIDDEN_LEVEL_B_FIELDS_PRESENT" for error in result["errors"])
    assert any(block["code"] == "RAG_SCOPE_VIOLATION" for block in result["blocks"])


def test_blocks_incomplete_documentary_packet():
    gate = FinalABResponseEnvelopeGate()
    envelope = _valid_envelope()
    del envelope["payload"]["documentary_packet"]["coverage_assessment"]

    result = gate.validate(envelope)

    assert result["status"] == STATUS_BLOCKED
    assert any(error["code"] == "DOCUMENTARY_PACKET_INCOMPLETE" for error in result["errors"])
    assert any(block["code"] == "OUTPUT_NOT_OPPONIBLE" for block in result["blocks"])
