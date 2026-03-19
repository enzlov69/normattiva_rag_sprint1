import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_schema():
    return json.loads((ROOT / 'schemas' / 'final_ab_release_readiness_statement_v1.json').read_text(encoding='utf-8'))


def test_release_readiness_statement_has_minimum_fields():
    schema = load_schema()

    assert set(schema['required_fields']) >= {
        'statement_id',
        'trace_id',
        'baseline_tag',
        'baseline_commit',
        'readiness_status',
        'human_approval_required',
        'non_delegability_confirmed',
    }


def test_release_readiness_statement_has_coherent_statuses():
    schema = load_schema()

    assert schema['readiness_status_values'] == [
        'NON_CERTIFIABLE',
        'CONDITIONALLY_CERTIFIABLE',
        'CERTIFIABLE',
    ]


def test_release_readiness_statement_requires_human_approval_and_non_delegability():
    example = load_schema()['baseline_example']

    assert example['human_approval_required'] is True
    assert example['non_delegability_confirmed'] is True
    assert example['blocks_opponibility'] is True
