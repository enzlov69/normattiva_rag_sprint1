from src.audit.audit_integrity import AuditIntegrityResult
from src.interface.level_b_package_builder import LevelBPackageBuilder
from src.models.shadow_trace import ShadowTrace
from src.reporting.report_types import TechnicalReport


def test_level_b_package_builder_builds_support_only_package() -> None:
    report = TechnicalReport(
        record_id='reportrec_1',
        record_type='TechnicalReport',
        report_id='report_1',
        case_id='case_001',
        source_ids=['source_1'],
        valid_citation_ids=['cit_1'],
        blocked_citation_ids=['cit_2'],
        citation_status_summary={'VALID': 1, 'BLOCKED': 1},
        vigenza_status_summary={'VIGENTE_VERIFICATA': 1},
        crossref_status_summary={'RESOLVED': 1},
        coverage_ref_id='cov_1',
        coverage_status='READY',
        m07_ref_id='m07_1',
        m07_status='READY',
        warnings=['warning_1'],
        errors=[],
        block_ids=['block_1'],
        block_codes=['CITATION_INCOMPLETE'],
        report_status='BLOCKED',
        trace_id='trace_001',
    )
    audit_result = AuditIntegrityResult(complete=True, checked_events=4)
    shadow = ShadowTrace(
        record_id='shadowrec_1',
        record_type='ShadowTrace',
        shadow_id='shadow_1',
        case_id='case_001',
        executed_modules=['RetrievalService', 'ReportBuilder'],
        documents_seen=['source_1'],
        norm_units_seen=['norm_1'],
        blocks=['CITATION_INCOMPLETE'],
    )

    package = LevelBPackageBuilder().build(
        technical_report=report,
        audit_integrity_result=audit_result,
        shadow_trace=shadow,
    )

    assert package.case_id == 'case_001'
    assert package.report_id == 'report_1'
    assert package.support_only_flag is True
    assert package.audit_complete is True
    assert package.shadow_id == 'shadow_1'
    assert package.package_status == 'BLOCKED'
    assert package.block_codes == ['CITATION_INCOMPLETE']


def test_level_b_package_builder_marks_warning_status_when_audit_is_incomplete() -> None:
    report = TechnicalReport(
        record_id='reportrec_2',
        record_type='TechnicalReport',
        report_id='report_2',
        case_id='case_002',
        warnings=[],
        errors=[],
        block_ids=[],
        block_codes=[],
        report_status='READY',
    )
    audit_result = AuditIntegrityResult(complete=False, missing_phases=['INGESTION'], checked_events=0)

    package = LevelBPackageBuilder().build(
        technical_report=report,
        audit_integrity_result=audit_result,
    )

    assert package.audit_complete is False
    assert package.audit_missing_phases == ['INGESTION']
    assert package.package_status == 'READY_WITH_WARNINGS'
