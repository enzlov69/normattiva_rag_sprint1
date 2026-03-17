from typing import Iterable, List, Tuple

from src.blocks import codes
from src.blocks.manager import BlockManager
from src.models.chunk_record import ChunkRecord
from src.models.norm_unit import NormUnit
from src.models.source_document import SourceDocument


class MetadataEnricher:
    def __init__(self, block_manager: BlockManager) -> None:
        self.block_manager = block_manager

    def enrich(
        self,
        *,
        case_id: str,
        source_document: SourceDocument,
        norm_units: List[NormUnit],
        chunks: List[ChunkRecord],
        trace_id: str = '',
    ) -> Tuple[SourceDocument, List[NormUnit], List[ChunkRecord]]:
        required = [source_document.atto_tipo, source_document.atto_numero, source_document.atto_anno, source_document.uri_ufficiale]
        if not all(required):
            self.block_manager.open_block(
                case_id=case_id,
                block_code=codes.METADATA_INSUFFICIENT,
                block_category='metadata',
                block_severity='CRITICAL',
                origin_module='MetadataEnricher',
                affected_object_type='SourceDocument',
                affected_object_id=source_document.source_id,
                block_reason='Metadati minimi non completi dopo enrichment',
                trace_id=trace_id,
            )
        source_document.index_ready_flag = True
        return source_document, norm_units, chunks
