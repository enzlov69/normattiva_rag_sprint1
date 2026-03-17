from src.adapters.level_a_request_mapper import LevelARequestEnvelope
from src.level_a.rac_builder import RACBuilder


def test_rac_builder_creates_non_conclusive_draft_with_support_refs() -> None:
    envelope = LevelARequestEnvelope(
        record_id='reqrec_3',
        record_type='LevelARequestEnvelope',
        request_id='req_3',
        case_id='case_003',
        source_package_id='pkg_3',
        support_only_flag=True,
        technical_status='BLOCKED',
        source_ids=['source_1'],
        valid_citation_ids=['cit_1', 'cit_2'],
        blocked_citation_ids=['cit_blocked'],
        warnings=['warning_1'],
        block_codes=['CITATION_INCOMPLETE'],
        coverage_status='INADEQUATE',
        source_layer='A',
        trace_id='trace_003',
    )

    draft = RACBuilder().build_draft(envelope)

    assert draft.support_only_flag is True
    assert draft.rac_draft_status == 'DRAFT_WITH_BLOCKS'
    assert draft.documentary_support_refs == ['source_1', 'cit_1', 'cit_2']
    assert draft.blocked_citation_ids == ['cit_blocked']
    assert draft.human_completion_required is True
