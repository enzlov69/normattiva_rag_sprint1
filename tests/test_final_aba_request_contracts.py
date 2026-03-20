from __future__ import annotations

import json
from typing import Any, Dict, Set


ALWAYS_ON_PRESIDIA = {
    "OP_ANTI_ALLUCINAZIONI_NORMATIVE",
    "OP_DOPPIA_LENTE_RATIO",
    "OP_COT++",
}

ALLOWED_TOP_LEVEL_REQUEST_FIELDS: Set[str] = {
    "request_id",
    "case_id",
    "source_level",
    "target_level",
    "request_kind",
    "source_phase",
    "method_context",
    "documentary_scope",
    "normative_scope",
    "local_regulation_scope",
    "risk_context",
    "active_presidia",
    "documentary_questions",
    "expected_documentary_outputs",
    "trace",
    "shadow",
}

FORBIDDEN_TOP_LEVEL_REQUEST_FIELDS: Set[str] = {
    "final_decision",
    "go_no_go",
    "firma_ready",
    "output_authorized",
    "final_opposability",
    "rac_final_outcome",
    "cf_atti_result",
    "m07_closed",
    "m07_completed",
    "final_validation",
    "output_layer_final",
}

ALLOWED_REQUEST_KINDS = {
    "DOCUMENTARY_SUPPORT_REQUEST",
}

ALLOWED_EXPECTED_DOCUMENTARY_OUTPUTS = {
    "sources",
    "citations",
    "vigency_checks",
    "cross_references",
    "coverage_report",
    "warnings",
    "errors",
    "blocks",
    "documentary_support_packet",
}

FORBIDDEN_EXPECTED_OUTPUTS = {
    "final_decision",
    "go_no_go",
    "firma_ready",
    "output_authorizer",
    "final_opposability",
    "m07_completion",
    "rac_final_outcome",
}


def build_valid_request_payload() -> Dict[str, Any]:
    return {
        "request_id": "REQ-ABA-0001",
        "case_id": "CASE-PPAV-0001",
        "source_level": "LEVEL_A",
        "target_level": "LEVEL_B",
        "request_kind": "DOCUMENTARY_SUPPORT_REQUEST",
        "source_phase": "S3",
        "method_context": {
            "method_name": "Metodo Cerda - PPAV 2.2",
            "roundtrip_mode": "A_TO_B_TO_A",
            "natura_output": "ATTO",
            "materia_prevalente": "SERVIZI_ALLA_PERSONA",
            "intensita_applicativa": "STANDARD",
        },
        "documentary_scope": {
            "objective": "Raccogliere supporto documentale su fonti, vigenza, rinvii e copertura",
            "must_return_documentary_only": True,
            "level_b_is_non_decisional": True,
        },
        "normative_scope": {
            "primary_sources": [
                "D.Lgs. 267/2000",
                "L. 241/1990",
            ],
            "need_vigency_check": True,
            "need_cross_reference_rebuild": True,
        },
        "local_regulation_scope": {
            "need_local_regulation_check": True,
            "regulations": [
                "Regolamento comunale pertinente",
            ],
        },
        "risk_context": {
            "initial_risk": "MEDIUM",
            "zone_rosse": ["M07", "OPPONIBILITA"],
            "fast_track": False,
        },
        "active_presidia": [
            "OP_ANTI_ALLUCINAZIONI_NORMATIVE",
            "OP_DOPPIA_LENTE_RATIO",
            "OP_COT++",
        ],
        "documentary_questions": [
            "Ricostruire le fonti pertinenti",
            "Verificare la vigenza delle fonti",
            "Ricostruire i rinvii normativi",
            "Segnalare coverage insufficiente o citazioni incomplete",
        ],
        "expected_documentary_outputs": [
            "sources",
            "citations",
            "vigency_checks",
            "cross_references",
            "coverage_report",
            "warnings",
            "errors",
            "blocks",
            "documentary_support_packet",
        ],
        "trace": {
            "origin_phase": "S3",
            "trace_id": "TRACE-ABA-0001",
        },
        "shadow": {
            "internal_use_only": True,
            "note": "Payload documentale controllato A->B",
        },
    }


