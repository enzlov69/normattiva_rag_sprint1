from dataclasses import dataclass
from typing import Optional

from src.models.base import BaseRecord


@dataclass
class ChunkRecord(BaseRecord):
    chunk_id: str = ''
    source_id: str = ''
    norm_unit_id: str = ''
    chunk_text: str = ''
    chunk_sequence: int = 0
    chunk_context_before: str = ''
    chunk_context_after: str = ''
    embedding_vector_ref: Optional[str] = None
    lexical_index_ref: Optional[str] = None
    quality_flag: str = 'OK'
    parse_confidence: float = 1.0
    retrievable_flag: bool = True
    orphan_flag: bool = False
    chunk_status: str = 'READY'
