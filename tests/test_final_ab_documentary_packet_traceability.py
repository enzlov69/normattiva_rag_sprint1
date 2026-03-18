from runtime.final_ab_response_envelope_gate import FinalABResponseEnvelopeGate, STATUS_BLOCKED


def _base_envelope():
    return {
        "request_id": "req-trace-001",
        "case_id": "case-trace-001",
        "trace_id": "trace-trace-001",
        "api_version": "1.0",
        "responder_module": "B21_ResponseMapper",
        "status": "SUCCESS",
        "timestamp": "2026-03-18T10:00:00Z",
        "warnings": [],
        "errors": [],
        "blocks": [],
        "payload": {
            "documentary_packet": {
                "sources": [{"source_id": "src-1", "uri": "https://example.test/src-1"}],
                "norm_units": [{"norm_unit_id": "nu-1", "article": "107"}],
                "citations_valid": [{"citation_id": "cit-1", "source_id": "src-1", "norm_unit_id": "nu-1"}],
                "citations_blocked": [],
                "vigenza_records": [],
                "cross_reference_records": [],
                "coverage_assessment": {"status": "ADEQUATE"},
                "warnings": [],
                "errors": [],
                "blocks": [],
                "shadow_fragment": {
                    "trace_id": "trace-trace-001",
                    "executed_modules": ["B21_ResponseMapper"],
                },
                "audit_fragment": {
                    "trace_id": "trace-trace-001",
                    "event_type": "response_mapped",
                },
            }
        },
    }


def test_blocks_when_citation_has_no_traceability_anchor():
    gate = FinalABResponseEnvelopeGate()
    envelope = _base_envelope()
    envelope["payload"]["documentary_packet"]["citations_valid"] = [{"note": "missing anchors"}]

    result = gate.validate(envelope)

    assert result["status"] == STATUS_BLOCKED
    assert any(error["code"] == "CITATION_TRACEABILITY_MISSING" for error in result["errors"])
    assert any(block["code"] == "CITATION_INCOMPLETE" for block in result["blocks"])


def test_blocks_when_citation_source_link_has_no_coverage_match():
    gate = FinalABResponseEnvelopeGate()
    envelope = _base_envelope()
    envelope["payload"]["documentary_packet"]["citations_valid"] = [
        {"citation_id": "cit-x", "source_id": "src-x", "norm_unit_id": "nu-1"}
    ]

    result = gate.validate(envelope)

    assert result["status"] == STATUS_BLOCKED
    assert any(error["code"] == "CITATION_SOURCE_LINK_MISSING" for error in result["errors"])
    assert any(block["code"] == "CROSSREF_UNRESOLVED" for block in result["blocks"])


def test_blocks_when_coverage_is_adequate_but_sources_are_empty():
    gate = FinalABResponseEnvelopeGate()
    envelope = _base_envelope()
    envelope["payload"]["documentary_packet"]["sources"] = []
    envelope["payload"]["documentary_packet"]["coverage_assessment"] = {"status": "ADEQUATE"}

    result = gate.validate(envelope)

    assert result["status"] == STATUS_BLOCKED
    assert any(error["code"] == "DOCUMENTARY_SOURCES_MISSING" for error in result["errors"])
    assert any(block["code"] == "SOURCE_UNVERIFIED" for block in result["blocks"])


def test_blocks_when_shadow_trace_id_mismatches_envelope_trace_id():
    gate = FinalABResponseEnvelopeGate()
    envelope = _base_envelope()
    envelope["payload"]["documentary_packet"]["shadow_fragment"]["trace_id"] = "trace-other"

    result = gate.validate(envelope)

    assert result["status"] == STATUS_BLOCKED
    assert any(error["code"] == "TRACEABILITY_SHADOW_MISMATCH" for error in result["errors"])
    assert any(block["code"] == "AUDIT_INCOMPLETE" for block in result["blocks"])
