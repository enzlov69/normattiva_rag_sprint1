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


def test_level_b_response_cannot_populate_human_approval_fields():
    trace = LevelAResponseGuard().build_final_human_approval_trace(
        build_payload(
            approval='APPROVAL_GRANTED',
            human_approval=True,
        ),
        protected_module='A1_OrchestratorePPAV',
        review_completed=True,
        approved_by_human=False,
    )

    assert trace['approved_by_human'] is False
    assert trace['approval_status'] != 'APPROVAL_GRANTED'
    assert trace['blocked_by_condition'] == 'FORBIDDEN_FIELDS'


def test_approved_by_human_never_derives_from_support_only_or_response_content():
    trace = LevelAResponseGuard().build_final_human_approval_trace(
        build_payload(),
        protected_module='A1_OrchestratorePPAV',
    )

    assert trace['approved_by_human'] is False
    assert trace['approval_status'] != 'APPROVAL_GRANTED'


def test_final_components_do_not_receive_implicit_approval_from_level_b():
    guard = LevelAResponseGuard()
    compliance_trace = guard.build_final_human_approval_trace(
        build_payload(adapter_notes=['ready to sign']),
        protected_module='A5_FinalComplianceGate',
        review_completed=True,
        approved_by_human=False,
    )
    authorizer_trace = guard.build_final_human_approval_trace(
        build_payload(),
        protected_module='A7_OutputAuthorizer',
        review_completed=True,
        approved_by_human=False,
    )

    assert compliance_trace['approval_status'] != 'APPROVAL_GRANTED'
    assert authorizer_trace['approval_status'] != 'APPROVAL_GRANTED'
    assert authorizer_trace['blocked_by_condition'] == 'PROTECTED_MODULE_ISOLATION'


def test_approval_trace_remains_distinct_from_support_only_and_degradation_states():
    guard = LevelAResponseGuard()
    degraded_trace = guard.build_final_human_approval_trace(
        build_payload(
            technical_status='READY_WITH_WARNINGS',
            warnings=['coverage_warning'],
        ),
        protected_module='A1_OrchestratorePPAV',
    )
    granted_trace = guard.build_final_human_approval_trace(
        build_payload(),
        protected_module='A1_OrchestratorePPAV',
        review_completed=True,
        approved_by_human=True,
    )

    assert degraded_trace['approval_status'] != 'APPROVAL_GRANTED'
    assert granted_trace['approval_status'] == 'APPROVAL_GRANTED'
    assert granted_trace['approved_by_human'] is True
