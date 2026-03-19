from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Union

from src.adapters.level_a_request_mapper import LevelARequestEnvelope


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

        return {
            'intake_decision': decision,
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
