from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.models.base import BaseRecord


@dataclass
class TechnicalReport(BaseRecord):
    report_id: str = ''
    case_id: str = ''
    source_ids: List[str] = field(default_factory=list)
    valid_citation_ids: List[str] = field(default_factory=list)
    blocked_citation_ids: List[str] = field(default_factory=list)
    citation_status_summary: Dict[str, int] = field(default_factory=dict)
    vigenza_status_summary: Dict[str, int] = field(default_factory=dict)
    crossref_status_summary: Dict[str, int] = field(default_factory=dict)
    coverage_ref_id: Optional[str] = None
    coverage_status: Optional[str] = None
    m07_ref_id: Optional[str] = None
    m07_status: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    block_ids: List[str] = field(default_factory=list)
    block_codes: List[str] = field(default_factory=list)
    support_only_flag: bool = True
    report_status: str = 'READY'
