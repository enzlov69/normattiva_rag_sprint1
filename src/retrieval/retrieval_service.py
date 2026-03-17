from typing import Iterable, List, Optional

from src.blocks import codes
from src.blocks.manager import BlockManager
from src.models.chunk_record import ChunkRecord
from src.retrieval.lexical_retriever import LexicalRetriever
from src.retrieval.retrieval_types import RetrievalQuery, RetrievalResult
from src.utils.ids import build_id


class RetrievalService:
    def __init__(
        self,
        *,
        block_manager: Optional[BlockManager] = None,
        lexical_retriever: Optional[LexicalRetriever] = None,
    ) -> None:
        self.block_manager = block_manager or BlockManager()
        self.lexical_retriever = lexical_retriever or LexicalRetriever()

    def query(
        self,
        *,
        case_id: str,
        query_text: str,
        chunks: Iterable[ChunkRecord],
        domain_target: str = 'enti_locali',
        top_k: int = 10,
        trace_id: str = '',
    ) -> tuple[RetrievalQuery, List[RetrievalResult]]:
        query = RetrievalQuery(
            record_id=build_id('retrqueryrec'),
            record_type='RetrievalQuery',
            query_id=build_id('retrquery'),
            case_id=case_id,
            query_text=query_text,
            domain_target=domain_target,
            top_k=top_k,
            trace_id=trace_id,
        )

        results = self.lexical_retriever.retrieve(
            case_id=case_id,
            query_id=query.query_id,
            query_text=query_text,
            chunks=chunks,
            top_k=top_k,
            trace_id=trace_id,
        )

        if not results:
            self.block_manager.open_block(
                case_id=case_id,
                block_code=codes.RETRIEVAL_EMPTY,
                block_category='retrieval',
                block_severity='CRITICAL',
                origin_module='RetrievalService',
                affected_object_type='RetrievalQuery',
                affected_object_id=query.query_id,
                block_reason='Nessun risultato documentale recuperato',
                trace_id=trace_id,
            )
            query.request_status = 'BLOCKED'
        else:
            query.request_status = 'SUCCESS'

        return query, results
