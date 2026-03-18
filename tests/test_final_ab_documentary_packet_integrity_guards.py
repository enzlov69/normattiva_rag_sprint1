from runtime.final_ab_response_envelope_gate import (
    FinalABResponseEnvelopeGate,
    STATUS_SUCCESS,
    STATUS_SUCCESS_WITH_WARNINGS,
)


def _minimal_envelope():
    return {
        "request_id": "req-int-001",
        "case_id": "case-int-001",
        "trace_id": "trace-int-001",
        "api_version": "1.0",
        "responder_module": "B21_ResponseMapper",
        "status": "SUCCESS",
        "timestamp": "2026-03-18T10:00:00Z",
        "warnings": [],
        "errors": [],
        "blocks": [],
        "payload": {
            "documentary_packet": {
                "sources": [],
                "norm_units": [],
                "citations_valid": [],
                "citations_blocked": [],
                "vigenza_records": [],
                "cross_reference_records": [],
                "coverage_assessment": {},
                "warnings": [],
                "errors": [],
                "blocks": [],
                "shadow_fragment": {
                    "trace_id": "trace-int-001",
                    "executed_modules": ["B21_ResponseMapper"],
                },
                "audit_fragment": {
                    "trace_id": "trace-int-001",
                    "event_type": "response_mapped",
                },
            }
        },
    }


def test_keeps_success_for_minimal_non_conclusive_documentary_packet():
    gate = FinalABResponseEnvelopeGate()
    envelope = _minimal_envelope()

    result = gate.validate(envelope)

    assert result["status"] == STATUS_SUCCESS
    assert result["errors"] == []
    assert result["blocks"] == []


def test_marks_warning_when_sources_are_weakly_traceable_but_not_materially_incoherent():
    gate = FinalABResponseEnvelopeGate()
    envelope = _minimal_envelope()
    envelope["payload"]["documentary_packet"]["sources"] = [{"label": "source-without-id"}]

    result = gate.validate(envelope)

    assert result["status"] == STATUS_SUCCESS_WITH_WARNINGS
    assert any(warning["code"] == "SOURCES_WEAK_TRACEABILITY" for warning in result["warnings"])


def test_marks_warning_when_norm_units_are_weakly_traceable_but_not_materially_incoherent():
    gate = FinalABResponseEnvelopeGate()
    envelope = _minimal_envelope()
    envelope["payload"]["documentary_packet"]["norm_units"] = [{"label": "nu-without-id"}]

    result = gate.validate(envelope)

    assert result["status"] == STATUS_SUCCESS_WITH_WARNINGS
    assert any(warning["code"] == "NORM_UNITS_WEAK_TRACEABILITY" for warning in result["warnings"])


def test_marks_warning_when_documentary_has_anchors_but_no_citations():
    gate = FinalABResponseEnvelopeGate()
    envelope = _minimal_envelope()
    envelope["payload"]["documentary_packet"]["sources"] = [{"source_id": "src-1"}]

    result = gate.validate(envelope)

    assert result["status"] == STATUS_SUCCESS_WITH_WARNINGS
    assert any(warning["code"] == "DOCUMENTARY_COMPLETENESS_WARNING" for warning in result["warnings"])
