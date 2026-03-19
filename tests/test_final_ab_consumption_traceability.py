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
        'documents_seen': ['doc_1'],
        'norm_units_seen': ['norm_1'],
    }
    payload.update(overrides)
    return payload


def test_valid_response_generates_coherent_consumption_audit_trail():
    trail = LevelAResponseGuard().build_consumption_audit_trail(
        build_payload(),
        target_level_a_module='A1_OrchestratorePPAV',
    )

    assert trail['intake_decision'] == 'ACCEPT_SUPPORT_ONLY'
    assert trail['consumption_mode'] == 'DOCUMENTARY_SUPPORT_ONLY'
    assert trail['support_only_flag'] is True
    assert trail['degraded_flag'] is False
    assert trail['quarantine_flag'] is False
    assert trail['rejected_flag'] is False
    assert trail['trace_id'] == 'trace_001'
    assert trail['case_id'] == 'case_001'
    assert trail['source_response_id'] == 'resp_001'


def test_degraded_response_generates_degraded_consumption_trail():
    trail = LevelAResponseGuard().build_consumption_audit_trail(
        build_payload(
            technical_status='READY_WITH_WARNINGS',
            warnings=['coverage_warning'],
        ),
        target_level_a_module='A1_OrchestratorePPAV',
    )

    assert trail['intake_decision'] == 'ACCEPT_WITH_DEGRADATION'
    assert trail['consumption_mode'] == 'DEGRADED_SUPPORT'
    assert trail['degraded_flag'] is True
    assert trail['quarantine_flag'] is False


def test_quarantined_and_rejected_responses_are_not_marked_as_consumed():
    guard = LevelAResponseGuard()
    quarantined = guard.build_consumption_audit_trail(
        build_payload(final_decision='GO'),
        target_level_a_module='A1_OrchestratorePPAV',
    )
    rejected = guard.build_consumption_audit_trail(
        build_payload(
            technical_status='BLOCKED',
            block_codes=['VIGENZA_UNCERTAIN'],
        ),
        target_level_a_module='A1_OrchestratorePPAV',
    )

    assert quarantined['consumption_mode'] == 'QUARANTINED_NOT_CONSUMED'
    assert quarantined['quarantine_flag'] is True
    assert rejected['consumption_mode'] == 'REJECTED_NOT_CONSUMED'
    assert rejected['rejected_flag'] is True
