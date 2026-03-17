from dataclasses import dataclass, field
from typing import List, Optional

from src.models.base import BaseRecord


@dataclass
class M07EvidencePack(BaseRecord):
    m07_pack_id: str = ''
    case_id: str = ''
    source_ids: List[str] = field(default_factory=list)
    norm_unit_ids: List[str] = field(default_factory=list)
    ordered_reading_sequence: List[str] = field(default_factory=list)
    annex_refs: List[str] = field(default_factory=list)
    crossref_refs: List[str] = field(default_factory=list)
    coverage_ref_id: Optional[str] = None
    missing_elements: List[str] = field(default_factory=list)
    m07_support_status: str = 'READY'
    human_completion_required: bool = True
