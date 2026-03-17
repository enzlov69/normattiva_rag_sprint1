from dataclasses import dataclass
from typing import Optional

from src.models.base import BaseRecord


@dataclass
class BlockEvent(BaseRecord):
    block_id: str = ''
    case_id: str = ''
    block_code: str = ''
    block_category: str = ''
    block_severity: str = 'HIGH'
    origin_module: str = ''
    affected_object_type: str = ''
    affected_object_id: str = ''
    block_reason: str = ''
    release_condition: Optional[str] = None
    block_status: str = 'OPEN'
    opened_at: str = ''
    released_at: Optional[str] = None
