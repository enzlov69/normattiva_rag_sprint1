from src.models.chunk_record import ChunkRecord
from src.retrieval.lexical_retriever import LexicalRetriever


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


def test_lexical_retriever_returns_ranked_results() -> None:
    retriever = LexicalRetriever()
    chunks = [
        _chunk('c1', 'I dirigenti curano la gestione amministrativa', 1),
        _chunk('c2', 'Il sindaco rappresenta l\'ente', 2),
    ]

    results = retriever.retrieve(
        case_id='case_400',
        query_id='qry_001',
        query_text='gestione dirigenti',
        chunks=chunks,
        top_k=5,
    )

    assert len(results) == 1
    assert results[0].chunk_id == 'c1'
    assert results[0].rank_position == 1
    assert results[0].score_lexical > 0
