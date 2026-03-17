from dataclasses import dataclass, field
from typing import List, Optional

from src.models.base import BaseRecord


@dataclass
class NormUnit(BaseRecord):
    norm_unit_id: str = ''
    source_id: str = ''
    unit_type: str = 'ARTICOLO'
    articolo: str = ''
    comma: Optional[str] = None
    lettera: Optional[str] = None
    numero: Optional[str] = None
    allegato: Optional[str] = None
    rubrica: str = ''
    testo_unita: str = ''
    position_index: int = 0
    hierarchy_path: str = ''
    cross_reference_ids: List[str] = field(default_factory=list)
    vigenza_ref_id: Optional[str] = None
    norm_unit_status: str = 'PARSED'
