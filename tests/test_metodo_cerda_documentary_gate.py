import json
from pathlib import Path

from runtime.metodo_cerda_documentary_gate import (
    build_not_required_gate_output,
    evaluate_documentary_gate,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "level_b_payloads"


def _classified_case(**overrides):
    payload = {
        "request_id": "REQ-A1TER-GATE-001",
        "case_id": "CASE-A1TER-GATE-001",
        "trace_id": "TRACE-A1TER-GATE-001",
        "sensibilita": "MEDIA",
        "intensita_applicativa": "MEDIA",
        "moduli_attivati": ["M07-LPR", "RAC"],
    }
    payload.update(overrides)
    return payload


def _load_fixture(*parts):
    with (FIXTURES / Path(*parts)).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_gate_returns_proceed_for_valid_response():
    response = _load_fixture("pass", "basic_success.json")

    result = evaluate_documentary_gate(_classified_case(), response)

    assert result["gate_status"] == "PROCEED"
    assert result["forbidden_field_detected"] is False
    assert result["packet_complete"] is True
    assert result["documentary_channel"] == "FEDERATED_ONLY"
    assert result["institutional_web_required"] is False
    assert "M07_SUPPORT" in result["allowed_routes"]


def test_gate_returns_degrade_when_response_has_warning():
    response = _load_fixture("degrade", "coverage_degraded.json")

    result = evaluate_documentary_gate(_classified_case(), response)

    assert result["gate_status"] == "DEGRADE"
    assert "LEVEL_B_WARNINGS_PRESENT" in result["degradation_reasons"]


def test_gate_returns_block_when_critical_block_is_present():
    response = _load_fixture("degrade", "coverage_degraded.json")
    response["blocks"][0]["block_code"] = "COVERAGE_INADEQUATE"

    result = evaluate_documentary_gate(
        _classified_case(intensita_applicativa="ALTA"),
        response,
    )

    assert result["gate_status"] == "BLOCK"
    assert "COVERAGE_INADEQUATE" in result["critical_blocks"]


def test_gate_returns_block_when_forbidden_fields_are_present():
    response = _load_fixture("reject", "m07_closed_true.json")

    result = evaluate_documentary_gate(_classified_case(), response)

    assert result["gate_status"] == "BLOCK"
    assert result["forbidden_field_detected"] is True
    assert "RAG_SCOPE_VIOLATION" in result["critical_blocks"]


def test_gate_returns_block_when_packet_is_critically_incomplete():
    response = _load_fixture("pass", "basic_success.json")
    del response["payload"]["shadow"]

    result = evaluate_documentary_gate(_classified_case(), response)

    assert result["gate_status"] == "BLOCK"
    assert "AUDIT_INCOMPLETE" in result["critical_blocks"]


def test_gate_can_emit_not_required_without_level_b_call():
    result = build_not_required_gate_output(_classified_case())

    assert result["gate_status"] == "NOT_REQUIRED"
    assert result["allowed_routes"] == []


def test_gate_keeps_federated_only_when_official_uri_is_already_verified():
    response = _load_fixture("pass", "basic_success.json")
    response["payload"]["citations_valid"][0]["uri_ufficiale"] = (
        "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2000-08-18;267"
    )

    result = evaluate_documentary_gate(_classified_case(), response)

    assert result["documentary_channel"] == "FEDERATED_ONLY"
    assert result["institutional_web_required"] is False
