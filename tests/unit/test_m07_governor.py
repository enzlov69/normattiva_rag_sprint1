from src.adapters.level_a_request_mapper import LevelARequestEnvelope
from src.level_a.m07_governor import M07Governor


def test_m07_governor_marks_required_when_m07_is_partial() -> None:
    envelope = LevelARequestEnvelope(
        record_id='reqrec_2',
        record_type='LevelARequestEnvelope',
        request_id='req_2',
        case_id='case_002',
        source_package_id='pkg_2',
        support_only_flag=True,
        technical_status='READY_WITH_WARNINGS',
        blocked_citation_ids=['cit_blocked'],
        block_codes=['M07_REQUIRED'],
        m07_ref_id='m07_2',
        m07_status='PARTIAL',
        audit_complete=False,
        source_layer='A',
        trace_id='trace_002',
    )

    result = M07Governor().govern(envelope)

    assert result.support_only_flag is True
    assert result.m07_governance_status == 'REQUIRED'
    assert result.m07_review_required is True
    assert 'm07_review' in result.missing_elements
    assert 'M07_REQUIRED' in result.block_codes
