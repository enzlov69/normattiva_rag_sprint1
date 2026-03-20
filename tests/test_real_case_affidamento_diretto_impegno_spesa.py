from __future__ import annotations

from runtime.final_aba_runtime_handoff_service import perform_runtime_roundtrip


def build_real_case_request() -> dict:
    return {
        "request_id": "REQ-REAL-AFFIDAMENTO-0004",
        "case_id": "CASE-REAL-AFFIDAMENTO-0004",
        "trace_id": "TRACE-REAL-AFFIDAMENTO-0004",
        "source_level": "LEVEL_A",
        "target_level": "LEVEL_B",
        "request_kind": "DOCUMENTARY_SUPPORT_REQUEST",
        "source_phase": "S3",
        "documentary_scope": {
            "must_return_documentary_only": True,
            "level_b_is_non_decisional": True,
            "objective": (
                "Ricostruire il perimetro documentale ufficiale dell'affidamento "
                "diretto di servizio per evento istituzionale/culturale con "
                "contestuale impegno di spesa, con focus su affidamento diretto, "
                "atto di affidamento, elementi istruttori minimi, presupposti "
                "dell'impegno, copertura finanziaria, tracciabilità e fascicolo, "
                "senza valutazione finale di legittimità o firma-ready."
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
            "note": "Caso reale n. 4 - affidamento diretto con impegno di spesa",
        },
    }


def build_real_case_response_degraded() -> dict:
    return {
        "response_id": "RESP-REAL-AFFIDAMENTO-0004",
        "request_id": "REQ-REAL-AFFIDAMENTO-0004",
        "source_level": "LEVEL_B",
        "target_level": "LEVEL_A",
        "response_kind": "DOCUMENTARY_SUPPORT_RESPONSE",
        "documentary_status": "DOCUMENTARY_WARNING",
        "documentary_packet": {
            "documentary_only": True,
            "contains_decision": False,
            "packet_title": "Supporto documentale su affidamento diretto e impegno di spesa",
        },
        "citations": [
            {
                "source_type": "norma",
                "citation_text": "D.Lgs. 31 marzo 2023, n. 36, art. 17",
                "official_source": True,
            },
            {
                "source_type": "norma",
                "citation_text": "D.Lgs. 31 marzo 2023, n. 36, art. 50",
                "official_source": True,
            },
            {
                "source_type": "norma",
                "citation_text": "D.Lgs. 18 agosto 2000, n. 267, art. 183",
                "official_source": True,
            },
            {
                "source_type": "norma",
                "citation_text": "D.Lgs. 18 agosto 2000, n. 267, art. 191",
                "official_source": True,
            },
            {
                "source_type": "norma",
                "citation_text": "D.Lgs. 18 agosto 2000, n. 267, art. 192",
                "official_source": True,
            },
            {
                "source_type": "norma",
                "citation_text": "D.Lgs. 18 agosto 2000, n. 267, art. 147-bis",
                "official_source": True,
            },
        ],
        "vigency_checks": [
            {
                "source": "D.Lgs. 36/2023, artt. 17 e 50",
                "vigency_status": "TO_VERIFY_IN_CONTEXT",
            },
            {
                "source": "D.Lgs. 267/2000, artt. 183, 191, 192, 147-bis",
                "vigency_status": "TO_VERIFY_IN_CONTEXT",
            },
        ],
        "cross_references": [
            {
                "source": "D.Lgs. 36/2023, art. 17",
                "linked_to": "D.Lgs. 36/2023, art. 50",
            },
            {
                "source": "Affidamento diretto",
                "linked_to": "TUEL, art. 192",
            },
            {
                "source": "Impegno di spesa",
                "linked_to": "TUEL, artt. 183 e 191",
            },
            {
                "source": "Determinazione gestionale",
                "linked_to": "TUEL, art. 147-bis",
            },
        ],
        "coverage_report": {
            "coverage_status": "PARTIAL",
            "missing_points": [
                "verifica disponibilità puntuale capitolo e prenotazione/impegno",
                "verifica tracciabilità CIG/CUP se pertinenti",
                "verifica istruttoria sulla scelta dell'operatore economico",
                "contestualizzazione finale dell'obbligazione giuridicamente perfezionata riservata al Livello A",
            ],
        },
        "warnings": [
            "Coverage documentale parziale sul lato contabile e sulla tracciabilità operativa.",
            "La verifica finale dell'obbligazione perfezionata e della copertura resta riservata al Livello A.",
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
    response["warnings"] = [
        "Supporto documentale non sufficiente per M07 su affidamento diretto e impegno."
    ]
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
    response["final_decision"] = "AFFIDAMENTO_AMMISSIBILE"
    return response


def build_real_case_response_invalid_firma_ready() -> dict:
    response = build_real_case_response_degraded()
    response["firma_ready"] = True
    return response


def test_real_case_affidamento_diretto_impegno_roundtrip_is_degraded_but_valid() -> None:
    request = build_real_case_request()

    def invoker(_: dict) -> dict:
        return build_real_case_response_degraded()

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "ROUNDTRIP_DEGRADED"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is True
    assert result["internal_envelope"] is not None
    assert result["internal_envelope"]["case_id"] == "CASE-REAL-AFFIDAMENTO-0004"
    assert result["internal_envelope"]["trace_id"] == "TRACE-REAL-AFFIDAMENTO-0004"
    assert result["internal_envelope"]["degrading_block_present"] is True
    assert result["internal_envelope"]["critical_block_present"] is False
    assert "COVERAGE_INSUFFICIENT" in result["internal_envelope"]["block_codes_received"]
    assert result["internal_envelope"]["can_emit_go_no_go"] is False
    assert result["internal_envelope"]["can_emit_firma_ready"] is False
    assert result["internal_envelope"]["can_authorize_output"] is False


def test_real_case_affidamento_diretto_impegno_m07_incomplete_blocks_roundtrip() -> None:
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


def test_real_case_affidamento_diretto_impegno_rejects_level_b_m07_overreach() -> None:
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


def test_real_case_affidamento_diretto_impegno_rejects_decisional_field_in_response() -> None:
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


def test_real_case_affidamento_diretto_impegno_rejects_firma_ready_in_response() -> None:
    request = build_real_case_request()

    def invoker(_: dict) -> dict:
        return build_real_case_response_invalid_firma_ready()

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "RESPONSE_INVALID"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is False
    assert any(
        "Forbidden response fields present" in error
        for error in result["response_validation"]["errors"]
    )
    assert result["internal_envelope"] is None


def test_real_case_affidamento_diretto_impegno_request_stays_non_decisional() -> None:
    request = build_real_case_request()

    assert request["source_level"] == "LEVEL_A"
    assert request["target_level"] == "LEVEL_B"
    assert request["request_kind"] == "DOCUMENTARY_SUPPORT_REQUEST"
    assert request["documentary_scope"]["must_return_documentary_only"] is True
    assert request["documentary_scope"]["level_b_is_non_decisional"] is True
    assert "go_no_go" not in request
    assert "firma_ready" not in request
    assert "final_decision" not in request