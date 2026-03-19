import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "final_ab_request_schema_v1.json"

FORBIDDEN_REQUEST_FIELDS = {
    "decision",
    "final_decision",
    "approval",
    "human_approval",
    "normative_prevalence_choice",
    "legal_applicability_decision",
    "final_motivation",
    "m07_closed",
    "output_authorized",
    "final_compliance_passed",
    "provvedimento_generato",
    "rac_finale_decisorio",
    "esito_istruttoria_conclusivo"
}


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _valid_request() -> dict:
    return {
        "request_id": "req_phase10_001",
        "case_id": "case_phase10_001",
        "trace_id": "trace_phase10_001",
        "api_version": "1.0.0",
        "caller_module": "A1_OrchestratorePPAV",
        "target_module": "RAG_NORMATIVO_GOVERNATO_E_FEDERATO",
        "request_type": "M07_DOCUMENTARY_SUPPORT",
        "documentary_objective": "Supporto documentale controllato su M07 e rinvii essenziali.",
        "legal_scope": {
            "domain": "enti_locali",
            "primary_corpus": "tuel",
            "normative_perimeter": ["D.Lgs. 267/2000 art. 42"]
        },
        "requested_outputs": [
            "documentary_packet",
            "citation_packet",
            "vigenza_status",
            "cross_reference_status",
            "coverage_status",
            "warnings",
            "errors",
            "blocks",
            "trace_tecnica"
        ],
        "documentary_constraints": {
            "support_only": True,
            "propagate_critical_blocks": True,
            "allow_only_documentary_outputs": True,
            "coverage_target": "STANDARD"
        },
        "m07_context": {
            "support_requested": True,
            "human_completion_required": True,
            "closure_requested": False,
            "requested_scope": "ANNEX_AND_CROSSREF"
        },
        "audit_context": {
            "timestamp": "2026-03-19T10:30:00Z",
            "orchestrator_mode": "AI_ASSISTED_LEVEL_A",
            "human_approval_required": True,
            "audit_channel": "LEVEL_A_AUDIT"
        }
    }


def test_request_schema_has_expected_required_fields() -> None:
    schema = _load_schema()
    required = set(schema["required"])
    assert {
        "request_id",
        "case_id",
        "trace_id",
        "api_version",
        "caller_module",
        "target_module",
        "request_type",
        "documentary_objective",
        "legal_scope",
        "requested_outputs",
        "documentary_constraints",
        "m07_context",
        "audit_context"
    }.issubset(required)


def test_request_example_has_no_forbidden_fields_and_is_level_b_safe() -> None:
    request = _valid_request()
    assert FORBIDDEN_REQUEST_FIELDS.isdisjoint(request.keys())
    assert request["target_module"] == "RAG_NORMATIVO_GOVERNATO_E_FEDERATO"
    assert request["requested_outputs"][0] == "documentary_packet"


def test_request_example_keeps_m07_non_conclusive() -> None:
    request = _valid_request()
    assert request["m07_context"]["support_requested"] is True
    assert request["m07_context"]["human_completion_required"] is True
    assert request["m07_context"]["closure_requested"] is False

