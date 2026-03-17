from dataclasses import dataclass
from typing import Optional

from src.models.base import BaseRecord


@dataclass
class AuditEvent(BaseRecord):
    audit_event_id: str = ''
    case_id: str = ''
    event_type: str = ''
    event_phase: str = ''
    origin_module: str = ''
    actor_type: str = 'SYSTEM'
    event_payload_ref: Optional[str] = None
    event_status: str = 'OK'
    event_timestamp: str = ''
