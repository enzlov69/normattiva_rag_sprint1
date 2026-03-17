from typing import List, Optional

from src.blocks import codes
from src.blocks.manager import BlockManager
from src.citations.citation_builder import CitationRecord


class CitationValidator:
    def __init__(self, block_manager: Optional[BlockManager] = None) -> None:
        self.block_manager = block_manager or BlockManager()

    def validate(self, *, case_id: str, citation: CitationRecord, trace_id: str = '') -> CitationRecord:
        errors: List[str] = []
        if not citation.atto_tipo:
            errors.append('atto_tipo mancante')
        if not citation.atto_numero:
            errors.append('atto_numero mancante')
        if not citation.atto_anno:
            errors.append('atto_anno mancante')
        if not citation.articolo:
            errors.append('articolo mancante')
        if not citation.uri_ufficiale:
            errors.append('uri_ufficiale mancante')
        if not citation.stato_vigenza:
            errors.append('stato_vigenza mancante')

        if errors:
            citation.citation_status = 'INVALID'
            citation.opponibile_flag = False
            citation.reconstructible_flag = False
            citation.validation_errors = errors
            block = self.block_manager.open_block(
                case_id=case_id,
                block_code=codes.CITATION_INCOMPLETE,
                block_category='citazione',
                block_severity='CRITICAL',
                origin_module='CitationValidator',
                affected_object_type='CitationRecord',
                affected_object_id=citation.citation_id,
                block_reason='; '.join(errors),
                trace_id=trace_id,
            )
            citation.block_refs.append(block.block_id)
            return citation

        citation.citation_status = 'VALID'
        citation.opponibile_flag = True
        citation.reconstructible_flag = True
        citation.validation_errors = []
        return citation
