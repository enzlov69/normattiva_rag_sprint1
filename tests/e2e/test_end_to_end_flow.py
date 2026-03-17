from src.interface.level_b_package_types import LevelBDeliveryPackage
from src.runtime.flow_runner import EndToEndFlowRunner


def build_package(**overrides):
    data = dict(
        record_id='pkgrec_001',
        record_type='LevelBDeliveryPackage',
        package_id='pkg_001',
        case_id='case_001',
        report_id='report_001',
        report_status='READY',
        support_only_flag=True,
        source_ids=['source_tuel'],
        valid_citation_ids=['citation_001'],
        blocked_citation_ids=[],
        citation_status_summary={'VALID': 1},
        vigenza_status_summary={'VIGENTE_VERIFICATA': 1},
        crossref_status_summary={'RESOLVED': 1},
        coverage_ref_id='cov_001',
        coverage_status='ADEQUATE',
        m07_ref_id='m07_001',
        m07_status='COMPLETE',
        warnings=[],
        errors=[],
        block_ids=[],
        block_codes=[],
        audit_complete=True,
        audit_checked_events=4,
        audit_missing_phases=[],
        audit_missing_modules=[],
        shadow_id='shadow_001',
        executed_modules=['B10_HybridRetriever'],
        documents_seen=['source_tuel'],
        norm_units_seen=['norm_001'],
        shadow_block_codes=[],
        package_status='READY',
        trace_id='trace_001',
    )
    data.update(overrides)
    return LevelBDeliveryPackage(**data)


def test_end_to_end_authorized_technical_output():
    runner = EndToEndFlowRunner()
    package = build_package()

    result = runner.run(package, requested_output_type='RAC_DRAFT')

    assert result.final_runtime_status == 'AUTHORIZED_TECHNICAL_OUTPUT'
    assert result.go_final_status == 'GO_FINAL_POSSIBLE'
    assert result.authorization_status == 'OUTPUT_AUTHORIZATION_ALLOWED'
    assert result.support_only_flag is True


def test_end_to_end_blocked_flow_on_vigenza_and_blocks():
    runner = EndToEndFlowRunner()
    package = build_package(
        vigenza_status_summary={'VIGENZA_INCERTA': 1},
        block_codes=['VIGENZA_UNCERTAIN'],
        package_status='BLOCKED',
    )

    result = runner.run(package, requested_output_type='RAC_DRAFT')

    assert result.final_runtime_status == 'BLOCKED'
    assert result.authorization_status == 'OUTPUT_AUTHORIZATION_DENIED'
    assert 'VIGENZA_UNCERTAIN' in result.block_codes


def test_end_to_end_support_only_when_warnings_persist():
    runner = EndToEndFlowRunner()
    package = build_package(warnings=['coverage_warning'], package_status='READY_WITH_WARNINGS')

    result = runner.run(package, requested_output_type='RAC_DRAFT')

    assert result.final_runtime_status == 'SUPPORT_ONLY'
    assert result.authorization_status == 'OUTPUT_AUTHORIZATION_DENIED'
    assert 'support_only_review' in result.required_reviews
