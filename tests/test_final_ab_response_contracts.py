import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESPONSE_SCHEMA_PATH = ROOT / "schemas" / "final_ab_response_schema_v1.json"
PACKET_SCHEMA_PATH = ROOT / "schemas" / "final_ab_minimum_documentary_packet_schema_v1.json"
FORBIDDEN_REGISTRY_PATH = ROOT / "schemas" / "final_ab_forbidden_level_b_fields_registry_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _scan_keys(node, hits=None):
    if hits is None:
        hits = []
    if isinstance(node, dict):
        for key, value in node.items():
            hits.append(key)
            _scan_keys(value, hits)
    elif isinstance(node, list):
        for item in node:
            _scan_keys(item, hits)
    return hits


def _valid_response() -> dict:
    return {
        "response_id": "resp_phase10_001",
        "request_id": "req_phase10_001",
        "case_id": "case_phase10_001",
        "trace_id": "trace_phase10_001",
        "responder_module": "RAG_NORMATIVO_GOVERNATO_E_FEDERATO",
        "response_status": "SUCCESS",
        "documentary_packet": {
            "source_set": [{"source_id": "src_001"}],
            "citation_set": [{"citation_id": "cit_001"}],
            "vigenza_findings": [{"finding_id": "vig_001"}],
            "cross_reference_findings": [{"finding_id": "xref_001"}],
            "coverage_findings": {
                "coverage_status": "SUFFICIENT",
                "critical_gap_flag": False
            },
            "documentary_warnings": [],
            "documentary_errors": [],
            "documentary_blocks": [],
            "completeness_flags": {
                "minimum_integrity": True,
                "minimum_traceability": True,
                "minimum_coverage": True
            },
            "audit_trace": {
                "trace_id": "trace_phase10_001",
                "request_id": "req_phase10_001"
            },
            "shadow_trace": {
                "trace_id": "trace_phase10_001",
                "request_id": "req_phase10_001",
                "human_completion_required": True
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "audit_trace": {
            "trace_id": "trace_phase10_001",
            "request_id": "req_phase10_001",
            "contract_validation_passed": True,
            "human_approval_required": True,
            "adapter_stage": "PRE_RUNTIME_CONTROLLED_HANDOFF"
        },
        "shadow_trace": {
            "trace_id": "trace_phase10_001",
            "request_id": "req_phase10_001",
            "forbidden_fields_detected": [],
            "propagated_block_codes": [],
            "support_only_flag": True,
            "m07_boundary_state": "PREPARATORY_ONLY"
        },
        "timestamp": "2026-03-19T10:31:00Z"
    }


def test_response_schema_has_expected_required_fields() -> None:
    schema = _load(RESPONSE_SCHEMA_PATH)
    required = set(schema["required"])
    assert {
        "response_id",
        "request_id",
        "case_id",
        "trace_id",
        "responder_module",
        "response_status",
        "documentary_packet",
        "warnings",
        "errors",
        "blocks",
        "audit_trace",
        "shadow_trace",
        "timestamp"
    }.issubset(required)


def test_response_example_is_documentary_only_and_traceable() -> None:
    response = _valid_response()
    forbidden = {entry["field_name"] for entry in _load(FORBIDDEN_REGISTRY_PATH)["entries"]}
    keys = set(_scan_keys(response))
    assert forbidden.isdisjoint(keys)
    assert response["documentary_packet"]["source_set"]
    assert response["audit_trace"]["trace_id"] == response["trace_id"]
    assert response["shadow_trace"]["request_id"] == response["request_id"]


def test_documentary_packet_schema_requires_minimum_packet() -> None:
    packet_schema = _load(PACKET_SCHEMA_PATH)
    required = set(packet_schema["required"])
    assert {
        "source_set",
        "citation_set",
        "vigenza_findings",
        "cross_reference_findings",
        "coverage_findings",
        "documentary_warnings",
        "documentary_errors",
        "documentary_blocks",
        "completeness_flags",
        "audit_trace",
        "shadow_trace"
    }.issubset(required)

