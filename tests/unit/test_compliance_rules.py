from src.adapters.level_a_request_mapper import LevelARequestEnvelope
from src.compliance.compliance_rules import ComplianceRules
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


def test_compliance_rules_pass_on_clean_technical_state() -> None:
    checks = ComplianceRules().evaluate(_envelope())
    assert all(check.passed for check in checks)


def test_compliance_rules_detect_vigenza_and_m07_gaps() -> None:
    envelope = _envelope(
        vigenza_status_summary={'VIGENZA_INCERTA': 1},
        m07_status='PARTIAL',
        block_codes=['VIGENZA_UNCERTAIN', 'M07_REQUIRED'],
    )
    m07_record = M07GovernanceRecord(
        record_id='m07rec_1',
        record_type='M07GovernanceRecord',
        m07_governance_id='m07gov_1',
        case_id='case_001',
        request_id='req_1',
        source_package_id='pkg_1',
        block_codes=['M07_REQUIRED'],
        source_layer='A',
    )
    rac_draft = RACDraftRecord(
        record_id='racrec_1',
        record_type='RACDraftRecord',
        rac_draft_id='rac_1',
        case_id='case_001',
        request_id='req_1',
        source_package_id='pkg_1',
        blocked_citation_ids=['cit_2'],
        source_layer='A',
    )

    checks = {check.rule_name: check for check in ComplianceRules().evaluate(envelope, m07_record=m07_record, rac_draft=rac_draft)}

    assert checks['vigenza'].passed is False
    assert checks['m07'].passed is False
    assert checks['citations'].passed is False
