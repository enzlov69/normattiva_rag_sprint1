import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_schema():
    return json.loads((ROOT / 'schemas' / 'level_a_consumption_audit_trail_schema_v1.json').read_text(encoding='utf-8'))


def test_consumption_audit_trail_schema_contains_required_fields():
    schema = load_schema()

    assert set(schema['required_fields']) >= {
        'event_id',
        'trace_id',
        'case_id',
        'source_response_id',
        'intake_decision',
        'target_level_a_module',
        'consumption_mode',
        'support_only_flag',
        'audit_timestamp',
    }


def test_consumption_audit_trail_schema_maps_intake_decisions_to_modes():
    schema = load_schema()

    assert schema['intake_decision_map'] == {
        'ACCEPT_SUPPORT_ONLY': 'DOCUMENTARY_SUPPORT_ONLY',
        'ACCEPT_WITH_DEGRADATION': 'DEGRADED_SUPPORT',
        'QUARANTINE': 'QUARANTINED_NOT_CONSUMED',
        'REJECT': 'REJECTED_NOT_CONSUMED',
    }


def test_consumption_audit_trail_schema_keeps_support_only_semantics_primary():
    schema = load_schema()

    assert 'support_only_flag remains the primary semantic anchor for Level A intake traceability.' in schema['notes']
