from src.finalization.finalization_types import FinalGoAssessment, OutputAuthorizationDecision
from src.utils.ids import build_id


class OutputAuthorizer:
    ALLOWED_OUTPUT_TYPES = {'RAC_DRAFT', 'TECHNICAL_MEMO', 'INTERNAL_REVIEW_PACKET'}

    def authorize(
        self,
        assessment: FinalGoAssessment,
        *,
        requested_output_type: str,
        trace_id: str = '',
    ) -> OutputAuthorizationDecision:
        denied_reasons = []
        if not assessment.go_final_possible:
            denied_reasons.append('go_final_not_possible')
        if requested_output_type not in self.ALLOWED_OUTPUT_TYPES:
            denied_reasons.append('output_type_not_allowed')

        allowed = not denied_reasons
        status = 'OUTPUT_AUTHORIZATION_ALLOWED' if allowed else 'OUTPUT_AUTHORIZATION_DENIED'
        notes = [
            'Autorizzazione tecnica emessa nel Livello A.',
            'L’autorizzazione non retroagisce sul Livello B e non delega alcuna decisione al RAG.',
        ]
        if not allowed:
            notes.append('Output non autorizzato: permangono presìdi da completare o vincoli di tipo output.')

        return OutputAuthorizationDecision(
            record_id=build_id('outauthrec'),
            record_type='OutputAuthorizationDecision',
            decision_id=build_id('outauth'),
            case_id=assessment.case_id,
            request_id=assessment.request_id,
            source_assessment_id=assessment.assessment_id,
            requested_output_type=requested_output_type,
            support_only_flag=True,
            authorization_allowed=allowed,
            authorization_status=status,
            denied_reasons=denied_reasons,
            notes=notes,
            authorized_output_ref=build_id('output') if allowed else None,
            source_layer='A',
            trace_id=trace_id or assessment.trace_id,
        )
