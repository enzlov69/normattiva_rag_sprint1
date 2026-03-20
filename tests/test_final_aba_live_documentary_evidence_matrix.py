from __future__ import annotations

from runtime.federated_runner_live_transport import (
    append_documentary_evidence_matrix,
    build_documentary_evidence_matrix,
    redact_endpoint,
)


def test_documentary_evidence_matrix_marks_coverage_vigenza_and_rinvii_risks():
    matrix = build_documentary_evidence_matrix(
        {
            "sources": [{"id": "S1"}],
            "normative_units": [{"id": "N1"}],
            "citations": [{"id": "C1"}],
            "incomplete_citations": [{"id": "IC1"}],
            "vigenza_status": "UNCERTAIN",
            "rinvii_status": "UNRESOLVED",
            "coverage": "INADEQUATE",
        }
    )

    assert matrix["coverage"]["adequate"] is False
    assert matrix["vigenza"]["confirmed"] is False
    assert matrix["rinvii"]["resolved"] is False
    assert "COVERAGE_NOT_ADEQUATE" in matrix["blocking_reasons"]
    assert "VIGENZA_NOT_CONFIRMED" in matrix["blocking_reasons"]
    assert "RINVII_NOT_RESOLVED" in matrix["blocking_reasons"]
    assert "INCOMPLETE_CITATIONS_PRESENT" in matrix["blocking_reasons"]
    assert matrix["non_opponible_outside_level_a"] is True


def test_append_documentary_evidence_matrix_enriches_envelope_without_creating_opponibility():
    envelope = {
        "status": "OK",
        "warnings": [],
        "errors": [],
        "blocks": [],
        "payload": {
            "documentary_packet": {
                "sources": [{"id": "S1"}],
                "normative_units": [{"id": "N1"}],
                "citations": [{"id": "C1"}],
                "incomplete_citations": [],
                "vigenza_status": "CONFIRMED",
                "rinvii_status": "RESOLVED",
                "coverage": "ADEQUATE",
            }
        },
        "audit": {"trail_events": []},
        "shadow": {"fragments": []},
    }

    enriched = append_documentary_evidence_matrix(envelope)

    assert enriched["payload"]["documentary_evidence_matrix"]["coverage"]["status"] == "ADEQUATE"
    assert enriched["payload"]["non_opponibility"]["outside_level_a"] is True
    assert enriched["audit"]["trail_events"][-1]["event"] == "documentary_evidence_matrix_built"
    assert enriched["shadow"]["fragments"][-1]["kind"] == "documentary_evidence_matrix"


def test_redact_endpoint_keeps_scheme_host_and_path_only():
    redacted = redact_endpoint(
        "https://api.example.org/federated/run?token=secret&debug=1"
    )
    assert redacted == "https://api.example.org/federated/run"
