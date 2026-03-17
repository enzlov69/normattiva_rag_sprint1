from src.adapters.level_a_request_mapper import LevelARequestEnvelope
from src.level_a.orchestrator_ppav import PPAVOrchestrator


def _envelope(**overrides) -> LevelARequestEnvelope:
    base = dict(
        record_id='reqrec_1',
        record_type='LevelARequestEnvelope',
        request_id='req_1',
        case_id='case_001',
        source_package_id='pkg_1',
        support_only_flag=True,
        technical_status='BLOCKED',
        source_ids=['source_1'],
        valid_citation_ids=['cit_1'],
        blocked_citation_ids=['cit_blocked'],
        warnings=['warning_1'],
        block_codes=['CITATION_INCOMPLETE'],
        coverage_status='INADEQUATE',
        m07_status='PARTIAL',
        audit_complete=False,
        trace_id='trace_001',
        source_layer='A',
    )
    base.update(overrides)
    return LevelARequestEnvelope(**base)


def test_orchestrator_starts_support_only_workflow() -> None:
    workflow = PPAVOrchestrator().start_workflow(_envelope())

    assert workflow.case_id == 'case_001'
    assert workflow.support_only_flag is True
    assert workflow.workflow_status == 'OPEN_WITH_BLOCKS'
    assert 'M07_GOVERNOR' in workflow.next_modules
    assert 'RAC_BUILDER' in workflow.next_modules


def test_orchestrator_builds_ppav_record_without_conclusive_status() -> None:
    record = PPAVOrchestrator().orchestrate(_envelope())

    assert record.support_only_flag is True
    assert record.ppav_status == 'OPEN_WITH_BLOCKS'
    assert 'PPAV_REVIEW' in record.requested_modules
    assert record.required_human_governance is True
    assert all(status not in {'GO', 'NO_GO'} for status in [record.ppav_status])
