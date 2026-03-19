import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_policy():
    return json.loads((ROOT / 'schemas' / 'level_a_runtime_intake_policy_v1.json').read_text(encoding='utf-8'))


def test_level_a_runtime_intake_policy_contains_required_fields():
    policy = load_policy()

    required = {
        'policy_name',
        'allowed_input_artifacts',
        'required_traces',
        'required_documentary_components',
        'forbidden_response_fields',
        'forbidden_response_semantics',
        'quarantine_conditions',
        'block_conditions',
        'degrade_conditions',
        'support_only_conditions',
        'sensitive_modules_protected',
        'notes',
    }

    assert required.issubset(policy.keys())


def test_level_a_runtime_intake_policy_protects_sensitive_modules():
    policy = load_policy()

    assert policy['sensitive_modules_protected'] == [
        'A4_M07Governor',
        'A6_RACBuilder',
        'A5_FinalComplianceGate',
        'A7_OutputAuthorizer',
    ]
    assert 'm07_closed' in policy['forbidden_response_fields']
    assert 'output_authorized' in policy['forbidden_response_fields']


def test_level_a_runtime_intake_policy_defines_quarantine_degrade_and_block_conditions():
    policy = load_policy()

    assert 'forbidden_field_present' in policy['quarantine_conditions']
    assert 'critical_block_present' in policy['block_conditions']
    assert 'warnings_present' in policy['degrade_conditions']
    assert 'support_only_flag_true_or_implied' in policy['support_only_conditions']
