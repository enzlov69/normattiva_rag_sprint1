from dataclasses import dataclass
from typing import Optional

from src.models.base import BaseRecord


@dataclass
class CrossReferenceRecord(BaseRecord):
    crossref_id: str = ''
    source_id: str = ''
    norm_unit_id: str = ''
    crossref_type: str = 'interno'
    crossref_text: str = ''
    target_source_id: Optional[str] = None
    target_norm_unit_id: Optional[str] = None
    target_uri: Optional[str] = None
    resolution_status: str = 'UNRESOLVED'
    essential_ref_flag: bool = False
    resolved_flag: bool = False
    block_if_unresolved_flag: bool = False
