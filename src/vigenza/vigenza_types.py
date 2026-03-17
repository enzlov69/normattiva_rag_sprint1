from dataclasses import dataclass
from typing import Optional

from src.models.base import BaseRecord


@dataclass
class VigenzaRecord(BaseRecord):
    vigenza_id: str = ''
    source_id: str = ''
    norm_unit_id: str = ''
    vigore_status: str = 'VIGENZA_INCERTA'
    vigore_start_date: Optional[str] = None
    vigore_end_date: Optional[str] = None
    vigore_basis: str = ''
    verification_method: str = 'documentale'
    verification_confidence: float = 0.0
    essential_point_flag: bool = False
    block_if_uncertain_flag: bool = False
