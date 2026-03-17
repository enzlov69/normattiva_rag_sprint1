from dataclasses import dataclass, field
from typing import List, Optional

from src.models.base import BaseRecord


@dataclass
class FinalGoAssessment(BaseRecord):
    assessment_id: str = ''
    case_id: str = ''
    request_id: str = ''
    source_package_id: str = ''
    source_compliance_id: str = ''
    support_only_flag: bool = True
    go_final_possible: bool = False
    go_final_status: str = 'GO_FINAL_NOT_POSSIBLE'
    blocking_reasons: List[str] = field(default_factory=list)
    required_reviews: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class OutputAuthorizationDecision(BaseRecord):
    decision_id: str = ''
    case_id: str = ''
    request_id: str = ''
    source_assessment_id: str = ''
    requested_output_type: str = ''
    support_only_flag: bool = True
    authorization_allowed: bool = False
    authorization_status: str = 'OUTPUT_AUTHORIZATION_DENIED'
    denied_reasons: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    authorized_output_ref: Optional[str] = None
