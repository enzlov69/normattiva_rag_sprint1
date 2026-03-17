from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.models.base import BaseRecord


@dataclass
class LevelBDeliveryPackage(BaseRecord):
    package_id: str = ''
    case_id: str = ''
    report_id: str = ''
    report_status: str = 'READY'
    support_only_flag: bool = True

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

    audit_complete: bool = False
    audit_checked_events: int = 0
    audit_missing_phases: List[str] = field(default_factory=list)
    audit_missing_modules: List[str] = field(default_factory=list)

    shadow_id: Optional[str] = None
    executed_modules: List[str] = field(default_factory=list)
    documents_seen: List[str] = field(default_factory=list)
    norm_units_seen: List[str] = field(default_factory=list)
    shadow_block_codes: List[str] = field(default_factory=list)

    package_status: str = 'READY'


@dataclass
class LevelBPackageValidationResult:
    valid: bool
    missing_fields: List[str] = field(default_factory=list)
    forbidden_fields: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    normalized_payload: Dict[str, Any] = field(default_factory=dict)
