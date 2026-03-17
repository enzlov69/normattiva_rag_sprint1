from typing import List, Optional

from src.models.block_event import BlockEvent
from src.utils.ids import build_id
from src.utils.timestamps import utc_now_iso


class BlockManager:
    def __init__(self) -> None:
        self._blocks: List[BlockEvent] = []

    def open_block(
        self,
        *,
        case_id: str,
        block_code: str,
        block_category: str,
        block_severity: str,
        origin_module: str,
        affected_object_type: str,
        affected_object_id: str,
        block_reason: str,
        trace_id: str = '',
        release_condition: Optional[str] = None,
    ) -> BlockEvent:
        event = BlockEvent(
            record_id=build_id('blockrec'),
            record_type='BlockEvent',
            block_id=build_id('block'),
            case_id=case_id,
            block_code=block_code,
            block_category=block_category,
            block_severity=block_severity,
            origin_module=origin_module,
            affected_object_type=affected_object_type,
            affected_object_id=affected_object_id,
            block_reason=block_reason,
            release_condition=release_condition,
            opened_at=utc_now_iso(),
            trace_id=trace_id,
        )
        self._blocks.append(event)
        return event

    def list_open_blocks(self, *, case_id: Optional[str] = None) -> List[BlockEvent]:
        blocks = [b for b in self._blocks if b.block_status == 'OPEN']
        if case_id:
            blocks = [b for b in blocks if b.case_id == case_id]
        return blocks

    def has_critical_blocks(self, *, case_id: Optional[str] = None) -> bool:
        return any(b.block_severity.upper() == 'CRITICAL' for b in self.list_open_blocks(case_id=case_id))
