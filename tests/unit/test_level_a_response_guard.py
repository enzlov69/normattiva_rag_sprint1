from src.adapters.level_a_request_mapper import LevelARequestEnvelope
from src.adapters.level_a_response_guard import LevelAResponseGuard


def test_response_guard_accepts_non_conclusive_payload():
    envelope = LevelARequestEnvelope(
        record_id='rec1',
        record_type='LevelARequestEnvelope',
        request_id='req1',
        case_id='case1',
        source_package_id='pkg1',
        source_report_id='rep1',
        support_only_flag=True,
        technical_status='READY',
    )

    guard = LevelAResponseGuard().validate(envelope)

    assert guard['valid'] is True
    assert guard['errors'] == []


def test_response_guard_rejects_forbidden_conclusive_fields():
    payload = {
        'request_id': 'req1',
        'case_id': 'case1',
        'support_only_flag': True,
        'technical_status': 'READY',
        'final_decision': 'GO',
    }

    guard = LevelAResponseGuard().validate(payload)

    assert guard['valid'] is False
    assert 'final_decision' in guard['forbidden_fields']


def test_response_guard_classifies_support_only_payload_without_sensitive_targets():
    payload = {
        'request_id': 'req1',
        'case_id': 'case1',
        'trace_id': 'trace1',
        'support_only_flag': True,
        'technical_status': 'READY',
        'source_ids': ['src1'],
        'valid_citation_ids': ['cit1'],
        'vigenza_status_summary': {'VIGENTE_VERIFICATA': 1},
        'crossref_status_summary': {'RESOLVED': 1},
        'coverage_status': 'ADEQUATE',
        'audit_complete': True,
        'shadow_id': 'shadow1',
    }

    result = LevelAResponseGuard().classify(payload)

    assert result['intake_decision'] == 'ACCEPT_SUPPORT_ONLY'
    assert result['requires_quarantine'] is False
    assert 'A4_M07Governor' in result['forbidden_level_a_targets']
    assert 'A7_OutputAuthorizer' in result['forbidden_level_a_targets']


def test_response_guard_quarantines_m07_contamination():
    payload = {
        'request_id': 'req1',
        'case_id': 'case1',
        'trace_id': 'trace1',
        'support_only_flag': True,
        'technical_status': 'READY',
        'documentary_packet': {
            'source_set': ['src1'],
            'citation_set': ['cit1'],
            'vigenza_findings': ['vig1'],
            'cross_reference_findings': ['xref1'],
            'coverage_findings': ['cov1'],
            'audit_trace': {'events': 1},
            'shadow_trace': {'events': 1},
            'm07_closed': True,
        },
    }

    result = LevelAResponseGuard().classify(payload)

    assert result['intake_decision'] == 'QUARANTINE'
    assert 'Q_M07_BOUNDARY' in result['quarantine_codes']
