from dataclasses import dataclass, field
from typing import List, Optional

from src.models.base import BaseRecord


@dataclass
class EndToEndFlowResult(BaseRecord):
    flow_id: str = ''
    case_id: str = ''
    package_id: str = ''
    request_id: str = ''

    support_only_flag: bool = True
    workflow_status: str = 'OPEN'
    ppav_status: str = 'OPEN'
    m07_status: str = 'REVIEW_REQUIRED'
    rac_status: str = 'DRAFT'
    compliance_status: str = 'READY_FOR_REVIEW'
    go_final_status: str = 'GO_FINAL_NOT_POSSIBLE'
    authorization_status: str = 'OUTPUT_AUTHORIZATION_DENIED'

    requested_output_type: str = ''
    authorized_output_ref: Optional[str] = None
    final_runtime_status: str = 'READY_FOR_METHOD_REVIEW'

    warnings: List[str] = field(default_factory=list)
    block_codes: List[str] = field(default_factory=list)
    required_reviews: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
