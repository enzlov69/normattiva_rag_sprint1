from dataclasses import dataclass, field
from typing import List

from src.models.base import BaseRecord


@dataclass
class ShadowTrace(BaseRecord):
    shadow_id: str = ''
    case_id: str = ''
    executed_modules: List[str] = field(default_factory=list)
    retrieval_queries: List[str] = field(default_factory=list)
    filters_applied: List[str] = field(default_factory=list)
    documents_seen: List[str] = field(default_factory=list)
    norm_units_seen: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
    decision_points: List[str] = field(default_factory=list)
    technical_notes: List[str] = field(default_factory=list)
