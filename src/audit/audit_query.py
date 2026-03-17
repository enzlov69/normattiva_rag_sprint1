import json
from pathlib import Path
from typing import Iterable, List, Optional

from src.models.audit_event import AuditEvent


class AuditQuery:
    def __init__(self, *, log_file: Optional[Path] = None) -> None:
        self.log_file = log_file

    def query(
        self,
        *,
        case_id: Optional[str] = None,
        origin_module: Optional[str] = None,
        event_phase: Optional[str] = None,
        event_type: Optional[str] = None,
        events: Optional[Iterable[AuditEvent]] = None,
    ) -> List[AuditEvent]:
        loaded = list(events) if events is not None else self._load_from_file()
        filtered: List[AuditEvent] = []
        for event in loaded:
            if case_id and event.case_id != case_id:
                continue
            if origin_module and event.origin_module != origin_module:
                continue
            if event_phase and event.event_phase != event_phase:
                continue
            if event_type and event.event_type != event_type:
                continue
            filtered.append(event)
        return filtered

    def _load_from_file(self) -> List[AuditEvent]:
        if not self.log_file or not self.log_file.exists():
            return []
        results: List[AuditEvent] = []
        with self.log_file.open('r', encoding='utf-8') as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                results.append(AuditEvent(**payload))
        return results
