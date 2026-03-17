from dataclasses import dataclass, field, asdict
from typing import Any, Dict

from src.config.settings import SCHEMA_VERSION
from src.utils.timestamps import utc_now_iso


@dataclass
class BaseRecord:
    record_id: str
    record_type: str
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    schema_version: str = SCHEMA_VERSION
    record_version: int = 1
    source_layer: str = 'B'
    trace_id: str = ''
    active_flag: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
