from dataclasses import dataclass, field
from typing import List

from src.models.base import BaseRecord


@dataclass
class CoverageAssessment(BaseRecord):
    coverage_id: str = ''
    case_id: str = ''
    query_id: str = ''
    domain_target: str = ''
    coverage_score: float = 0.0
    coverage_scope_notes: str = ''
    missing_sources: List[str] = field(default_factory=list)
    missing_annexes: List[str] = field(default_factory=list)
    missing_crossrefs: List[str] = field(default_factory=list)
    coverage_status: str = 'READY'
    critical_gap_flag: bool = False
