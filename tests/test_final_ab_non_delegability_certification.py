import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_schema():
    return json.loads((ROOT / 'schemas' / 'final_ab_non_delegability_certification_v1.json').read_text(encoding='utf-8'))


def test_non_delegability_certification_covers_protected_functions():
    schema = load_schema()

    assert set(schema['protected_functions']) == {
        'qualificazione_del_fatto',
        'interpretazione',
        'rac_decisorio',
        'chiusura_m07',
        'final_compliance_gate',
        'output_authorizer',
        'approvazione_umana_finale',
    }


def test_non_delegability_certification_never_marks_critical_function_as_delegable_in_example():
    example = load_schema()['certification_examples'][0]

    assert example['delegated_to_level_b'] is False
    assert example['violation_detected'] is False
    assert example['blocking_effect'] is True


def test_non_delegability_certification_has_expected_status_values():
    schema = load_schema()

    assert schema['certification_status_values'] == [
        'CONFIRMED',
        'VIOLATED',
        'REQUIRES_REVIEW',
    ]
