from src.blocks import codes
from src.blocks.manager import BlockManager
from src.models.chunk_record import ChunkRecord
from src.retrieval.retrieval_service import RetrievalService


def _chunk(chunk_id: str, text: str, seq: int) -> ChunkRecord:
    return ChunkRecord(
        record_id=f'rec_{chunk_id}',
        record_type='ChunkRecord',
        chunk_id=chunk_id,
        source_id='source_001',
        norm_unit_id=f'norm_{chunk_id}',
        chunk_text=text,
        chunk_sequence=seq,
    )


def test_retrieval_service_opens_block_when_no_results() -> None:
    block_manager = BlockManager()
    service = RetrievalService(block_manager=block_manager)

    query, results = service.query(
        case_id='case_401',
        query_text='appalto concessione',
        chunks=[_chunk('c1', 'Il sindaco rappresenta il comune', 1)],
    )

    assert query.request_status == 'BLOCKED'
    assert results == []
    assert any(block.block_code == codes.RETRIEVAL_EMPTY for block in block_manager.list_open_blocks(case_id='case_401'))


def test_retrieval_service_returns_results_without_blocks() -> None:
    block_manager = BlockManager()
    service = RetrievalService(block_manager=block_manager)

    query, results = service.query(
        case_id='case_402',
        query_text='sindaco comune',
        chunks=[_chunk('c1', 'Il sindaco rappresenta il comune', 1)],
    )

    assert query.request_status == 'SUCCESS'
    assert len(results) == 1
    assert block_manager.list_open_blocks(case_id='case_402') == []
