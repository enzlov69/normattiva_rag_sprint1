import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SENSITIVE = {
    'A4_M07Governor',
    'A6_RACBuilder',
    'A5_FinalComplianceGate',
    'A7_OutputAuthorizer',
}


def load_registry():
    return json.loads((ROOT / 'schemas' / 'level_a_consumption_event_registry_v1.json').read_text(encoding='utf-8'))


def test_consumption_event_registry_covers_four_minimum_states():
    registry = load_registry()
    decisions = {event['intake_decision'] for event in registry['events']}

    assert decisions == {
        'ACCEPT_SUPPORT_ONLY',
        'ACCEPT_WITH_DEGRADATION',
        'QUARANTINE',
        'REJECT',
    }


def test_consumption_event_registry_keeps_allowed_and_forbidden_targets_separate():
    for event in load_registry()['events']:
        assert set(event['allowed_targets']).isdisjoint(set(event['forbidden_targets']))
        assert event['requires_audit'] is True
        assert event['requires_isolation_log'] is True


def test_consumption_event_registry_marks_sensitive_modules_as_forbidden():
    for event in load_registry()['events']:
        assert SENSITIVE.issubset(set(event['forbidden_targets']))
