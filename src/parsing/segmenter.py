from typing import List

from src.blocks import codes
from src.blocks.manager import BlockManager
from src.config.settings import DEFAULT_CHUNK_MAX_CHARS
from src.models.chunk_record import ChunkRecord
from src.models.norm_unit import NormUnit
from src.utils.ids import build_id


class Segmenter:
    def __init__(self, block_manager: BlockManager, max_chars: int = DEFAULT_CHUNK_MAX_CHARS) -> None:
        self.block_manager = block_manager
        self.max_chars = max_chars

    def segment(self, *, case_id: str, norm_units: List[NormUnit], trace_id: str = '') -> List[ChunkRecord]:
        chunks: List[ChunkRecord] = []
        for seq, unit in enumerate(norm_units, start=1):
            if not unit.source_id or not unit.norm_unit_id:
                orphan = ChunkRecord(
                    record_id=build_id('chunkrec'),
                    record_type='ChunkRecord',
                    chunk_id=build_id('chunk'),
                    source_id=unit.source_id,
                    norm_unit_id=unit.norm_unit_id,
                    chunk_text=unit.testo_unita,
                    chunk_sequence=seq,
                    orphan_flag=True,
                    retrievable_flag=False,
                    chunk_status='BLOCKED',
                    trace_id=trace_id,
                )
                chunks.append(orphan)
                self.block_manager.open_block(
                    case_id=case_id,
                    block_code=codes.CHUNK_ORPHAN,
                    block_category='chunk',
                    block_severity='CRITICAL',
                    origin_module='Segmenter',
                    affected_object_type='ChunkRecord',
                    affected_object_id=orphan.chunk_id,
                    block_reason='Chunk senza ancoraggio a fonte o unità normativa',
                    trace_id=trace_id,
                )
                continue

            text = unit.testo_unita.strip()
            if len(text) <= self.max_chars:
                chunks.append(self._build_chunk(unit=unit, text=text, sequence=seq, trace_id=trace_id))
                continue

            part_idx = 0
            start = 0
            while start < len(text):
                part_idx += 1
                piece = text[start:start + self.max_chars].strip()
                chunks.append(self._build_chunk(unit=unit, text=piece, sequence=seq * 100 + part_idx, trace_id=trace_id))
                start += self.max_chars
        return chunks

    def _build_chunk(self, *, unit: NormUnit, text: str, sequence: int, trace_id: str) -> ChunkRecord:
        return ChunkRecord(
            record_id=build_id('chunkrec'),
            record_type='ChunkRecord',
            chunk_id=build_id('chunk'),
            source_id=unit.source_id,
            norm_unit_id=unit.norm_unit_id,
            chunk_text=text,
            chunk_sequence=sequence,
            orphan_flag=False,
            retrievable_flag=True,
            chunk_status='READY',
            trace_id=trace_id,
        )
