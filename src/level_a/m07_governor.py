from src.adapters.level_a_request_mapper import LevelARequestEnvelope
from src.level_a.level_a_types import M07GovernanceRecord
from src.utils.ids import build_id


class M07Governor:
    def govern(self, envelope: LevelARequestEnvelope, *, trace_id: str = '') -> M07GovernanceRecord:
        missing_elements = []
        block_codes = list(envelope.block_codes)

        if envelope.m07_status in {None, '', 'PARTIAL', 'REQUIRED'}:
            missing_elements.append('m07_review')
        if envelope.blocked_citation_ids:
            missing_elements.append('blocked_citations')
        if not envelope.audit_complete:
            missing_elements.append('audit_review')

        status = 'READY_FOR_REVIEW'
        if 'M07_REQUIRED' in block_codes or envelope.m07_status in {'PARTIAL', 'REQUIRED'}:
            status = 'REQUIRED'
        elif missing_elements:
            status = 'REVIEW_REQUIRED'

        notes = [
            'Il supporto documentale del Livello B non equivale a chiusura di M07.',
            'La lettura integrale resta governata dal Metodo Cerda.',
        ]
        if envelope.m07_ref_id:
            notes.append('È presente un riferimento tecnico al pacchetto M07 del Livello B.')

        return M07GovernanceRecord(
            record_id=build_id('m07govrec'),
            record_type='M07GovernanceRecord',
            m07_governance_id=build_id('m07gov'),
            case_id=envelope.case_id,
            request_id=envelope.request_id,
            source_package_id=envelope.source_package_id,
            source_m07_ref_id=envelope.m07_ref_id,
            support_only_flag=True,
            m07_governance_status=status,
            m07_review_required=True,
            missing_elements=missing_elements,
            block_codes=block_codes,
            notes=notes,
            source_layer='A',
            trace_id=trace_id or envelope.trace_id,
        )
