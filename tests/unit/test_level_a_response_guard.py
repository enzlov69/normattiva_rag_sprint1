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
