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


def test_support_only_response_requires_review_but_is_not_approval():
    gate = LevelAResponseGuard().evaluate_manual_review_gate(
        build_payload(),
        protected_module='A1_OrchestratorePPAV',
    )

    assert gate['review_required'] is True
    assert gate['review_status'] == 'REVIEW_REQUIRED'
    assert gate['approval_status'] == 'APPROVAL_DENIED'
    assert gate['support_only_flag'] is True


def test_strong_signals_require_escalation():
    gate = LevelAResponseGuard().evaluate_manual_review_gate(
        build_payload(
            technical_status='BLOCKED',
            block_codes=['VIGENZA_UNCERTAIN'],
        ),
        protected_module='A1_OrchestratorePPAV',
    )

    assert gate['review_required'] is True
    assert gate['escalation_flag'] is True
    assert gate['approval_status'] == 'ESCALATION_REQUIRED'


def test_m07_or_authorization_contamination_cannot_bypass_review():
    guard = LevelAResponseGuard()
    m07_gate = guard.evaluate_manual_review_gate(
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
    auth_gate = guard.evaluate_manual_review_gate(
        build_payload(adapter_notes=['ready to sign']),
        protected_module='A5_FinalComplianceGate',
    )

    assert m07_gate['escalation_flag'] is True
    assert m07_gate['blocked_by_condition'] == 'M07_CONTAMINATION'
    assert auth_gate['escalation_flag'] is True
    assert auth_gate['blocked_by_condition'] == 'AUTHORIZATION_LIKE_SEMANTICS'


def test_manual_review_gate_keeps_audit_and_trace_linkage():
    guard = LevelAResponseGuard()
    gate = guard.evaluate_manual_review_gate(
        build_payload(),
        protected_module='A1_OrchestratorePPAV',
    )
    trace = guard.build_final_human_approval_trace(
        build_payload(),
        protected_module='A1_OrchestratorePPAV',
        review_event_id=gate['review_event_id'],
        review_completed=True,
        approved_by_human=False,
    )

    assert gate['consumption_audit_event_id']
    assert gate['decision_isolation_log_id']
    assert trace['review_event_id'] == gate['review_event_id']
    assert trace['trace_id'] == 'trace_001'
    assert trace['case_id'] == 'case_001'
