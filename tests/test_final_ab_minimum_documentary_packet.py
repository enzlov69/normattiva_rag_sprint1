import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "final_ab_minimum_documentary_packet_schema_v1.json"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _valid_packet() -> dict:
    return {
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
            "trace_id": "trace_packet_001",
            "request_id": "req_packet_001"
        },
        "shadow_trace": {
            "trace_id": "trace_packet_001",
            "request_id": "req_packet_001",
            "human_completion_required": True
        }
    }


def test_minimum_packet_schema_contains_required_components() -> None:
    schema = _load_schema()
    required = set(schema["required"])
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


def test_minimum_packet_example_has_audit_and_shadow() -> None:
    packet = _valid_packet()
    assert packet["audit_trace"]["trace_id"] == "trace_packet_001"
    assert packet["shadow_trace"]["request_id"] == "req_packet_001"


def test_minimum_packet_example_has_coherent_warnings_errors_blocks() -> None:
    packet = _valid_packet()
    assert packet["documentary_warnings"] == []
    assert packet["documentary_errors"] == []
    assert packet["documentary_blocks"] == []
    assert packet["completeness_flags"]["minimum_integrity"] is True

