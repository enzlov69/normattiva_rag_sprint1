import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_registry():
    return json.loads((ROOT / 'schemas' / 'level_a_manual_review_event_registry_v1.json').read_text(encoding='utf-8'))


def test_manual_review_event_registry_covers_minimum_events():
    registry = load_registry()
    event_codes = {event['event_code'] for event in registry['events']}

    assert event_codes == {
        'MR_REVIEW_DEGRADED_SUPPORT',
        'MR_REVIEW_QUARANTINE_HISTORY',
        'MR_REVIEW_M07_BOUNDARY',
        'MR_REVIEW_AUTHORIZATION_SEMANTICS',
        'MR_ESCALATION_CRITICAL_BLOCKS',
        'MR_APPROVAL_DENIAL_PATH',
    }


def test_manual_review_event_registry_has_consistent_next_states():
    for event in load_registry()['events']:
        assert set(event['allowed_next_states']).isdisjoint(set(event['forbidden_next_states']))
        assert event['review_required'] is True
        assert event['blocks_opponibility'] is True


def test_manual_review_event_registry_contains_escalation_and_denial_paths():
    events = {event['event_code']: event for event in load_registry()['events']}

    assert events['MR_ESCALATION_CRITICAL_BLOCKS']['escalation_required'] is True
    assert 'APPROVAL_DENIED' in events['MR_APPROVAL_DENIAL_PATH']['allowed_next_states']
