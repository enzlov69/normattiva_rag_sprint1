from __future__ import annotations

from runtime.final_aba_runtime_handoff_service import perform_runtime_roundtrip


def build_real_case_request() -> dict:
    return {
        "request_id": "REQ-REAL-10BIS-0003",
        "case_id": "CASE-REAL-10BIS-0003",
        "trace_id": "TRACE-REAL-10BIS-0003",
        "source_level": "LEVEL_A",
        "target_level": "LEVEL_B",
        "request_kind": "DOCUMENTARY_SUPPORT_REQUEST",
        "source_phase": "S3",
        "documentary_scope": {
            "must_return_documentary_only": True,
            "level_b_is_non_decisional": True,
            "objective": (
                "Ricostruire il perimetro documentale ufficiale del preavviso di "
                "rigetto ex art. 10-bis L. 241/1990, con focus su motivi ostativi, "
                "termini per osservazioni del privato, documentazione integrativa, "
                "rinvii normativi, fascicolo e tracciabilità, senza valutazione "
                "finale del merito delle osservazioni."
            ),
        },
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
            "m07_documentary_support",
        ],
        "active_presidia": [
            "OP_ANTI_ALLUCINAZIONI_NORMATIVE",
            "OP_DOPPIA_LENTE_RATIO",
            "OP_COT++",
        ],
        "audit": {
            "created_by": "LEVEL_A_RUNTIME",
            "internal_only": True,
        },
        "shadow": {
            "internal_use_only": True,
            "note": "Caso reale n. 3 - preavviso di rigetto con osservazioni del privato",
        },
    }


def build_real_case_response_degraded() -> dict:
    return {
        "response_id": "RESP-REAL-10BIS-0003",
        "request_id": "REQ-REAL-10BIS-0003",
        "source_level": "LEVEL_B",
        "target_level": "LEVEL_A",
        "response_kind": "DOCUMENTARY_SUPPORT_RESPONSE",
        "documentary_status": "DOCUMENTARY_WARNING",
        "documentary_packet": {
            "documentary_only": True,
            "contains_decision": False,
            "packet_title": "Supporto documentale su preavviso di rigetto e osservazioni del privato",
        },
        "citations": [
            {
                "source_type": "norma",
                "citation_text": "Legge 7 agosto 1990, n. 241, art. 2",
                "official_source": True,
            },
            {
                "source_type": "norma",
                "citation_text": "Legge 7 agosto 1990, n. 241, art. 7",
                "official_source": True,
            },
            {
                "source_type": "norma",
                "citation_text": "Legge 7 agosto 1990, n. 241, art. 8",
                "official_source": True,
            },
            {
                "source_type": "norma",
                "citation_text": "Legge 7 agosto 1990, n. 241, art. 10-bis",
                "official_source": True,
            },
            {
                "source_type": "norma",
                "citation_text": "Legge 7 agosto 1990, n. 241, art. 21-octies",
                "official_source": True,
            },
        ],
        "vigency_checks": [
            {
                "source": "L. 241/1990, artt. 2, 7, 8, 10-bis, 21-octies",
                "vigency_status": "TO_VERIFY_IN_CONTEXT",
            }
        ],
        "cross_references": [
            {
                "source": "L. 241/1990, art. 10-bis",
                "linked_to": "L. 241/1990, art. 2",
            },
            {
                "source": "L. 241/1990, art. 10-bis",
                "linked_to": "L. 241/1990, art. 21-octies",
            },
            {
                "source": "Preavviso di rigetto",
                "linked_to": "Osservazioni del privato",
            },
        ],
        "coverage_report": {
            "coverage_status": "PARTIAL",
            "missing_points": [
                "verifica regolamento comunale su contributi e criteri di ammissibilità",
                "verifica modulistica o disciplina interna delle integrazioni documentali",
                "valutazione finale del merito delle osservazioni riservata al Livello A",
            ],
        },
        "warnings": [
            "Coverage documentale parziale sul livello regolamentare e sui criteri interni di valutazione.",
            "Il merito delle osservazioni del privato resta riservato al Livello A.",
        ],
        "errors": [],
        "blocks": [
            {
                "code": "COVERAGE_INSUFFICIENT",
                "severity": "MEDIUM",
                "documentary_only": True,
            }
        ],
        "m07_documentary_support": {
            "support_provided": True,
            "documentary_only": True,
            "completion_declared": False,
        },
        "audit": {
            "created_by": "LEVEL_B_RUNTIME",
            "internal_only": True,
        },
        "shadow": {
            "internal_use_only": True,
        },
    }


