from __future__ import annotations

from runtime.final_aba_runtime_handoff_service import perform_runtime_roundtrip


# ============================================================
# CASO REALE N. 1
# Avvio del procedimento d'ufficio per possibile revoca parziale
# di contributo a causa di mancata rendicontazione
# ============================================================


def build_case1_request() -> dict:
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
            "note": "Pack v1 - Caso reale 1",
        },
    }


def build_case1_response_degraded() -> dict:
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


def build_case1_response_blocked_m07() -> dict:
    response = build_case1_response_degraded()
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


# ============================================================
# CASO REALE N. 2
# Procedimento su istanza di parte per contributo straordinario
# con documentazione iniziale incompleta
# ============================================================


def build_case2_request() -> dict:
    return {
        "request_id": "REQ-REAL-ISTANZA-0002",
        "case_id": "CASE-REAL-ISTANZA-0002",
        "trace_id": "TRACE-REAL-ISTANZA-0002",
        "source_level": "LEVEL_A",
        "target_level": "LEVEL_B",
        "request_kind": "DOCUMENTARY_SUPPORT_REQUEST",
        "source_phase": "S3",
        "documentary_scope": {
            "must_return_documentary_only": True,
            "level_b_is_non_decisional": True,
            "objective": (
                "Ricostruire il perimetro documentale ufficiale del procedimento "
                "su istanza di parte per contributo economico straordinario, con "
                "focus su avvio del procedimento, contenuti della comunicazione, "
                "richiesta di integrazione documentale, eventuale preavviso di "
                "rigetto, fascicolo e tracciabilità."
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
            "note": "Pack v1 - Caso reale 2",
        },
    }


def build_case2_response_degraded() -> dict:
    return {
        "response_id": "RESP-REAL-ISTANZA-0002",
        "request_id": "REQ-REAL-ISTANZA-0002",
        "source_level": "LEVEL_B",
        "target_level": "LEVEL_A",
        "response_kind": "DOCUMENTARY_SUPPORT_RESPONSE",
        "documentary_status": "DOCUMENTARY_WARNING",
        "documentary_packet": {
            "documentary_only": True,
            "contains_decision": False,
            "packet_title": "Supporto documentale su istanza contributo con documentazione incompleta",
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
                "citation_text": "D.Lgs. 7 marzo 2005, n. 82, art. 41",
                "official_source": True,
            },
        ],
        "vigency_checks": [
            {
                "source": "L. 241/1990, artt. 2, 7, 8, 10-bis",
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
                "source": "L. 241/1990, art. 2",
                "linked_to": "L. 241/1990, art. 10-bis",
            },
            {
                "source": "Procedimento su istanza di parte",
                "linked_to": "CAD, art. 41",
            },
        ],
        "coverage_report": {
            "coverage_status": "PARTIAL",
            "missing_points": [
                "verifica regolamento comunale su contributi e patrocini",
                "verifica modulistica interna e documentazione obbligatoria",
                "contestualizzazione finale del caso concreto riservata al Livello A",
            ],
        },
        "warnings": [
            "Coverage documentale parziale sul livello regolamentare e modulare interno.",
            "La valutazione finale sulla sufficienza della documentazione resta riservata al Livello A.",
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


def build_case2_response_invalid_overreach() -> dict:
    response = build_case2_response_degraded()
    response["m07_documentary_support"]["completion_declared"] = True
    response["documentary_status"] = "DOCUMENTARY_OK"
    response["blocks"] = []
    response["coverage_report"] = {"coverage_status": "FULL"}
    response["warnings"] = []
    return response


# ============================================================
# TEST PACK V1
# ============================================================


def test_real_cases_pack_v1_case1_degraded_valid() -> None:
    request = build_case1_request()

    def invoker(_: dict) -> dict:
        return build_case1_response_degraded()

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "ROUNDTRIP_DEGRADED"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is True
    assert result["internal_envelope"] is not None
    assert result["internal_envelope"]["case_id"] == "CASE-REAL-AVVIO-0001"
    assert result["internal_envelope"]["degrading_block_present"] is True
    assert result["internal_envelope"]["critical_block_present"] is False
    assert "COVERAGE_INSUFFICIENT" in result["internal_envelope"]["block_codes_received"]


def test_real_cases_pack_v1_case1_m07_blocked() -> None:
    request = build_case1_request()

    def invoker(_: dict) -> dict:
        return build_case1_response_blocked_m07()

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "ROUNDTRIP_BLOCKED"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is True
    assert result["internal_envelope"] is not None
    assert result["internal_envelope"]["critical_block_present"] is True
    assert "M07_DOCUMENTARY_INCOMPLETE" in result["internal_envelope"]["block_codes_received"]


def test_real_cases_pack_v1_case2_degraded_valid() -> None:
    request = build_case2_request()

    def invoker(_: dict) -> dict:
        return build_case2_response_degraded()

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "ROUNDTRIP_DEGRADED"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is True
    assert result["internal_envelope"] is not None
    assert result["internal_envelope"]["case_id"] == "CASE-REAL-ISTANZA-0002"
    assert result["internal_envelope"]["degrading_block_present"] is True
    assert result["internal_envelope"]["critical_block_present"] is False
    assert "COVERAGE_INSUFFICIENT" in result["internal_envelope"]["block_codes_received"]


def test_real_cases_pack_v1_case2_m07_overreach_rejected() -> None:
    request = build_case2_request()

    def invoker(_: dict) -> dict:
        return build_case2_response_invalid_overreach()

    result = perform_runtime_roundtrip(request, invoker)

    assert result["runtime_status"] == "RESPONSE_INVALID"
    assert result["request_validation"]["is_valid"] is True
    assert result["response_validation"]["is_valid"] is False
    assert result["internal_envelope"] is None
    assert any(
        "Level B cannot declare m07 completion" in error
        for error in result["response_validation"]["errors"]
    )


def test_real_cases_pack_v1_all_requests_remain_non_decisional() -> None:
    case1_request = build_case1_request()
    case2_request = build_case2_request()

    for request in (case1_request, case2_request):
        assert request["source_level"] == "LEVEL_A"
        assert request["target_level"] == "LEVEL_B"
        assert request["request_kind"] == "DOCUMENTARY_SUPPORT_REQUEST"
        assert request["documentary_scope"]["must_return_documentary_only"] is True
        assert request["documentary_scope"]["level_b_is_non_decisional"] is True
        assert "go_no_go" not in request
        assert "firma_ready" not in request
        assert "final_decision" not in request


def test_real_cases_pack_v1_summary_state_is_coherent() -> None:
    scenarios = []

    def invoker_case1(_: dict) -> dict:
        return build_case1_response_degraded()

    def invoker_case2(_: dict) -> dict:
        return build_case2_response_degraded()

    scenarios.append(perform_runtime_roundtrip(build_case1_request(), invoker_case1))
    scenarios.append(perform_runtime_roundtrip(build_case2_request(), invoker_case2))

    statuses = [scenario["runtime_status"] for scenario in scenarios]

    assert statuses == ["ROUNDTRIP_DEGRADED", "ROUNDTRIP_DEGRADED"]

    for scenario in scenarios:
        assert scenario["request_validation"]["is_valid"] is True
        assert scenario["response_validation"]["is_valid"] is True
        assert scenario["internal_envelope"] is not None
        assert scenario["internal_envelope"]["can_emit_go_no_go"] is False
        assert scenario["internal_envelope"]["can_emit_firma_ready"] is False
        assert scenario["internal_envelope"]["can_authorize_output"] is False