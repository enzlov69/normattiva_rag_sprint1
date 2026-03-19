import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_schema():
    return json.loads((ROOT / 'schemas' / 'level_a_final_human_approval_trace_schema_v1.json').read_text(encoding='utf-8'))


def test_final_human_approval_trace_schema_contains_required_fields():
    schema = load_schema()

    assert set(schema['required_fields']) >= {
        'approval_trace_id',
        'trace_id',
        'case_id',
        'source_response_id',
        'review_event_id',
        'protected_module',
        'review_status',
        'approval_status',
        'approval_required',
        'approved_by_human',
        'approval_timestamp',
    }


def test_final_human_approval_trace_schema_distinguishes_review_and_approval_status():
    schema = load_schema()

    assert schema['review_status_values'] == [
        'REVIEW_REQUIRED',
        'REVIEW_COMPLETED',
    ]
    assert schema['approval_status_values'] == [
        'APPROVAL_GRANTED',
        'APPROVAL_DENIED',
        'ESCALATION_REQUIRED',
    ]


def test_final_human_approval_trace_schema_requires_human_for_granted_approval():
    schema = load_schema()

    assert 'APPROVAL_GRANTED requires approved_by_human=true.' in schema['approval_rules']
