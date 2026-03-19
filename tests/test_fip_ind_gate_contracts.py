import json
from pathlib import Path

from jsonschema import Draft202012Validator

from runtime.fip_ind_gate import build_question, evaluate_gate


BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = BASE_DIR / "schemas"


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


def test_questionnaire_schema_accepts_valid_payload() -> None:
    schema = _load_schema("fip_ind_questionnaire_schema_v1.json")
    questionnaire = {
        "case_id": "case_fip_001",
        "trace_id": "trace_fip_001",
        "act_type": "DELIBERA_GC",
        "act_title": "Atto di indirizzo per programmazione culturale",
        "compiled_by_module": "A1_OrchestratorePPAV",
        "questions": [build_question(f"Q{n:02d}", "NO") for n in range(1, 11)],
    }
    Draft202012Validator(schema).validate(questionnaire)


def test_gate_result_schema_accepts_runtime_result() -> None:
    schema = _load_schema("fip_ind_gate_result_schema_v1.json")
    questionnaire = {
        "case_id": "case_fip_002",
        "trace_id": "trace_fip_002",
        "act_type": "DELIBERA_GC",
        "act_title": "Atto di indirizzo puro",
        "compiled_by_module": "A1_OrchestratorePPAV",
        "questions": [build_question(f"Q{n:02d}", "NO") for n in range(1, 11)],
    }
    result = evaluate_gate(questionnaire)
    Draft202012Validator(schema).validate(result)
