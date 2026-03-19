import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_registry():
    return json.loads((ROOT / 'schemas' / 'final_ab_response_quarantine_registry_v1.json').read_text(encoding='utf-8'))


def test_quarantine_registry_covers_minimum_triggers():
    registry = load_registry()
    codes = {entry['quarantine_code'] for entry in registry['entries']}

    assert codes == {
        'Q_FORBIDDEN_FIELDS',
        'Q_TRACEABILITY_GAP',
        'Q_MISSING_DOCUMENTARY_PACKET',
        'Q_M07_BOUNDARY',
        'Q_AUTHORIZATION_SEMANTICS',
        'Q_UNRESOLVED_CRITICAL_BLOCKS',
    }


def test_quarantine_registry_requires_manual_review_for_all_entries():
    registry = load_registry()

    for entry in registry['entries']:
        assert entry['requires_manual_review'] is True
        assert entry['severity'] in {'HIGH', 'CRITICAL'}


def test_quarantine_registry_contains_boundary_and_traceability_cases():
    entries = {entry['quarantine_code']: entry for entry in load_registry()['entries']}

    assert 'boundary' in entries['Q_M07_BOUNDARY']['trigger_condition'].lower() or 'm07' in entries['Q_M07_BOUNDARY']['trigger_condition'].lower()
    assert 'traceability' in entries['Q_TRACEABILITY_GAP']['trigger_condition'].lower()
    assert 'A7_OutputAuthorizer' in entries['Q_AUTHORIZATION_SEMANTICS']['affected_modules']
