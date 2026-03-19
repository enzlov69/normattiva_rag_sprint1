import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_policy():
    return json.loads((ROOT / 'schemas' / 'level_a_manual_review_gate_policy_v1.json').read_text(encoding='utf-8'))


def test_manual_review_gate_policy_contains_required_fields():
    policy = load_policy()

    assert set(policy.keys()) >= {
        'policy_name',
        'review_required_conditions',
        'escalation_conditions',
        'approval_block_conditions',
        'required_review_traces',
        'sensitive_modules_protected',
        'human_approval_required_for',
        'forbidden_approval_sources',
        'notes',
    }


def test_manual_review_gate_policy_covers_review_escalation_and_block_conditions():
    policy = load_policy()

    assert 'quarantine_history_present' in policy['review_required_conditions']
    assert 'unresolved_critical_blocks' in policy['escalation_conditions']
    assert 'approval_derived_from_level_b_response' in policy['approval_block_conditions']


def test_manual_review_gate_policy_protects_sensitive_modules_and_forbidden_sources():
    policy = load_policy()

    assert policy['sensitive_modules_protected'] == [
        'A4_M07Governor',
        'A6_RACBuilder',
        'A5_FinalComplianceGate',
        'A7_OutputAuthorizer',
    ]
    assert 'response_b_to_a' in policy['forbidden_approval_sources']
    assert 'output_authorizer' in policy['forbidden_approval_sources']
