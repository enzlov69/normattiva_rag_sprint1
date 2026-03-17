from dataclasses import dataclass, field
from typing import List

from src.models.base import BaseRecord


@dataclass
class ComplianceCheckResult:
    rule_name: str
    passed: bool
    critical: bool = True
    reason: str = ''


@dataclass
class FinalComplianceSnapshot(BaseRecord):
    compliance_id: str = ''
    case_id: str = ''
    request_id: str = ''
    source_package_id: str = ''
    support_only_flag: bool = True
    technical_readiness_status: str = 'READY_FOR_REVIEW'
    citation_ok: bool = False
    vigenza_ok: bool = False
    crossref_ok: bool = False
    coverage_ok: bool = False
    m07_ok: bool = False
    audit_ok: bool = False
    open_block_codes: List[str] = field(default_factory=list)
    missing_requirements: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
