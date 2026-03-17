from typing import List, Optional

from src.adapters.level_a_request_mapper import LevelARequestEnvelope
from src.compliance.compliance_types import ComplianceCheckResult
from src.level_a.level_a_types import M07GovernanceRecord, RACDraftRecord


class ComplianceRules:
    def evaluate(
        self,
        envelope: LevelARequestEnvelope,
        *,
        m07_record: Optional[M07GovernanceRecord] = None,
        rac_draft: Optional[RACDraftRecord] = None,
    ) -> List[ComplianceCheckResult]:
        return [
            self.assess_citations(envelope, rac_draft=rac_draft),
            self.assess_vigenza(envelope),
            self.assess_crossrefs(envelope),
            self.assess_coverage(envelope),
            self.assess_m07(envelope, m07_record=m07_record),
            self.assess_audit(envelope),
        ]

    def assess_citations(
        self,
        envelope: LevelARequestEnvelope,
        *,
        rac_draft: Optional[RACDraftRecord] = None,
    ) -> ComplianceCheckResult:
        blocked_ids = list(envelope.blocked_citation_ids)
        if rac_draft is not None:
            blocked_ids.extend(rac_draft.blocked_citation_ids)
        blocked_ids = [x for x in blocked_ids if x]
        has_block = 'CITATION_INCOMPLETE' in envelope.block_codes
        passed = not blocked_ids and not has_block
        reason = '' if passed else 'citazioni bloccate o incomplete'
        return ComplianceCheckResult('citations', passed, True, reason)

    def assess_vigenza(self, envelope: LevelARequestEnvelope) -> ComplianceCheckResult:
        uncertain = envelope.vigenza_status_summary.get('VIGENZA_INCERTA', 0) > 0
        has_block = 'VIGENZA_UNCERTAIN' in envelope.block_codes
        passed = not uncertain and not has_block
        reason = '' if passed else 'vigenza incerta su punti rilevanti'
        return ComplianceCheckResult('vigenza', passed, True, reason)

    def assess_crossrefs(self, envelope: LevelARequestEnvelope) -> ComplianceCheckResult:
        unresolved = envelope.crossref_status_summary.get('UNRESOLVED', 0) > 0
        has_block = 'CROSSREF_UNRESOLVED' in envelope.block_codes
        passed = not unresolved and not has_block
        reason = '' if passed else 'rinvii essenziali non risolti'
        return ComplianceCheckResult('crossrefs', passed, True, reason)

    def assess_coverage(self, envelope: LevelARequestEnvelope) -> ComplianceCheckResult:
        inadequate = envelope.coverage_status == 'INADEQUATE'
        has_block = 'COVERAGE_INADEQUATE' in envelope.block_codes
        passed = not inadequate and not has_block
        reason = '' if passed else 'copertura documentale inadeguata'
        return ComplianceCheckResult('coverage', passed, True, reason)

    def assess_m07(
        self,
        envelope: LevelARequestEnvelope,
        *,
        m07_record: Optional[M07GovernanceRecord] = None,
    ) -> ComplianceCheckResult:
        statuses = {envelope.m07_status}
        if m07_record is not None:
            statuses.add(m07_record.m07_governance_status)
        required = any(status in {'PARTIAL', 'REQUIRED'} for status in statuses if status)
        has_block = 'M07_REQUIRED' in envelope.block_codes or (
            m07_record is not None and 'M07_REQUIRED' in m07_record.block_codes
        )
        passed = not required and not has_block
        reason = '' if passed else 'M07 richiede completamento o revisione governata'
        return ComplianceCheckResult('m07', passed, True, reason)

    def assess_audit(self, envelope: LevelARequestEnvelope) -> ComplianceCheckResult:
        has_block = 'AUDIT_INCOMPLETE' in envelope.block_codes
        passed = bool(envelope.audit_complete) and not has_block
        reason = '' if passed else 'audit trail incompleto'
        return ComplianceCheckResult('audit', passed, True, reason)
