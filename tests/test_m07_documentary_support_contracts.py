import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = BASE_DIR / "schemas"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture()
def request_schema() -> dict:
    return load_schema("m07_documentary_support_request_schema_v1.json")


@pytest.fixture()
def response_schema() -> dict:
    return load_schema("m07_documentary_support_response_schema_v1.json")


@pytest.fixture()
def m07_schema() -> dict:
    return load_schema("m07_evidence_pack_schema_v1.json")


def test_request_schema_accepts_minimal_valid_payload(request_schema: dict) -> None:
    payload = {
        "request_id": "req_0001",
        "case_id": "case_001",
        "trace_id": "trace_001",
        "api_version": "2.0",
        "caller_module": "A1_OrchestratorePPAV",
        "target_module": "B16_M07SupportLayer",
        "timestamp": "2026-03-19T10:00:00Z",
        "payload": {
            "goal_istruttorio": "supporto documentale a M07 su testo normativo lungo",
            "domain_target": "enti_locali",
            "query_text": "articolo 107 TUEL e rapporto con competenze gestionali",
            "documentary_scope": {
                "source_priority": ["corpus_governato", "fonti_ufficiali"],
                "require_official_uri": True,
                "require_vigenza_check": True,
                "require_crossref_check": True,
                "require_coverage_check": True,
                "include_annexes": True
            },
            "m07_context": {
                "m07_opened": True,
                "human_reading_required": True
            },
            "requested_outputs": [
                "documentary_packet",
                "citation_packets",
                "vigenza_status",
                "crossref_status",
                "coverage_status",
                "m07_evidence_pack",
                "warnings",
                "errors",
                "blocks",
                "technical_trace"
            ]
        }
    }

    Draft202012Validator(request_schema).validate(payload)


def test_m07_evidence_pack_accepts_minimal_valid_object(m07_schema: dict) -> None:
    m07_pack = {
        "record_id": "rec_m07_001",
        "record_type": "M07EvidencePack",
        "m07_pack_id": "m07pack_001",
        "case_id": "case_001",
        "source_ids": ["source_tuel_267_2000"],
        "norm_unit_ids": ["normunit_art107"],
        "ordered_reading_sequence": [
            {
                "sequence_index": 1,
                "source_id": "source_tuel_267_2000",
                "norm_unit_id": "normunit_art107",
                "position_index": 107
            }
        ],
        "annex_refs": [],
        "crossref_refs": [],
        "coverage_ref_id": "cov_001",
        "missing_elements": [],
        "m07_support_status": "READY_FOR_HUMAN_READING",
        "human_completion_required": True,
        "created_at": "2026-03-19T10:00:00Z",
        "updated_at": "2026-03-19T10:00:00Z",
        "schema_version": "1.0",
        "record_version": 1,
        "source_layer": "B",
        "trace_id": "trace_001",
        "active_flag": True
    }

    Draft202012Validator(m07_schema).validate(m07_pack)


def test_response_schema_accepts_minimal_valid_payload(response_schema: dict) -> None:
    response = {
        "request_id": "req_0001",
        "case_id": "case_001",
        "trace_id": "trace_001",
        "api_version": "2.0",
        "responder_module": "B16_M07SupportLayer",
        "status": "SUCCESS",
        "payload": {
            "documentary_packet": {
                "source_ids": ["source_tuel_267_2000"],
                "norm_unit_ids": ["normunit_art107"],
                "support_only_flag": True
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": "2026-03-19T10:00:01Z"
    }

    Draft202012Validator(response_schema).validate(response)