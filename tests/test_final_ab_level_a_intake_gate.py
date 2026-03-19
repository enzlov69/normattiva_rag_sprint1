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
        'documents_seen': ['doc_1'],
        'norm_units_seen': ['norm_1'],
    }
    payload.update(overrides)
    return payload


def test_level_a_intake_gate_accepts_valid_response_as_support_only():
    result = LevelAResponseGuard().classify(build_payload())

    assert result['intake_decision'] == 'ACCEPT_SUPPORT_ONLY'
    assert result['requires_quarantine'] is False
    assert result['blocks_opponibility'] is True
    assert 'A5_FinalComplianceGate' in result['forbidden_level_a_targets']
    assert 'A7_OutputAuthorizer' in result['forbidden_level_a_targets']


def test_level_a_intake_gate_degrades_warning_response():
    result = LevelAResponseGuard().classify(
        build_payload(
            technical_status='READY_WITH_WARNINGS',
            warnings=['coverage_warning'],
        )
    )

    assert result['intake_decision'] == 'ACCEPT_WITH_DEGRADATION'
    assert result['requires_human_review'] is True
    assert result['requires_quarantine'] is False


def test_level_a_intake_gate_quarantines_forbidden_field_response():
    result = LevelAResponseGuard().classify(
        build_payload(
            final_decision='GO',
        )
    )

    assert result['intake_decision'] == 'QUARANTINE'
    assert 'Q_FORBIDDEN_FIELDS' in result['quarantine_codes']


def test_level_a_intake_gate_rejects_blocked_runtime_response():
    result = LevelAResponseGuard().classify(
        build_payload(
            technical_status='BLOCKED',
            block_codes=['VIGENZA_UNCERTAIN'],
        )
    )

    assert result['intake_decision'] == 'REJECT'
    assert result['blocks_opponibility'] is True
    assert 'VIGENZA_UNCERTAIN' in result['critical_blocks']
