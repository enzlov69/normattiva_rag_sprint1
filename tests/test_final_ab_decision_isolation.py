from src.adapters.level_a_response_guard import LevelAResponseGuard


def build_payload(**overrides):
    payload = {
        'response_id': 'resp_001',
        'request_id': 'req_001',
        'case_id': 'case_001',
        'trace_id': 'trace_001',
        'support_only_flag': True,
        'technical_status': 'READY',
        'source_ids': ['source_1'],
        'valid_citation_ids': ['citation_1'],
        'vigenza_status_summary': {'VIGENTE_VERIFICATA': 1},
        'crossref_status_summary': {'RESOLVED': 1},
        'coverage_status': 'ADEQUATE',
        'warnings': [],
        'errors': [],
        'block_codes': [],
        'audit_complete': True,
        'shadow_id': 'shadow_001',
    }
    payload.update(overrides)
    return payload


def test_decision_isolation_blocks_m07_governor_on_m07_contamination():
    log = LevelAResponseGuard().build_decision_isolation_log(
        build_payload(
            documentary_packet={
                'source_set': ['source_1'],
                'citation_set': ['citation_1'],
                'vigenza_findings': ['vig_1'],
                'cross_reference_findings': ['xref_1'],
                'coverage_findings': ['cov_1'],
                'audit_trace': {'events': 1},
                'shadow_trace': {'events': 1},
                'm07_closed': True,
            }
        ),
        protected_module='A4_M07Governor',
    )

    assert log['source_allowed'] is False
    assert log['violation_detected'] is True
    assert log['violation_type'] == 'M07_CONTAMINATION'


def test_decision_isolation_blocks_rac_builder_on_decisional_fields():
    log = LevelAResponseGuard().build_decision_isolation_log(
        build_payload(final_decision='GO'),
        protected_module='A6_RACBuilder',
    )

    assert log['source_allowed'] is False
    assert log['violation_type'] == 'FORBIDDEN_FIELDS'


def test_decision_isolation_blocks_final_compliance_gate_on_authorization_semantics():
    log = LevelAResponseGuard().build_decision_isolation_log(
        build_payload(adapter_notes=['ready to sign', 'final compliance passed']),
        protected_module='A5_FinalComplianceGate',
    )

    assert log['source_allowed'] is False
    assert log['violation_type'] == 'AUTHORIZATION_LIKE_SEMANTICS'


def test_decision_isolation_blocks_output_authorizer_on_direct_b_to_a_basis():
    log = LevelAResponseGuard().build_decision_isolation_log(
        build_payload(),
        protected_module='A7_OutputAuthorizer',
    )

    assert log['source_allowed'] is False
    assert log['violation_detected'] is True
    assert log['blocks_opponibility'] is True
