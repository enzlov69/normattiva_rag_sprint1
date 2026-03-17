from dataclasses import dataclass, field
from typing import List, Optional

from src.models.base import BaseRecord


@dataclass
class RetrievalResult(BaseRecord):
    retrieval_result_id: str = ''
    query_id: str = ''
    case_id: str = ''
    source_id: str = ''
    norm_unit_id: str = ''
    chunk_id: str = ''
    rank_position: int = 0
    score_lexical: float = 0.0
    score_vector: float = 0.0
    score_reranked: float = 0.0
    domain_coherence_score: float = 1.0
    source_authority_score: float = 1.0
    retrieval_reason: str = ''
    retrieval_status: str = 'READY'
    warning_flags: List[str] = field(default_factory=list)
    block_refs: List[str] = field(default_factory=list)


@dataclass
class RetrievalQuery(BaseRecord):
    query_id: str = ''
    case_id: str = ''
    query_text: str = ''
    domain_target: str = ''
    retrieval_mode: str = 'lexical'
    top_k: int = 10
    request_status: str = 'READY'
    metadata_filters: dict = field(default_factory=dict)
