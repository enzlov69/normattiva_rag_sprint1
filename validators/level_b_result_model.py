from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ResponseStatus(str, Enum):
    SUCCESS = "SUCCESS"
    SUCCESS_WITH_WARNINGS = "SUCCESS_WITH_WARNINGS"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"


class BlockSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


OPEN_BLOCK_STATUSES = {"OPEN", "CONFIRMED"}


@dataclass
class ValidationFinding:
    code: str
    level: str
    message: str
    pointer: str = ""


@dataclass
class WarningMessage:
    code: str
    message: str
    pointer: str = ""
    module: str = ""


@dataclass
class ErrorMessage:
    code: str
    message: str
    pointer: str = ""
    module: str = ""


@dataclass
class BlockRef:
    block_code: str
    block_category: str
    block_severity: str
    origin_module: str
    affected_object_type: str
    affected_object_id: str
    block_reason: str
    block_status: str
    release_condition: Optional[str] = None

    @property
    def is_open(self) -> bool:
        return self.block_status in OPEN_BLOCK_STATUSES

    @property
    def is_critical_open(self) -> bool:
        return self.is_open and self.block_severity == BlockSeverity.CRITICAL.value


@dataclass
class AuditSummary:
    events_present: bool
    critical_nodes_logged: bool
    audit_event_count: int = 0
    missing_nodes: List[str] = field(default_factory=list)


@dataclass
class ShadowSummary:
    executed_modules: List[str]
    retrieval_queries: List[str]
    documents_seen: List[str]
    blocks: List[str]
    filters_applied: List[str] = field(default_factory=list)
    norm_units_seen: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    decision_points: List[str] = field(default_factory=list)
    technical_notes: List[str] = field(default_factory=list)


@dataclass
class M07SupportSummary:
    human_completion_required: bool
    ordered_reading_sequence: List[str]
    missing_elements: List[str]
    annex_refs: List[str] = field(default_factory=list)
    crossref_refs: List[str] = field(default_factory=list)
    m07_support_status: str = ""


@dataclass
class LevelBPayloadResult:
    request_id: str
    case_id: str
    trace_id: str
    api_version: str
    responder_module: str
    status: ResponseStatus
    payload: Dict[str, Any]
    warnings: List[WarningMessage]
    errors: List[ErrorMessage]
    blocks: List[BlockRef]
    timestamp: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LevelBPayloadResult":
        warnings = [
            WarningMessage(
                code=item.get("code", ""),
                message=item.get("message", ""),
                pointer=item.get("pointer", ""),
                module=item.get("module", ""),
            )
            for item in data.get("warnings", [])
        ]
        errors = [
            ErrorMessage(
                code=item.get("code", ""),
                message=item.get("message", ""),
                pointer=item.get("pointer", ""),
                module=item.get("module", ""),
            )
            for item in data.get("errors", [])
        ]
        blocks = [
            BlockRef(
                block_code=item.get("block_code", ""),
                block_category=item.get("block_category", ""),
                block_severity=item.get("block_severity", ""),
                origin_module=item.get("origin_module", ""),
                affected_object_type=item.get("affected_object_type", ""),
                affected_object_id=item.get("affected_object_id", ""),
                block_reason=item.get("block_reason", ""),
                block_status=item.get("block_status", ""),
                release_condition=item.get("release_condition"),
            )
            for item in data.get("blocks", [])
        ]
        return cls(
            request_id=data.get("request_id", ""),
            case_id=data.get("case_id", ""),
            trace_id=data.get("trace_id", ""),
            api_version=data.get("api_version", ""),
            responder_module=data.get("responder_module", ""),
            status=ResponseStatus(data.get("status", "ERROR")),
            payload=data.get("payload", {}),
            warnings=warnings,
            errors=errors,
            blocks=blocks,
            timestamp=data.get("timestamp", ""),
        )


@dataclass
class ValidationReport:
    ok: bool
    findings: List[ValidationFinding] = field(default_factory=list)

    def add(self, code: str, level: str, message: str, pointer: str = "") -> None:
        self.findings.append(
            ValidationFinding(code=code, level=level, message=message, pointer=pointer)
        )

    @property
    def error_count(self) -> int:
        return sum(1 for finding in self.findings if finding.level in {"ERROR", "CRITICAL"})
