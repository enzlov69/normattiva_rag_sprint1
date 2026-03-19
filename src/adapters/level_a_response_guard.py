from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Union

from src.adapters.level_a_request_mapper import LevelARequestEnvelope
from src.utils.ids import build_id
from src.utils.timestamps import utc_now_iso


class LevelAResponseGuard:
    SUPPORT_ONLY_TARGETS = (
        'A1_OrchestratorePPAV',
        'A8_AuditLogger',
        'A9_SHADOWTracer',
    )
    SENSITIVE_TARGETS = (
        'A4_M07Governor',
        'A6_RACBuilder',
        'A5_FinalComplianceGate',
        'A7_OutputAuthorizer',
    )
    QUARANTINE_CODES = {
        'forbidden_fields': 'Q_FORBIDDEN_FIELDS',
        'traceability_gap': 'Q_TRACEABILITY_GAP',
        'documentary_gap': 'Q_MISSING_DOCUMENTARY_PACKET',
        'm07_boundary': 'Q_M07_BOUNDARY',
        'authorization_semantics': 'Q_AUTHORIZATION_SEMANTICS',
        'critical_blocks': 'Q_UNRESOLVED_CRITICAL_BLOCKS',
    }
    CRITICAL_BLOCK_CODES = {
        'AUDIT_INCOMPLETE',
        'CORPUS_MISSING',
        'M07_REQUIRED',
        'OUTPUT_NOT_OPPONIBLE',
        'RAG_SCOPE_VIOLATION',
        'SOURCE_UNVERIFIED',
        'VIGENZA_UNCERTAIN',
    }
    FORBIDDEN_FIELDS = {
        'final_decision',
        'decision',
        'approval',
        'human_approval',
        'final_applicability',
        'legal_conclusion',
        'motivazione_finale',
        'final_motivation',
        'output_authorized',
        'final_compliance_passed',
        'go_finale',
        'no_go_finale',
        'm07_closed',
        'ppav_closed',
        'rac_finalizzato',
        'normative_prevalence_choice',
        'legal_applicability_decision',
        'authorization_status',
        'final_gate_status',
    }
    FORBIDDEN_SEMANTICS = (
        'decisione finale',
        'final decision',
        'output authorized',
        'authorization allowed',
        'ready to sign',
        'final compliance passed',
        'case resolved',
        'm07 closed',
    )
    CONSUMPTION_MODES = {
        'ACCEPT_SUPPORT_ONLY': 'DOCUMENTARY_SUPPORT_ONLY',
        'ACCEPT_WITH_DEGRADATION': 'DEGRADED_SUPPORT',
        'QUARANTINE': 'QUARANTINED_NOT_CONSUMED',
        'REJECT': 'REJECTED_NOT_CONSUMED',
    }
    ESCALATION_REVIEW_CODES = {
        'FORBIDDEN_FIELDS',
        'M07_CONTAMINATION',
        'AUTHORIZATION_LIKE_SEMANTICS',
        'UNRESOLVED_CRITICAL_BLOCKS',
        'SUPPORT_ONLY_BREACH',
    }

    def validate(self, payload: Union[LevelARequestEnvelope, Dict[str, Any]]) -> Dict[str, Any]:
        normalized = self._normalize(payload)
        forbidden_present = sorted(self.FORBIDDEN_FIELDS.intersection(normalized.keys()))
        errors: List[str] = []

        if normalized.get('support_only_flag') is not True:
            errors.append('Il pacchetto inoltrato al Livello A deve restare tecnico-documentale.')

        if normalized.get('technical_status') == 'GO':
            errors.append('Il bridge tecnico non può esprimere GO finale.')

        if forbidden_present:
            errors.append('Sono presenti campi conclusivi vietati nel bridge verso il Livello A.')

        return {
            'valid': not errors and not forbidden_present,
            'forbidden_fields': forbidden_present,
            'errors': errors,
            'normalized_payload': normalized,
        }

    def classify(self, payload: Union[LevelARequestEnvelope, Dict[str, Any]]) -> Dict[str, Any]:
        normalized = self._normalize(payload)
        validation = self.validate(normalized)
        packet = self._extract_documentary_packet(normalized)

        documentary_gaps = self._documentary_gaps(packet)
        traceability_gaps = self._traceability_gaps(normalized, packet)
        forbidden_semantics = self._find_semantic_markers(normalized, self.FORBIDDEN_SEMANTICS)
        critical_blocks = self._critical_blocks(normalized, packet)
        status = str(normalized.get('technical_status') or normalized.get('response_status') or normalized.get('package_status') or '').upper()

        quarantine_codes: List[str] = []
        reasons: List[str] = list(validation['errors'])

        if validation['forbidden_fields']:
            quarantine_codes.append(self.QUARANTINE_CODES['forbidden_fields'])
        if self._has_m07_contamination(normalized, packet):
            quarantine_codes.append(self.QUARANTINE_CODES['m07_boundary'])
            reasons.append('Il supporto documentale non puo chiudere o certificare M07.')
        if forbidden_semantics:
            quarantine_codes.append(self.QUARANTINE_CODES['authorization_semantics'])
            reasons.append('Sono presenti semantiche autorizzative o decisorie non ammissibili nel Livello B.')
        if traceability_gaps:
            quarantine_codes.append(self.QUARANTINE_CODES['traceability_gap'])
            reasons.append('Sono presenti gap di traceability o audit/SHADOW.')
        if documentary_gaps:
            quarantine_codes.append(self.QUARANTINE_CODES['documentary_gap'])
            reasons.append('Il documentary packet minimo non e completo.')
        if critical_blocks and status not in {'BLOCKED', 'REJECTED', 'ERROR'}:
            quarantine_codes.append(self.QUARANTINE_CODES['critical_blocks'])
            reasons.append('Sono presenti blocchi critici non risolti da governare nel Livello A.')

        decision = 'ACCEPT_SUPPORT_ONLY'
        requires_human_review = False
        requires_quarantine = False

        if status in {'BLOCKED', 'REJECTED', 'ERROR'}:
            decision = 'REJECT'
            requires_human_review = True
            reasons.append('La response runtime non e consumabile per stato tecnico bloccante.')
        elif quarantine_codes:
            decision = 'QUARANTINE'
            requires_human_review = True
            requires_quarantine = True
        elif self._should_degrade(normalized, packet, status):
            decision = 'ACCEPT_WITH_DEGRADATION'
            requires_human_review = True

        source_signal_class = self._source_signal_class(decision, critical_blocks, traceability_gaps, quarantine_codes, normalized, packet)
        source_runtime_effect = self._source_runtime_effect(decision)

        return {
            'intake_decision': decision,
            'source_status': status or 'READY',
            'source_signal_class': source_signal_class,
            'source_runtime_effect': source_runtime_effect,
            'consumption_mode': self.CONSUMPTION_MODES[decision],
            'allowed_level_a_targets': list(self.SUPPORT_ONLY_TARGETS),
            'forbidden_level_a_targets': list(self.SENSITIVE_TARGETS),
            'requires_human_review': requires_human_review,
            'requires_quarantine': requires_quarantine,
            'blocks_opponibility': True,
            'quarantine_codes': self._unique(quarantine_codes),
            'forbidden_fields': validation['forbidden_fields'],
            'documentary_gaps': documentary_gaps,
            'traceability_gaps': traceability_gaps,
            'critical_blocks': critical_blocks,
            'errors': self._unique(reasons),
            'normalized_payload': normalized,
        }

    def build_consumption_audit_trail(
        self,
        payload: Union[LevelARequestEnvelope, Dict[str, Any]],
        *,
        target_level_a_module: str,
        source_response_id: str = '',
    ) -> Dict[str, Any]:
        classification = self.classify(payload)
        normalized = classification['normalized_payload']

        return {
            'event_id': build_id('aconsaudit'),
            'trace_id': normalized.get('trace_id', ''),
            'case_id': normalized.get('case_id', ''),
            'source_response_id': source_response_id or normalized.get('response_id') or normalized.get('source_response_id') or normalized.get('request_id', ''),
            'intake_decision': classification['intake_decision'],
            'source_status': classification['source_status'],
            'source_signal_class': classification['source_signal_class'],
            'source_runtime_effect': classification['source_runtime_effect'],
            'target_level_a_module': target_level_a_module,
            'consumption_mode': classification['consumption_mode'],
            'support_only_flag': normalized.get('support_only_flag') is True,
            'degraded_flag': classification['intake_decision'] == 'ACCEPT_WITH_DEGRADATION',
            'quarantine_flag': classification['intake_decision'] == 'QUARANTINE',
            'rejected_flag': classification['intake_decision'] == 'REJECT',
            'allowed_use': self._allowed_use_for_decision(classification['intake_decision']),
            'forbidden_use': self._forbidden_use_for_decision(classification['intake_decision']),
            'audit_timestamp': utc_now_iso(),
            'notes': list(classification['errors']),
        }

    def build_decision_isolation_log(
        self,
        payload: Union[LevelARequestEnvelope, Dict[str, Any]],
        *,
        protected_module: str,
        source_artifact_type: str = 'final_ab_runtime_response',
    ) -> Dict[str, Any]:
        classification = self.classify(payload)
        normalized = classification['normalized_payload']
        source_allowed = protected_module in classification['allowed_level_a_targets']
        violation_type = self._violation_type(classification, normalized)
        violation_detected = (protected_module in classification['forbidden_level_a_targets']) or bool(violation_type)

        return {
            'log_id': build_id('aisolog'),
            'trace_id': normalized.get('trace_id', ''),
            'case_id': normalized.get('case_id', ''),
            'protected_module': protected_module,
            'source_artifact_type': source_artifact_type,
            'source_allowed': source_allowed,
            'isolation_result': 'CONSUMPTION_DENIED' if violation_detected else 'ALLOWED_SUPPORT_PATH',
            'violation_detected': violation_detected,
            'violation_type': violation_type or ('PROTECTED_MODULE_ISOLATION' if violation_detected else ''),
            'manual_review_required': classification['requires_human_review'] or violation_detected,
            'blocks_opponibility': True,
            'notes': list(classification['errors']),
        }

    def evaluate_manual_review_gate(
        self,
        payload: Union[LevelARequestEnvelope, Dict[str, Any]],
        *,
        protected_module: str,
    ) -> Dict[str, Any]:
        audit_trail = self.build_consumption_audit_trail(
            payload,
            target_level_a_module=protected_module,
        )
        isolation_log = self.build_decision_isolation_log(
            payload,
            protected_module=protected_module,
        )
        classification = self.classify(payload)
        normalized = classification['normalized_payload']
        blocked_by_condition = isolation_log['violation_type']
        if not blocked_by_condition and classification['intake_decision'] == 'QUARANTINE':
            blocked_by_condition = 'QUARANTINE_STATE'
        if not blocked_by_condition and classification['intake_decision'] == 'REJECT':
            blocked_by_condition = 'REJECT_STATE'
        escalation_flag = self._requires_escalation(classification, isolation_log)

        return {
            'review_event_id': build_id('amanrev'),
            'trace_id': normalized.get('trace_id', ''),
            'case_id': normalized.get('case_id', ''),
            'source_response_id': normalized.get('response_id') or normalized.get('source_response_id') or normalized.get('request_id', ''),
            'protected_module': protected_module,
            'intake_decision': classification['intake_decision'],
            'review_required': True,
            'review_status': 'REVIEW_REQUIRED',
            'approval_required': True,
            'approval_status': 'ESCALATION_REQUIRED' if escalation_flag else 'APPROVAL_DENIED',
            'escalation_flag': escalation_flag,
            'blocked_by_condition': blocked_by_condition,
            'consumption_audit_event_id': audit_trail['event_id'],
            'decision_isolation_log_id': isolation_log['log_id'],
            'consumption_mode': classification['consumption_mode'],
            'support_only_flag': normalized.get('support_only_flag') is True,
            'audit_timestamp': utc_now_iso(),
            'notes': list(classification['errors']),
        }

    def build_final_human_approval_trace(
        self,
        payload: Union[LevelARequestEnvelope, Dict[str, Any]],
        *,
        protected_module: str,
        review_event_id: str = '',
        review_completed: bool = False,
        approved_by_human: bool = False,
        approval_basis: str = 'manual_review_gate',
    ) -> Dict[str, Any]:
        review_gate = self.evaluate_manual_review_gate(
            payload,
            protected_module=protected_module,
        )
        normalized = self.classify(payload)['normalized_payload']
        blocked_by_condition = review_gate['blocked_by_condition']
        escalation_flag = review_gate['escalation_flag']

        review_status = 'REVIEW_COMPLETED' if review_completed else 'REVIEW_REQUIRED'
        approval_status = 'APPROVAL_DENIED'

        if escalation_flag and not approved_by_human:
            approval_status = 'ESCALATION_REQUIRED'
        elif review_completed and approved_by_human and not blocked_by_condition:
            approval_status = 'APPROVAL_GRANTED'

        return {
            'approval_trace_id': build_id('ahumanapproval'),
            'trace_id': normalized.get('trace_id', ''),
            'case_id': normalized.get('case_id', ''),
            'source_response_id': normalized.get('response_id') or normalized.get('source_response_id') or normalized.get('request_id', ''),
            'review_event_id': review_event_id or review_gate['review_event_id'],
            'protected_module': protected_module,
            'review_status': review_status,
            'approval_status': approval_status,
            'approval_required': True,
            'approved_by_human': approved_by_human,
            'approval_timestamp': utc_now_iso() if review_completed else '',
            'approval_basis': approval_basis,
            'blocked_by_condition': blocked_by_condition,
            'escalation_flag': escalation_flag,
            'notes': list(review_gate['notes']),
        }

    def _normalize(self, payload: Union[LevelARequestEnvelope, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return dict(payload)
        if is_dataclass(payload):
            return asdict(payload)
        raise TypeError('payload must be a dict or dataclass instance')

    def _extract_documentary_packet(self, normalized: Dict[str, Any]) -> Dict[str, Any]:
        packet = normalized.get('documentary_packet')
        if isinstance(packet, dict):
            return packet
        return normalized

    def _documentary_gaps(self, packet: Dict[str, Any]) -> List[str]:
        gaps: List[str] = []

        if not self._has_any(packet, ('source_set', 'source_ids', 'sources', 'documents_seen')):
            gaps.append('sources')
        if not self._has_any(packet, ('citation_set', 'valid_citation_ids', 'citations_valid', 'blocked_citation_ids', 'citations_blocked')):
            gaps.append('citations')
        if not self._has_any(packet, ('vigenza_findings', 'vigenza_records', 'vigenza_status_summary')):
            gaps.append('vigenza')
        if not self._has_any(packet, ('cross_reference_findings', 'cross_reference_records', 'crossref_status_summary')):
            gaps.append('cross_reference')
        if not self._has_any(packet, ('coverage_findings', 'coverage_assessment', 'coverage_status')):
            gaps.append('coverage')

        return gaps

    def _traceability_gaps(self, normalized: Dict[str, Any], packet: Dict[str, Any]) -> List[str]:
        gaps: List[str] = []

        if not normalized.get('trace_id'):
            gaps.append('trace_id')
        if not normalized.get('request_id'):
            gaps.append('request_id')
        if not (
            normalized.get('audit_complete') is True
            or normalized.get('audit_trace')
            or packet.get('audit_trace')
            or packet.get('audit_fragment')
        ):
            gaps.append('audit')
        if not (
            normalized.get('shadow_id')
            or normalized.get('shadow_trace')
            or packet.get('shadow_trace')
            or packet.get('shadow_fragment')
        ):
            gaps.append('shadow')

        return gaps

    def _has_m07_contamination(self, normalized: Dict[str, Any], packet: Dict[str, Any]) -> bool:
        if normalized.get('m07_closed') is True or packet.get('m07_closed') is True:
            return True
        m07_status = str(normalized.get('m07_status') or packet.get('m07_status') or '').upper()
        return m07_status in {'CLOSED', 'COMPLETED_AND_CLOSED'}

    def _critical_blocks(self, normalized: Dict[str, Any], packet: Dict[str, Any]) -> List[str]:
        block_codes = normalized.get('block_codes') or packet.get('block_codes') or packet.get('documentary_blocks') or []
        if not isinstance(block_codes, list):
            return []
        return sorted(code for code in block_codes if code in self.CRITICAL_BLOCK_CODES)

    def _should_degrade(self, normalized: Dict[str, Any], packet: Dict[str, Any], status: str) -> bool:
        if status in {'READY_WITH_WARNINGS', 'DEGRADED', 'SUCCESS_WITH_WARNINGS'}:
            return True
        if normalized.get('warnings') or packet.get('warnings') or packet.get('documentary_warnings'):
            return True
        if normalized.get('errors') or packet.get('errors') or packet.get('documentary_errors'):
            return True
        if str(normalized.get('coverage_status') or packet.get('coverage_status') or '').upper() in {'PARTIAL', 'DEGRADED', 'INCOMPLETE'}:
            return True
        return False

    def _source_signal_class(
        self,
        decision: str,
        critical_blocks: List[str],
        traceability_gaps: List[str],
        quarantine_codes: List[str],
        normalized: Dict[str, Any],
        packet: Dict[str, Any],
    ) -> str:
        if decision == 'REJECT' or critical_blocks:
            return 'CRITICAL_BLOCK'
        if decision == 'QUARANTINE' or traceability_gaps or quarantine_codes:
            return 'BOUNDARY_OR_TRACEABILITY'
        if decision == 'ACCEPT_WITH_DEGRADATION' or normalized.get('warnings') or normalized.get('errors') or packet.get('documentary_warnings') or packet.get('documentary_errors'):
            return 'WARNING_OR_ERROR'
        return 'DOCUMENTARY'

    def _source_runtime_effect(self, decision: str) -> str:
        if decision == 'ACCEPT_SUPPORT_ONLY':
            return 'SUPPORT_ONLY'
        if decision == 'ACCEPT_WITH_DEGRADATION':
            return 'DEGRADED_SUPPORT'
        if decision == 'QUARANTINE':
            return 'QUARANTINE'
        return 'REJECT_CONSUMPTION'

    def _find_semantic_markers(self, payload: Dict[str, Any], markers: Iterable[str]) -> List[str]:
        haystack = ' '.join(self._flatten_strings(payload)).lower()
        return [marker for marker in markers if marker.lower() in haystack]

    def _flatten_strings(self, value: Any) -> List[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, dict):
            collected: List[str] = []
            for key, nested in value.items():
                collected.append(str(key))
                collected.extend(self._flatten_strings(nested))
            return collected
        if isinstance(value, list):
            collected = []
            for nested in value:
                collected.extend(self._flatten_strings(nested))
            return collected
        return []

    def _has_any(self, payload: Dict[str, Any], fields: Iterable[str]) -> bool:
        for field in fields:
            value = payload.get(field)
            if value not in (None, '', [], {}):
                return True
        return False

    def _unique(self, items: Iterable[str]) -> List[str]:
        seen = set()
        ordered: List[str] = []
        for item in items:
            if item and item not in seen:
                seen.add(item)
                ordered.append(item)
        return ordered

    def _allowed_use_for_decision(self, decision: str) -> str:
        if decision == 'ACCEPT_SUPPORT_ONLY':
            return 'documentary_support_under_level_a_governance'
        if decision == 'ACCEPT_WITH_DEGRADATION':
            return 'degraded_documentary_support_with_manual_review'
        return 'no_direct_consumption'

    def _forbidden_use_for_decision(self, decision: str) -> str:
        if decision in {'QUARANTINE', 'REJECT'}:
            return 'direct_level_a_consumption_and_any_decisional_use'
        return 'decisional_use_m07_closure_final_compliance_output_authorization'

    def _violation_type(self, classification: Dict[str, Any], normalized: Dict[str, Any]) -> str:
        if classification['forbidden_fields']:
            return 'FORBIDDEN_FIELDS'
        if self.QUARANTINE_CODES['m07_boundary'] in classification['quarantine_codes']:
            return 'M07_CONTAMINATION'
        if self.QUARANTINE_CODES['authorization_semantics'] in classification['quarantine_codes']:
            return 'AUTHORIZATION_LIKE_SEMANTICS'
        if self.QUARANTINE_CODES['critical_blocks'] in classification['quarantine_codes'] or classification['intake_decision'] == 'REJECT':
            return 'UNRESOLVED_CRITICAL_BLOCKS'
        if normalized.get('support_only_flag') is not True:
            return 'SUPPORT_ONLY_BREACH'
        return ''

    def _requires_escalation(self, classification: Dict[str, Any], isolation_log: Dict[str, Any]) -> bool:
        if classification['intake_decision'] in {'QUARANTINE', 'REJECT'}:
            return True
        return isolation_log['violation_type'] in self.ESCALATION_REVIEW_CODES
