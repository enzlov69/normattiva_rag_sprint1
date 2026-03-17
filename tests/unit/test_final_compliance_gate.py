from src.adapters.level_a_request_mapper import LevelARequestEnvelope
from src.compliance.final_compliance_gate import FinalComplianceGate
from src.level_a.level_a_types import M07GovernanceRecord, RACDraftRecord


def _envelope(**overrides) -> LevelARequestEnvelope:
    base = dict(
        record_id='reqrec_1',
        record_type='LevelARequestEnvelope',
        request_id='req_1',
        case_id='case_001',
        source_package_id='pkg_1',
        source_report_id='report_1',
        support_only_flag=True,
        technical_status='READY',
        source_ids=['source_1'],
        valid_citation_ids=['cit_1'],
        blocked_citation_ids=[],
        citation_status_summary={'VALID': 1},
        vigenza_status_summary={'VIGENTE_VERIFICATA': 1},
        crossref_status_summary={'RESOLVED': 1},
        coverage_status='READY',
        m07_status='READY',
        warnings=[],
        errors=[],
        block_ids=[],
        block_codes=[],
        audit_complete=True,
        audit_checked_events=3,
        trace_id='trace_001',
        source_layer='A',
    )
    base.update(overrides)
    return LevelARequestEnvelope(**base)


def test_final_compliance_gate_marks_ready_for_review_without_critical_failures() -> None:
    result = FinalComplianceGate().evaluate(_envelope())

    assert result.technical_readiness_status == 'READY_FOR_REVIEW'
    assert result.support_only_flag is True
    assert 'GO' not in result.technical_readiness_status


def test_final_compliance_gate_marks_support_only_when_only_warnings_exist() -> None:
    result = FinalComplianceGate().evaluate(_envelope(warnings=['warning_1']))

    assert result.technical_readiness_status == 'SUPPORT_ONLY'
    assert result.open_block_codes == []


def test_final_compliance_gate_blocks_on_critical_gaps() -> None:
    envelope = _envelope(
        block_codes=['CROSSREF_UNRESOLVED', 'AUDIT_INCOMPLETE'],
        crossref_status_summary={'UNRESOLVED': 1},
        audit_complete=False,
    )
    m07_record = M07GovernanceRecord(
        record_id='m07rec_1',
        record_type='M07GovernanceRecord',
        m07_governance_id='m07gov_1',
        case_id='case_001',
        request_id='req_1',
        source_package_id='pkg_1',
        source_layer='A',
    )
    rac_draft = RACDraftRecord(
        record_id='racrec_1',
        record_type='RACDraftRecord',
        rac_draft_id='rac_1',
        case_id='case_001',
        request_id='req_1',
        source_package_id='pkg_1',
        source_layer='A',
    )

    result = FinalComplianceGate().evaluate(envelope, m07_record=m07_record, rac_draft=rac_draft)

    assert result.technical_readiness_status == 'BLOCKED'
    assert result.audit_ok is False
    assert result.crossref_ok is False
    assert 'rinvii essenziali non risolti' in result.missing_requirements
