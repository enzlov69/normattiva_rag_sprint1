import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_schema():
    return json.loads((ROOT / 'schemas' / 'level_a_decision_isolation_log_schema_v1.json').read_text(encoding='utf-8'))


def test_decision_isolation_log_schema_contains_required_fields():
    schema = load_schema()

    assert set(schema['required_fields']) >= {
        'log_id',
        'trace_id',
        'case_id',
        'protected_module',
        'source_allowed',
        'isolation_result',
        'violation_detected',
        'violation_type',
        'manual_review_required',
        'blocks_opponibility',
    }


def test_decision_isolation_log_schema_covers_main_violations():
    schema = load_schema()

    assert set(schema['covered_violation_types']) == {
        'PROTECTED_MODULE_ISOLATION',
        'SUPPORT_ONLY_BREACH',
        'M07_CONTAMINATION',
        'AUTHORIZATION_LIKE_SEMANTICS',
        'FORBIDDEN_FIELDS',
        'UNRESOLVED_CRITICAL_BLOCKS',
    }


def test_decision_isolation_log_schema_remains_non_decisional():
    schema = load_schema()

    assert 'does not validate, authorize or decide any administrative outcome.' in ' '.join(schema['notes'])
