
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class LivePreparedRequest:
    method: str
    path: str
    url: str
    headers: Dict[str, str]
    body: Optional[Any] = None
    description: str = ""


@dataclass(frozen=True)
class LiveResponseEnvelope:
    status_code: int
    content_type: str
    payload: Any
    raw_text: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
