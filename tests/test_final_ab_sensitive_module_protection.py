from src.adapters.level_a_response_guard import LevelAResponseGuard


def build_payload(**overrides):
    payload = {
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


def test_sensitive_module_protection_blocks_m07_closure_semantics():
    result = LevelAResponseGuard().classify(
        build_payload(
            documentary_packet={
                'source_set': ['source_1'],
                'citation_set': ['citation_1'],
                'vigenza_findings': ['vig_1'],
                'cross_reference_findings': ['xref_1'],
                'coverage_findings': ['coverage_1'],
                'audit_trace': {'events': 1},
                'shadow_trace': {'events': 1},
                'm07_closed': True,
            }
        )
    )

    assert result['intake_decision'] == 'QUARANTINE'
    assert 'Q_M07_BOUNDARY' in result['quarantine_codes']
    assert 'A4_M07Governor' in result['forbidden_level_a_targets']


def test_sensitive_module_protection_blocks_rac_builder_from_decisional_payloads():
    result = LevelAResponseGuard().classify(
        build_payload(
            final_decision='GO',
        )
    )

    assert result['intake_decision'] == 'QUARANTINE'
    assert 'A6_RACBuilder' in result['forbidden_level_a_targets']


def test_sensitive_module_protection_blocks_final_compliance_gate_authorization_semantics():
    result = LevelAResponseGuard().classify(
        build_payload(
            adapter_notes=['ready to sign', 'final compliance passed'],
        )
    )

    assert result['intake_decision'] == 'QUARANTINE'
    assert 'Q_AUTHORIZATION_SEMANTICS' in result['quarantine_codes']
    assert 'A5_FinalComplianceGate' in result['forbidden_level_a_targets']


def test_sensitive_module_protection_never_allows_direct_output_authorizer_consumption():
    result = LevelAResponseGuard().classify(build_payload())

    assert result['intake_decision'] == 'ACCEPT_SUPPORT_ONLY'
    assert 'A7_OutputAuthorizer' in result['forbidden_level_a_targets']
    assert 'A7_OutputAuthorizer' not in result['allowed_level_a_targets']
