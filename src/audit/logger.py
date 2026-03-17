import json
from pathlib import Path
from typing import List, Optional

from src.config.settings import LOG_ROOT
from src.models.audit_event import AuditEvent
from src.utils.ids import build_id
from src.utils.timestamps import utc_now_iso


class AuditLogger:
    def __init__(self, log_file: Optional[Path] = None) -> None:
        LOG_ROOT.mkdir(parents=True, exist_ok=True)
        self.log_file = log_file or (LOG_ROOT / "audit_events.jsonl")
        self.events: List[AuditEvent] = []

    def log_event(
        self,
        *,
        case_id: str,
        event_type: str,
        event_phase: str,
        origin_module: str,
        actor_type: str = "SYSTEM",
        event_payload_ref: Optional[str] = None,
        event_status: str = "OK",
        trace_id: str = "",
    ) -> AuditEvent:
        event = AuditEvent(
            record_id=build_id("auditrec"),
            record_type="AuditEvent",
            audit_event_id=build_id("audit"),
            case_id=case_id,
            event_type=event_type,
            event_phase=event_phase,
            origin_module=origin_module,
            actor_type=actor_type,
            event_payload_ref=event_payload_ref,
            event_status=event_status,
            event_timestamp=utc_now_iso(),
            trace_id=trace_id,
        )
        self.events.append(event)
        with self.log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        return event