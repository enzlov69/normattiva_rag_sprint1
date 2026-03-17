import re
from typing import Iterable, List

from src.models.chunk_record import ChunkRecord
from src.retrieval.retrieval_types import RetrievalResult
from src.utils.ids import build_id


TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


class LexicalRetriever:
    def __init__(self) -> None:
        pass

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [token.lower() for token in TOKEN_PATTERN.findall(text or '')]

    def retrieve(
        self,
        *,
        case_id: str,
        query_id: str,
        query_text: str,
        chunks: Iterable[ChunkRecord],
        top_k: int = 10,
        trace_id: str = '',
    ) -> List[RetrievalResult]:
        query_tokens = set(self._tokenize(query_text))
        if not query_tokens:
            return []

        scored: List[tuple[float, ChunkRecord]] = []
        for chunk in chunks:
            if not chunk.retrievable_flag or chunk.orphan_flag:
                continue
            chunk_tokens = self._tokenize(chunk.chunk_text)
            if not chunk_tokens:
                continue
            overlap = query_tokens.intersection(chunk_tokens)
            if not overlap:
                continue
            score = len(overlap) / max(len(query_tokens), 1)
            scored.append((score, chunk))

        scored.sort(key=lambda item: (-item[0], item[1].chunk_sequence))

        results: List[RetrievalResult] = []
        for idx, (score, chunk) in enumerate(scored[:top_k], start=1):
            results.append(
                RetrievalResult(
                    record_id=build_id('retrresrec'),
                    record_type='RetrievalResult',
                    retrieval_result_id=build_id('retrres'),
                    query_id=query_id,
                    case_id=case_id,
                    source_id=chunk.source_id,
                    norm_unit_id=chunk.norm_unit_id,
                    chunk_id=chunk.chunk_id,
                    rank_position=idx,
                    score_lexical=round(score, 6),
                    score_reranked=round(score, 6),
                    retrieval_reason='Token overlap lessicale',
                    trace_id=trace_id,
                )
            )
        return results
