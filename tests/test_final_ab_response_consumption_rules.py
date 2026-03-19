import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_TARGETS = {
    'A4_M07Governor',
    'A6_RACBuilder',
    'A5_FinalComplianceGate',
    'A7_OutputAuthorizer',
}


def load_rules():
    return json.loads((ROOT / 'schemas' / 'final_ab_response_consumption_rules_v1.json').read_text(encoding='utf-8'))


def test_response_consumption_rules_cover_minimum_decisions():
    data = load_rules()
    decisions = {rule['intake_decision'] for rule in data['rules']}

    assert decisions == {
        'ACCEPT_SUPPORT_ONLY',
        'ACCEPT_WITH_DEGRADATION',
        'QUARANTINE',
        'REJECT',
    }


def test_response_consumption_rules_protect_sensitive_targets_in_all_cases():
    data = load_rules()

    for rule in data['rules']:
        assert SENSITIVE_TARGETS.issubset(set(rule['forbidden_level_a_targets']))
        assert set(rule['allowed_level_a_targets']).isdisjoint(SENSITIVE_TARGETS)
        assert rule['blocks_opponibility'] is True


def test_response_consumption_rules_keep_degraded_and_quarantine_under_review():
    rules = {rule['intake_decision']: rule for rule in load_rules()['rules']}

    assert rules['ACCEPT_WITH_DEGRADATION']['requires_human_review'] is True
    assert rules['QUARANTINE']['requires_quarantine'] is True
    assert rules['REJECT']['requires_human_review'] is True