def test_request_payload_uses_only_allowed_top_level_fields() -> None:
    payload = build_valid_request_payload()
    actual_fields = set(payload.keys())

    assert actual_fields.issubset(ALLOWED_TOP_LEVEL_REQUEST_FIELDS), (
        f"Campi non ammessi nel payload A->B: {sorted(actual_fields - ALLOWED_TOP_LEVEL_REQUEST_FIELDS)}"
    )


def test_request_payload_contains_no_forbidden_decisional_fields() -> None:
    payload = build_valid_request_payload()
    actual_fields = set(payload.keys())

    assert actual_fields.isdisjoint(FORBIDDEN_TOP_LEVEL_REQUEST_FIELDS), (
        f"Campi decisori/conclusivi vietati nel payload A->B: "
        f"{sorted(actual_fields & FORBIDDEN_TOP_LEVEL_REQUEST_FIELDS)}"
    )


def test_request_payload_has_correct_level_direction() -> None:
    payload = build_valid_request_payload()

    assert payload["source_level"] == "LEVEL_A"
    assert payload["target_level"] == "LEVEL_B"


def test_request_kind_is_documentary_only() -> None:
    payload = build_valid_request_payload()

    assert payload["request_kind"] in ALLOWED_REQUEST_KINDS


def test_request_payload_explicitly_marks_level_b_as_non_decisional() -> None:
    payload = build_valid_request_payload()

    assert payload["documentary_scope"]["must_return_documentary_only"] is True
    assert payload["documentary_scope"]["level_b_is_non_decisional"] is True


def test_request_payload_contains_always_on_presidia() -> None:
    payload = build_valid_request_payload()
    actual_presidia = set(payload["active_presidia"])

    assert ALWAYS_ON_PRESIDIA.issubset(actual_presidia), (
        f"Presidi trasversali mancanti nel payload A->B: "
        f"{sorted(ALWAYS_ON_PRESIDIA - actual_presidia)}"
    )


def test_expected_outputs_are_documentary_and_non_decisional() -> None:
    payload = build_valid_request_payload()
    expected_outputs = set(payload["expected_documentary_outputs"])

    assert expected_outputs.issubset(ALLOWED_EXPECTED_DOCUMENTARY_OUTPUTS), (
        f"Output attesi non documentali nel payload A->B: "
        f"{sorted(expected_outputs - ALLOWED_EXPECTED_DOCUMENTARY_OUTPUTS)}"
    )
    assert expected_outputs.isdisjoint(FORBIDDEN_EXPECTED_OUTPUTS), (
        f"Output attesi vietati nel payload A->B: "
        f"{sorted(expected_outputs & FORBIDDEN_EXPECTED_OUTPUTS)}"
    )


def test_request_payload_does_not_delegate_final_evaluation_to_level_b() -> None:
    payload = build_valid_request_payload()

    documentary_questions = " ".join(payload["documentary_questions"]).lower()
    forbidden_fragments = [
        "decidere",
        "validare",
        "autorizzare",
        "firma-ready",
        "go/no-go",
        "go no go",
        "opponibilità finale",
        "opponibilita finale",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in documentary_questions, (
            f"Il payload A->B non deve delegare a B attività conclusive: trovato frammento '{fragment}'"
        )


def test_request_payload_can_be_serialized_to_json() -> None:
    payload = build_valid_request_payload()
    serialized = json.dumps(payload, ensure_ascii=False)

    assert isinstance(serialized, str)
    assert '"source_level": "LEVEL_A"' in serialized
    assert '"target_level": "LEVEL_B"' in serialized


def test_request_payload_does_not_close_or_complete_m07() -> None:
    payload = build_valid_request_payload()
    actual_fields = set(payload.keys())

    assert "m07_closed" not in actual_fields
    assert "m07_completed" not in actual_fields


def test_request_payload_trace_and_shadow_are_internal_and_non_opposable() -> None:
    payload = build_valid_request_payload()

    assert payload["trace"]["origin_phase"] == "S3"
    assert payload["shadow"]["internal_use_only"] is True


def test_request_payload_forbidden_field_example_is_detected() -> None:
    payload = build_valid_request_payload()
    payload["firma_ready"] = True

    actual_fields = set(payload.keys())
    forbidden_found = actual_fields & FORBIDDEN_TOP_LEVEL_REQUEST_FIELDS

    assert "firma_ready" in forbidden_found