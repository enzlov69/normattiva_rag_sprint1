from src.adapters.level_a_request_mapper import LevelARequestEnvelope
from src.level_a.level_a_types import RACDraftRecord
from src.utils.ids import build_id


class RACBuilder:
    def build_draft(self, envelope: LevelARequestEnvelope, *, trace_id: str = '') -> RACDraftRecord:
        documentary_support_refs = []
        documentary_support_refs.extend(envelope.source_ids)
        documentary_support_refs.extend(envelope.valid_citation_ids)

        status = 'DRAFT_WITH_BLOCKS' if envelope.block_codes or envelope.blocked_citation_ids else 'DRAFT'
        notes = [
            'Bozza RAC tecnica, non conclusiva e non opponibile.',
            'Il Livello A conserva la motivazione finale e la validazione dell’atto.',
        ]
        if envelope.blocked_citation_ids:
            notes.append('Sono presenti citazioni bloccate da governare prima di un uso opponibile.')
        if envelope.coverage_status == 'INADEQUATE':
            notes.append('La copertura documentale risulta inadeguata e richiede integrazione.')

        return RACDraftRecord(
            record_id=build_id('racdraftrec'),
            record_type='RACDraftRecord',
            rac_draft_id=build_id('racdraft'),
            case_id=envelope.case_id,
            request_id=envelope.request_id,
            source_package_id=envelope.source_package_id,
            support_only_flag=True,
            rac_draft_status=status,
            documentary_support_refs=documentary_support_refs,
            blocked_citation_ids=list(envelope.blocked_citation_ids),
            warnings=list(envelope.warnings),
            block_codes=list(envelope.block_codes),
            human_completion_required=True,
            notes=notes,
            source_layer='A',
            trace_id=trace_id or envelope.trace_id,
        )
