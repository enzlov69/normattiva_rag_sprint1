from __future__ import annotations

import json
from typing import Any, Dict, Set


ALLOWED_TOP_LEVEL_RESPONSE_FIELDS: Set[str] = {
    "response_id",
    "request_id",
    "source_level",
    "target_level",
    "response_kind",
    "documentary_status",
    "documentary_packet",
    "citations",
    "vigency_checks",
    "cross_references",
    "coverage_report",
    "warnings",
    "errors",
    "blocks",
    "m07_documentary_support",
    "audit",
    "shadow",
}

FORBIDDEN_TOP_LEVEL_RESPONSE_FIELDS: Set[str] = {
    "final_decision",
    "go_no_go",
    "firma_ready",
    "output_authorized",
    "final_opposability",
    "rac_final_outcome",
    "cf_atti_result",
    "m07_closed",
    "m07_completed",
    "m07_approved",
    "final_validation",
    "layer_atto_firma_ready",
    "output_layer_final",
}

ALLOWED_RESPONSE_KINDS = {
    "DOCUMENTARY_SUPPORT_RESPONSE",
}

ALLOWED_DOCUMENTARY_STATUS = {
    "DOCUMENTARY_OK",
    "DOCUMENTARY_WARNING",
    "DOCUMENTARY_BLOCKED",
}

ALLOWED_BLOCK_CODES = {
    "CRITICAL_DOCUMENTARY_BLOCK",
    "M07_DOCUMENTARY_INCOMPLETE",
    "COVERAGE_INSUFFICIENT",
    "CITATION_NOT_IDONEA",
    "VIGENCY_UNCERTAIN",
}


def build_valid_response_payload() -> Dict[str, Any]:
    return {
        "response_id": "RESP-ABA-0001",
        "request_id": "REQ-ABA-0001",
        "source_level": "LEVEL_B",
        "target_level": "LEVEL_A",
        "response_kind": "DOCUMENTARY_SUPPORT_RESPONSE",
        "documentary_status": "DOCUMENTARY_WARNING",
        "documentary_packet": {
            "sources_found": 4,
            "documentary_only": True,
            "contains_decision": False,
        },
        "citations": [
            {
                "source_type": "norma",
                "citation_text": "D.Lgs. 267/2000, art. 107",
                "official_source": True,
            },
            {
                "source_type": "norma",
                "citation_text": "L. 241/1990, art. 1",
                "official_source": True,
            },
        ],
        "vigency_checks": [
            {
                "source": "D.Lgs. 267/2000",
                "vigency_status": "TO_VERIFY_IN_CONTEXT",
            }
        ],
        "cross_references": [
            {
                "source": "D.Lgs. 267/2000, art. 107",
                "linked_to": "L. 241/1990",
            }
        ],
        "coverage_report": {
            "coverage_status": "PARTIAL",
            "missing_points": [
                "Verifica finale di completezza citazionale",
            ],
        },
        "warnings": [
            "Coverage documentale parziale: richiede governo del Livello A",
        ],
        "errors": [],
        "blocks": [
            {
                "code": "COVERAGE_INSUFFICIENT",
                "severity": "HIGH",
                "documentary_only": True,
            }
        ],
        "m07_documentary_support": {
            "support_provided": True,
            "documentary_only": True,
            "completion_declared": False,
        },
        "audit": {
            "trace_id": "TRACE-ABA-0001",
            "documentary_roundtrip": True,
        },
        "shadow": {
            "internal_use_only": True,
            "note": "Risposta documentale B->A",
        },
    }


def test_response_payload_uses_only_allowed_top_level_fields() -> None:
    payload = build_valid_response_payload()
    actual_fields = set(payload.keys())

    assert actual_fields.issubset(ALLOWED_TOP_LEVEL_RESPONSE_FIELDS), (
        f"Campi non ammessi nel payload B->A: {sorted(actual_fields - ALLOWED_TOP_LEVEL_RESPONSE_FIELDS)}"
    )