def build_real_case_response_blocked_m07() -> dict:
    response = build_real_case_response_degraded()
    response["documentary_status"] = "DOCUMENTARY_BLOCKED"
    response["blocks"] = [
        {
            "code": "M07_DOCUMENTARY_INCOMPLETE",
            "severity": "HIGH",
            "documentary_only": True,
        }
    ]
    response["coverage_report"] = {"coverage_status": "PARTIAL"}
    response["warnings"] = ["Supporto documentale non sufficiente per M07 sul preavviso di rigetto."]
    return response


def build_real_case_response_invalid_overreach_m07() -> dict:
    response = build_real_case_response_degraded()
    response["m07_documentary_support"]["completion_declared"] = True
    response["documentary_status"] = "DOCUMENTARY_OK"
    response["blocks"] = []
    response["coverage_report"] = {"coverage_status": "FULL"}
    response["warnings"] = []
    return response


def build_real_case_response_invalid_decision_field() -> dict:
    response = build_real_case_response_degraded()
    response["final_decision"] = "RIGETTO_CONFERMATO"
    return response


def build_real_case_response_invalid_merit_evaluation() -> dict:
    response = build_real_case_response_degraded()
    response["go_no_go"] = "GO"
    return response


def test_real_case_10bis_roundtrip_is_degraded_but_valid() -> None:
    request = build_real_case_request()

    def invoker(_: dict) -> dict:
        return build_real_case_response_degraded()

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "ROUNDTRIP_DEGRADED"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is True
    assert result["internal_envelope"] is not None
    assert result["internal_envelope"]["case_id"] == "CASE-REAL-10BIS-0003"
    assert result["internal_envelope"]["trace_id"] == "TRACE-REAL-10BIS-0003"
    assert result["internal_envelope"]["degrading_block_present"] is True
    assert result["internal_envelope"]["critical_block_present"] is False
    assert "COVERAGE_INSUFFICIENT" in result["internal_envelope"]["block_codes_received"]
    assert result["internal_envelope"]["can_emit_go_no_go"] is False
    assert result["internal_envelope"]["can_emit_firma_ready"] is False
    assert result["internal_envelope"]["can_authorize_output"] is False


def test_real_case_10bis_m07_incomplete_blocks_roundtrip() -> None:
    request = build_real_case_request()

    def invoker(_: dict) -> dict:
        return build_real_case_response_blocked_m07()

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "ROUNDTRIP_BLOCKED"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is True
    assert result["internal_envelope"] is not None
    assert result["internal_envelope"]["critical_block_present"] is True
    assert "M07_DOCUMENTARY_INCOMPLETE" in result["internal_envelope"]["block_codes_received"]
    assert result["internal_envelope"]["runtime_status"] == "ROUNDTRIP_BLOCKED"


def test_real_case_10bis_rejects_level_b_m07_overreach() -> None:
    request = build_real_case_request()

    def invoker(_: dict) -> dict:
        return build_real_case_response_invalid_overreach_m07()

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "RESPONSE_INVALID"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is False
    assert any(
        "Level B cannot declare m07 completion" in error
        for error in result["response_validation"]["errors"]
    )
    assert result["internal_envelope"] is None


def test_real_case_10bis_rejects_decisional_field_in_response() -> None:
    request = build_real_case_request()

    def invoker(_: dict) -> dict:
        return build_real_case_response_invalid_decision_field()

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "RESPONSE_INVALID"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is False
    assert any(
        "Forbidden response fields present" in error
        for error in result["response_validation"]["errors"]
    )
    assert result["internal_envelope"] is None


def test_real_case_10bis_rejects_merit_evaluation_by_level_b() -> None:
    request = build_real_case_request()

    def invoker(_: dict) -> dict:
        return build_real_case_response_invalid_merit_evaluation()

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "RESPONSE_INVALID"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is False
    assert any(
        "Forbidden response fields present" in error
        for error in result["response_validation"]["errors"]
    )
    assert result["internal_envelope"] is None


def test_real_case_10bis_request_stays_non_decisional() -> None:
    request = build_real_case_request()

    assert request["source_level"] == "LEVEL_A"
    assert request["target_level"] == "LEVEL_B"
    assert request["request_kind"] == "DOCUMENTARY_SUPPORT_REQUEST"
    assert request["documentary_scope"]["must_return_documentary_only"] is True
    assert request["documentary_scope"]["level_b_is_non_decisional"] is True
    assert "go_no_go" not in request
    assert "firma_ready" not in request
    assert "final_decision" not in request