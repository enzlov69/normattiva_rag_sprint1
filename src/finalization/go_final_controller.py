from typing import Optional

from src.adapters.level_a_request_mapper import LevelARequestEnvelope
from src.compliance.compliance_types import FinalComplianceSnapshot
from src.finalization.finalization_types import FinalGoAssessment
from src.level_a.level_a_types import M07GovernanceRecord, PPAVOrchestrationRecord, RACDraftRecord
from src.utils.ids import build_id


class GoFinalController:
    def assess(
        self,
        envelope: LevelARequestEnvelope,
        compliance_snapshot: FinalComplianceSnapshot,
        *,
        ppav_record: Optional[PPAVOrchestrationRecord] = None,
        m07_record: Optional[M07GovernanceRecord] = None,
        rac_draft: Optional[RACDraftRecord] = None,
        trace_id: str = '',
    ) -> FinalGoAssessment:
        blocking_reasons = []
        required_reviews = []
        warnings = list(envelope.warnings)

        if compliance_snapshot.technical_readiness_status == 'BLOCKED':
            blocking_reasons.append('compliance_blocked')
        elif compliance_snapshot.technical_readiness_status == 'SUPPORT_ONLY':
            required_reviews.append('support_only_review')

        if envelope.block_codes:
            blocking_reasons.append('open_blocks_present')
        if envelope.errors:
            blocking_reasons.append('technical_errors_present')
        if not envelope.audit_complete:
            blocking_reasons.append('audit_incomplete')
        if m07_record is not None and m07_record.m07_governance_status in {'REQUIRED', 'REVIEW_REQUIRED'}:
            blocking_reasons.append('m07_not_governed')
        if rac_draft is None:
            blocking_reasons.append('rac_draft_missing')
        elif rac_draft.human_completion_required:
            required_reviews.append('rac_human_completion_required')
            if rac_draft.blocked_citation_ids:
                blocking_reasons.append('rac_blocked_citations_present')
        if ppav_record is not None and ppav_record.required_human_governance:
            required_reviews.append('ppav_human_governance_required')

        go_possible = not blocking_reasons and compliance_snapshot.technical_readiness_status == 'READY_FOR_REVIEW'
        status = 'GO_FINAL_POSSIBLE' if go_possible else 'GO_FINAL_NOT_POSSIBLE'

        notes = [
            'Valutazione tecnica finale del Livello A.',
            'Il GO finale resta sotto controllo esplicito del Metodo Cerda.',
            'Nessuna decisione è delegata al RAG o al solo stato documentale.',
        ]
        if required_reviews:
            notes.append('Persistono verifiche umane e metodologiche necessarie prima di qualunque esito opponibile.')

        return FinalGoAssessment(
            record_id=build_id('gofinalrec'),
            record_type='FinalGoAssessment',
            assessment_id=build_id('gofinal'),
            case_id=envelope.case_id,
            request_id=envelope.request_id,
            source_package_id=envelope.source_package_id,
            source_compliance_id=compliance_snapshot.compliance_id,
            support_only_flag=True,
            go_final_possible=go_possible,
            go_final_status=status,
            blocking_reasons=blocking_reasons,
            required_reviews=required_reviews,
            warnings=warnings,
            notes=notes,
            source_layer='A',
            trace_id=trace_id or envelope.trace_id,
        )