def test_response_payload_contains_no_forbidden_decisional_fields() -> None:
    payload = build_valid_response_payload()
    actual_fields = set(payload.keys())

    assert actual_fields.isdisjoint(FORBIDDEN_TOP_LEVEL_RESPONSE_FIELDS), (
        f"Campi decisori/conclusivi vietati nel payload B->A: "
        f"{sorted(actual_fields & FORBIDDEN_TOP_LEVEL_RESPONSE_FIELDS)}"
    )


def test_response_payload_has_correct_level_direction() -> None:
    payload = build_valid_response_payload()

    assert payload["source_level"] == "LEVEL_B"
    assert payload["target_level"] == "LEVEL_A"


def test_response_kind_is_documentary_only() -> None:
    payload = build_valid_response_payload()

    assert payload["response_kind"] in ALLOWED_RESPONSE_KINDS
    assert payload["documentary_packet"]["documentary_only"] is True
    assert payload["documentary_packet"]["contains_decision"] is False


def test_response_status_is_documentary_and_not_decisional() -> None:
    payload = build_valid_response_payload()

    assert payload["documentary_status"] in ALLOWED_DOCUMENTARY_STATUS


def test_response_payload_can_contain_warnings_errors_and_blocks_without_deciding() -> None:
    payload = build_valid_response_payload()

    assert isinstance(payload["warnings"], list)
    assert isinstance(payload["errors"], list)
    assert isinstance(payload["blocks"], list)
    assert len(payload["blocks"]) >= 1


def test_blocks_are_documentary_and_use_allowed_codes() -> None:
    payload = build_valid_response_payload()

    for block in payload["blocks"]:
        assert block["code"] in ALLOWED_BLOCK_CODES
        assert block["documentary_only"] is True


def test_response_payload_does_not_emit_go_no_go_or_firma_ready() -> None:
    payload = build_valid_response_payload()
    actual_fields = set(payload.keys())

    assert "go_no_go" not in actual_fields
    assert "firma_ready" not in actual_fields
    assert "output_authorized" not in actual_fields


def test_response_payload_does_not_close_m07() -> None:
    payload = build_valid_response_payload()
    m07 = payload["m07_documentary_support"]

    assert m07["support_provided"] is True
    assert m07["documentary_only"] is True
    assert m07["completion_declared"] is False

    actual_fields = set(payload.keys())
    assert "m07_closed" not in actual_fields
    assert "m07_completed" not in actual_fields
    assert "m07_approved" not in actual_fields


def test_response_payload_citations_and_vigency_checks_are_documentary_outputs() -> None:
    payload = build_valid_response_payload()

    assert len(payload["citations"]) >= 1
    assert len(payload["vigency_checks"]) >= 1

    for citation in payload["citations"]:
        assert citation["official_source"] is True


def test_response_payload_can_be_serialized_to_json() -> None:
    payload = build_valid_response_payload()
    serialized = json.dumps(payload, ensure_ascii=False)

    assert isinstance(serialized, str)
    assert '"source_level": "LEVEL_B"' in serialized
    assert '"target_level": "LEVEL_A"' in serialized


def test_response_payload_forbidden_field_example_is_detected() -> None:
    payload = build_valid_response_payload()
    payload["final_decision"] = "APPROVED"

    actual_fields = set(payload.keys())
    forbidden_found = actual_fields & FORBIDDEN_TOP_LEVEL_RESPONSE_FIELDS

    assert "final_decision" in forbidden_found


def test_response_payload_forbidden_m07_completion_example_is_detected() -> None:
    payload = build_valid_response_payload()
    payload["m07_completed"] = True

    actual_fields = set(payload.keys())
    forbidden_found = actual_fields & FORBIDDEN_TOP_LEVEL_RESPONSE_FIELDS

    assert "m07_completed" in forbidden_found