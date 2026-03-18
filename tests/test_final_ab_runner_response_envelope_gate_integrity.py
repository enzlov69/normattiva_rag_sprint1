from runtime.final_ab_response_envelope_gate import (
    FinalABResponseEnvelopeGate,
    STATUS_BLOCKED,
    STATUS_DEGRADED,
)


def _valid_envelope(status="SUCCESS"):
    return {
        "request_id": "req-002",
        "case_id": "case-002",
        "trace_id": "trace-002",
        "api_version": "1.0",
        "responder_module": "B21_ResponseMapper",
        "status": status,
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
                    "trace_id": "trace-002",
                    "executed_modules": ["B10_HybridRetriever", "B21_ResponseMapper"],
                },
            },
            "audit_fragment": {
                "trace_id": "trace-002",
                "event_type": "response_mapped",
            },
        },
    }


def test_reinstates_missing_critical_upstream_blocks():
    gate = FinalABResponseEnvelopeGate()
    envelope = _valid_envelope(status="SUCCESS")
    raw_validation = {
        "status": "BLOCKED",
        "blocks": [
            {
                "code": "CITATION_INCOMPLETE",
                "severity": "CRITICAL",
                "reason": "Critical citation missing uri_ufficiale",
            }
        ],
        "errors": [{"code": "RAW_CITATION_FAIL", "message": "citation invalid"}],
    }

    result = gate.validate(envelope, raw_validation_result=raw_validation)

    assert result["status"] == STATUS_BLOCKED
    assert any(block["code"] == "CITATION_INCOMPLETE" for block in result["blocks"])
    assert any(error["code"] == "CRITICAL_BLOCK_LOSS_DETECTED" for error in result["errors"])


def test_blocks_improper_status_downgrade_from_raw_validation():
    gate = FinalABResponseEnvelopeGate()
    envelope = _valid_envelope(status="DEGRADED")
    raw_validation = {
        "status": "REJECTED",
        "blocks": [
            {"code": "RAG_SCOPE_VIOLATION", "severity": "CRITICAL", "reason": "forbidden conclusory field"}
        ],
    }

    result = gate.validate(envelope, raw_validation_result=raw_validation)

    assert result["status"] == "REJECTED"
    assert any(error["code"] == "STATUS_DOWNGRADE_DETECTED" for error in result["errors"])


def test_marks_raw_validation_mismatch_as_blocking():
    gate = FinalABResponseEnvelopeGate()
    envelope = _valid_envelope(status="SUCCESS")
    raw_validation = {
        "status": "SUCCESS",
        "is_valid": False,
        "errors": [{"code": "RAW_SCHEMA_FAIL", "message": "raw schema invalid"}],
    }

    result = gate.validate(envelope, raw_validation_result=raw_validation)

    assert result["status"] == STATUS_BLOCKED
    assert any(error["code"] == "RAW_VALIDATION_MISMATCH" for error in result["errors"])


def test_degrades_when_errors_exist_without_critical_blocks():
    gate = FinalABResponseEnvelopeGate()
    envelope = _valid_envelope(status="SUCCESS")
    envelope["errors"] = [{"code": "NON_CRITICAL_MAPPING_GAP", "message": "optional metadata not mapped"}]

    result = gate.validate(envelope)

    assert result["status"] == STATUS_DEGRADED
