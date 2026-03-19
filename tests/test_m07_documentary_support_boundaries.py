import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = BASE_DIR / "schemas"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


def test_m07_evidence_pack_rejects_forbidden_m07_closed_field() -> None:
    schema = load_schema("m07_evidence_pack_schema_v1.json")

    payload = {
        "record_id": "rec_m07_001",
        "record_type": "M07EvidencePack",
        "m07_pack_id": "m07pack_001",
        "case_id": "case_001",
        "source_ids": ["source_tuel_267_2000"],
        "norm_unit_ids": ["normunit_art107"],
        "ordered_reading_sequence": [],
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
        "active_flag": True,
        "m07_closed": True
    }

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(payload)


def test_response_rejects_forbidden_final_decision_field() -> None:
    schema = load_schema("m07_documentary_support_response_schema_v1.json")

    payload = {
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
        "timestamp": "2026-03-19T10:00:01Z",
        "final_decision": "GO"
    }

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(payload)


def test_response_rejects_payload_with_conclusive_semantics() -> None:
    schema = load_schema("m07_documentary_support_response_schema_v1.json")

    payload = {
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
        "blocks": [
            {
                "block_id": "blk_001",
                "case_id": "case_001",
                "block_code": "RAG_SCOPE_VIOLATION",
                "block_category": "BOUNDARY",
                "block_severity": "CRITICAL",
                "origin_module": "B17_GuardrailEngine",
                "block_reason": "tentativo di semantica conclusiva",
                "block_status": "OPEN"
            }
        ],
        "timestamp": "2026-03-19T10:00:01Z"
    }

    Draft202012Validator(schema).validate(payload)
    assert payload["blocks"][0]["block_code"] == "RAG_SCOPE_VIOLATION"