from src.adapters.level_a_request_mapper import LevelARequestEnvelope
from src.compliance.compliance_types import FinalComplianceSnapshot
from src.finalization.go_final_controller import GoFinalController
from src.level_a.level_a_types import M07GovernanceRecord, PPAVOrchestrationRecord, RACDraftRecord


def build_envelope() -> LevelARequestEnvelope:
    return LevelARequestEnvelope(
        record_id='envrec_1',
        record_type='LevelARequestEnvelope',
        request_id='req_1',
        case_id='case_1',
        source_package_id='pkg_1',
        source_report_id='rep_1',
        support_only_flag=True,
        technical_status='READY_FOR_REVIEW',
        audit_complete=True,
        source_layer='A',
    )


def build_compliance(status: str = 'READY_FOR_REVIEW') -> FinalComplianceSnapshot:
    return FinalComplianceSnapshot(
        record_id='comprec_1',
        record_type='FinalComplianceSnapshot',
        compliance_id='comp_1',
        case_id='case_1',
        request_id='req_1',
        source_package_id='pkg_1',
        support_only_flag=True,
        technical_readiness_status=status,
        source_layer='A',
    )


def build_m07(status: str = 'READY_FOR_REVIEW') -> M07GovernanceRecord:
    return M07GovernanceRecord(
        record_id='m07rec_1',
        record_type='M07GovernanceRecord',
        m07_governance_id='m07_1',
        case_id='case_1',
        request_id='req_1',
        source_package_id='pkg_1',
        support_only_flag=True,
        m07_governance_status=status,
        m07_review_required=True,
        source_layer='A',
    )


def build_ppav() -> PPAVOrchestrationRecord:
    return PPAVOrchestrationRecord(
        record_id='ppavrec_1',
        record_type='PPAVOrchestrationRecord',
        orchestration_id='ppav_1',
        case_id='case_1',
        request_id='req_1',
        source_package_id='pkg_1',
        support_only_flag=True,
        ppav_status='OPEN',
        required_human_governance=True,
        source_layer='A',
    )


def build_rac(human_completion_required: bool = False) -> RACDraftRecord:
    return RACDraftRecord(
        record_id='racrec_1',
        record_type='RACDraftRecord',
        rac_draft_id='rac_1',
        case_id='case_1',
        request_id='req_1',
        source_package_id='pkg_1',
        support_only_flag=True,
        rac_draft_status='DRAFT',
        human_completion_required=human_completion_required,
        source_layer='A',
    )


def test_go_final_possible_only_when_all_core_conditions_are_satisfied() -> None:
    controller = GoFinalController()
    assessment = controller.assess(
        build_envelope(),
        build_compliance('READY_FOR_REVIEW'),
        ppav_record=build_ppav(),
        m07_record=build_m07('READY_FOR_REVIEW'),
        rac_draft=build_rac(False),
    )
    assert assessment.go_final_possible is True
    assert assessment.go_final_status == 'GO_FINAL_POSSIBLE'
    assert assessment.blocking_reasons == []



def test_go_final_not_possible_when_core_blocks_exist() -> None:
    controller = GoFinalController()
    envelope = build_envelope()
    envelope.block_codes = ['CITATION_INCOMPLETE']
    assessment = controller.assess(
        envelope,
        build_compliance('BLOCKED'),
        m07_record=build_m07('REQUIRED'),
        rac_draft=build_rac(False),
    )
    assert assessment.go_final_possible is False
    assert assessment.go_final_status == 'GO_FINAL_NOT_POSSIBLE'
    assert 'open_blocks_present' in assessment.blocking_reasons
    assert 'compliance_blocked' in assessment.blocking_reasons
    assert 'm07_not_governed' in assessment.blocking_reasons
