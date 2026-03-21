from runtime.metodo_cerda_documentary_request_builder import (
    DocumentaryRequestBuilderError,
    build_documentary_request_envelope,
)


def _classified_case(**overrides):
    payload = {
        "request_id": "REQ-A1TER-001",
        "case_id": "CASE-A1TER-001",
        "trace_id": "TRACE-A1TER-001",
        "natura_output": "PARERE",
        "tipologia_atto": "DETERMINA",
        "materia_prevalente": "CONTRATTI",
        "sensibilita": "MEDIA",
        "rischio_iniziale": "MEDIO",
        "intensita_applicativa": "MEDIA",
        "zone_rosse": [],
        "fast_track": False,
        "moduli_attivati": ["M07-LPR", "RAC"],
        "esigenza_documentale": True,
        "obiettivo_documentale": "verifica vigenza e rinvii",
        "query_guidata": "art. 107 TUEL affidamento",
        "corpora_preferiti": ["tuel", "l241"],
        "contesto_metodologico": {
            "fase0_requires_federated_documentary_support": True,
        },
        "caller_module": "A0_FASE0",
    }
    payload.update(overrides)
    return payload


def test_builder_creates_request_from_classified_level_a_output():
    request = build_documentary_request_envelope(
        _classified_case(),
        timestamp="2026-03-21T10:00:00Z",
    )

    assert request["request_id"] == "REQ-A1TER-001"
    assert request["case_id"] == "CASE-A1TER-001"
    assert request["trace_id"] == "TRACE-A1TER-001"
    assert request["target_module"] == "B_REAL_FEDERATED_RUNNER"
    assert request["payload"]["documentary_scope"]["must_return_documentary_only"] is True
    assert request["payload"]["documentary_scope"]["level_b_is_non_decisional"] is True
    assert request["payload"]["documentary_channel_policy"]["federated_is_not_official_source"] is True
    assert request["payload"]["documentary_request"]["query_guidata"] == "art. 107 TUEL affidamento"


def test_builder_sets_tipologia_atto_to_null_when_output_is_not_atto():
    request = build_documentary_request_envelope(
        _classified_case(natura_output="PARERE", tipologia_atto="DETERMINA"),
        timestamp="2026-03-21T10:00:00Z",
    )

    assert request["payload"]["documentary_request"]["tipologia_atto"] is None


def test_builder_keeps_required_identifiers():
    request = build_documentary_request_envelope(
        _classified_case(),
        timestamp="2026-03-21T10:00:00Z",
    )

    assert request["request_id"]
    assert request["case_id"]
    assert request["trace_id"]


def test_builder_payload_does_not_include_decision_fields():
    request = build_documentary_request_envelope(
        _classified_case(),
        timestamp="2026-03-21T10:00:00Z",
    )

    payload = request["payload"]
    forbidden = {
        "final_decision",
        "go_no_go",
        "output_authorized",
        "m07_closed",
        "rac_finalized",
    }
    assert forbidden.isdisjoint(payload.keys())
    assert forbidden.isdisjoint(payload["documentary_request"].keys())


def test_builder_rejects_missing_required_fields():
    try:
        build_documentary_request_envelope(
            _classified_case(request_id=None),
            timestamp="2026-03-21T10:00:00Z",
        )
    except DocumentaryRequestBuilderError as exc:
        assert "None is not of type 'string'" in str(exc)
    else:
        raise AssertionError("Expected DocumentaryRequestBuilderError")
