from __future__ import annotations

from runtime.final_aba_runtime_handoff_service import perform_runtime_roundtrip


def build_real_case_request() -> dict:
    return {
        "request_id": "REQ-REAL-AVVIO-0001",
        "case_id": "CASE-REAL-AVVIO-0001",
        "trace_id": "TRACE-REAL-AVVIO-0001",
        "source_level": "LEVEL_A",
        "target_level": "LEVEL_B",
        "request_kind": "DOCUMENTARY_SUPPORT_REQUEST",
        "source_phase": "S3",
        "documentary_scope": {
            "must_return_documentary_only": True,
            "level_b_is_non_decisional": True,
            "objective": (
                "Ricostruire il perimetro documentale ufficiale dell'avvio del "
                "procedimento d'ufficio per possibile revoca parziale di contributo "
                "comunale ad associazione, con focus su comunicazione di avvio, "
                "contenuti obbligatori, regolamento comunale sui contributi, "
                "termini procedimentali, garanzie partecipative, effetti della "
                "mancata comunicazione, fascicolo e tracciabilità."
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
            "note": "Caso reale n. 1 - avvio procedimento revoca contributo",
        },
    }


def build_real_case_response_degraded() -> dict:
    return {
        "response_id": "RESP-REAL-AVVIO-0001",
        "request_id": "REQ-REAL-AVVIO-0001",
        "source_level": "LEVEL_B",
        "target_level": "LEVEL_A",
        "response_kind": "DOCUMENTARY_SUPPORT_RESPONSE",
        "documentary_status": "DOCUMENTARY_WARNING",
        "documentary_packet": {
            "documentary_only": True,
            "contains_decision": False,
            "packet_title": "Supporto documentale su avvio procedimento e revoca contributo",
        },
        "citations": [
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
                "citation_text": "Legge 7 agosto 1990, n. 241, art. 10",
                "official_source": True,
            },
            {
                "source_type": "norma",
                "citation_text": "Legge 7 agosto 1990, n. 241, art. 21-octies",
                "official_source": True,
            },
            {
                "source_type": "norma",
                "citation_text": "D.Lgs. 7 marzo 2005, n. 82, art. 41",
                "official_source": True,
            },
        ],
        "vigency_checks": [
            {
                "source": "L. 241/1990, artt. 7, 8, 10, 21-octies",
                "vigency_status": "TO_VERIFY_IN_CONTEXT",
            },
            {
                "source": "D.Lgs. 82/2005, art. 41",
                "vigency_status": "TO_VERIFY_IN_CONTEXT",
            },
        ],
        "cross_references": [
            {
                "source": "L. 241/1990, art. 7",
                "linked_to": "L. 241/1990, art. 8",
            },
            {
                "source": "L. 241/1990, art. 7",
                "linked_to": "L. 241/1990, art. 10",
            },
            {
                "source": "Avvio del procedimento",
                "linked_to": "CAD, art. 41",
            },
        ],
        "coverage_report": {
            "coverage_status": "PARTIAL",
            "missing_points": [
                "verifica regolamento comunale contributi",
                "verifica clausole della determina di concessione",
                "verifica modelli interni di rendicontazione",
            ],
        },
        "warnings": [
            "Coverage documentale parziale sul livello regolamentare interno.",
            "Contestualizzazione applicativa concreta riservata al Livello A.",
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
    response["warnings"] = ["Supporto documentale non sufficiente per M07."]
    return response


def build_real_case_response_invalid_overreach() -> dict:
    response = build_real_case_response_degraded()
    response["m07_documentary_support"]["completion_declared"] = True
    response["documentary_status"] = "DOCUMENTARY_OK"
    response["blocks"] = []
    response["coverage_report"] = {"coverage_status": "FULL"}
    response["warnings"] = []
    return response


def test_real_case_revoca_contributo_roundtrip_is_degraded_but_valid() -> None:
    request = build_real_case_request()

    def invoker(_: dict) -> dict:
        return build_real_case_response_degraded()

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "ROUNDTRIP_DEGRADED"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is True
    assert result["internal_envelope"] is not None
    assert result["internal_envelope"]["case_id"] == "CASE-REAL-AVVIO-0001"
    assert result["internal_envelope"]["trace_id"] == "TRACE-REAL-AVVIO-0001"
    assert result["internal_envelope"]["degrading_block_present"] is True
    assert result["internal_envelope"]["critical_block_present"] is False
    assert "COVERAGE_INSUFFICIENT" in result["internal_envelope"]["block_codes_received"]
    assert result["internal_envelope"]["can_emit_go_no_go"] is False
    assert result["internal_envelope"]["can_emit_firma_ready"] is False
    assert result["internal_envelope"]["can_authorize_output"] is False


def test_real_case_revoca_contributo_m07_incomplete_blocks_roundtrip() -> None:
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


def test_real_case_revoca_contributo_rejects_level_b_m07_overreach() -> None:
    request = build_real_case_request()

    def invoker(_: dict) -> dict:
        return build_real_case_response_invalid_overreach()

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "RESPONSE_INVALID"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is False
    assert any(
        "Level B cannot declare m07 completion" in error
        for error in result["response_validation"]["errors"]
    )
    assert result["internal_envelope"] is None


def test_real_case_revoca_contributo_request_stays_non_decisional() -> None:
    request = build_real_case_request()

    assert request["source_level"] == "LEVEL_A"
    assert request["target_level"] == "LEVEL_B"
    assert request["request_kind"] == "DOCUMENTARY_SUPPORT_REQUEST"
    assert request["documentary_scope"]["must_return_documentary_only"] is True
    assert request["documentary_scope"]["level_b_is_non_decisional"] is True
    assert "go_no_go" not in request
    assert "firma_ready" not in request
    assert "final_decision" not in request