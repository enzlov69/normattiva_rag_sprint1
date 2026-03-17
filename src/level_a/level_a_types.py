from dataclasses import dataclass, field
from typing import List, Optional

from src.models.base import BaseRecord


@dataclass
class LevelAWorkflowState(BaseRecord):
    workflow_id: str = ''
    case_id: str = ''
    request_id: str = ''
    source_package_id: str = ''
    support_only_flag: bool = True
    workflow_status: str = 'OPEN'
    next_modules: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    block_codes: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class PPAVOrchestrationRecord(BaseRecord):
    orchestration_id: str = ''
    case_id: str = ''
    request_id: str = ''
    source_package_id: str = ''
    support_only_flag: bool = True
    ppav_status: str = 'OPEN'
    requested_modules: List[str] = field(default_factory=list)
    required_human_governance: bool = True
    warnings: List[str] = field(default_factory=list)
    block_codes: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class M07GovernanceRecord(BaseRecord):
    m07_governance_id: str = ''
    case_id: str = ''
    request_id: str = ''
    source_package_id: str = ''
    source_m07_ref_id: Optional[str] = None
    support_only_flag: bool = True
    m07_governance_status: str = 'REVIEW_REQUIRED'
    m07_review_required: bool = True
    missing_elements: List[str] = field(default_factory=list)
    block_codes: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class RACDraftRecord(BaseRecord):
    rac_draft_id: str = ''
    case_id: str = ''
    request_id: str = ''
    source_package_id: str = ''
    support_only_flag: bool = True
    rac_draft_status: str = 'DRAFT'
    documentary_support_refs: List[str] = field(default_factory=list)
    blocked_citation_ids: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    block_codes: List[str] = field(default_factory=list)
    human_completion_required: bool = True
    notes: List[str] = field(default_factory=list)
