from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


STATUS_SUCCESS = "SUCCESS"
STATUS_SUCCESS_WITH_WARNINGS = "SUCCESS_WITH_WARNINGS"
STATUS_DEGRADED = "DEGRADED"
STATUS_BLOCKED = "BLOCKED"
STATUS_REJECTED = "REJECTED"
STATUS_ERROR = "ERROR"

STATUS_ORDER = {
    STATUS_SUCCESS: 0,
    STATUS_SUCCESS_WITH_WARNINGS: 1,
    STATUS_DEGRADED: 2,
    STATUS_BLOCKED: 3,
    STATUS_REJECTED: 4,
    STATUS_ERROR: 5,
}

DEFAULT_REQUIRED_ENVELOPE_FIELDS: Tuple[str, ...] = (
    "request_id",
    "case_id",
    "trace_id",
    "api_version",
    "responder_module",
    "status",
    "payload",
    "warnings",
    "errors",
    "blocks",
    "timestamp",
)

DEFAULT_REQUIRED_DOCUMENTARY_PACKET_FIELDS: Tuple[str, ...] = (
    "sources",
    "norm_units",
    "citations_valid",
    "citations_blocked",
    "vigenza_records",
    "cross_reference_records",
    "coverage_assessment",
    "warnings",
    "errors",
    "blocks",
    "shadow_fragment",
)

DEFAULT_FINAL_BLOCK_CODES: Tuple[str, ...] = (
    "CORPUS_MISSING",
    "SOURCE_UNVERIFIED",
    "CITATION_INCOMPLETE",
    "VIGENZA_UNCERTAIN",
    "CROSSREF_UNRESOLVED",
    "M07_REQUIRED",
    "RAG_SCOPE_VIOLATION",
    "AUDIT_INCOMPLETE",
    "OUTPUT_NOT_OPPONIBLE",
    "COVERAGE_INADEQUATE",
)

DEFAULT_FORBIDDEN_FIELDS: Tuple[str, ...] = (
    "decision",
    "decision_status",
    "final_decision",
    "approved",
    "authorization",
    "output_authorized",
    "signature_ready",
    "compliance_go",
    "compliance_passed",
    "go_final",
    "go_finale",
    "no_go_final",
    "final_applicability",
    "applicability_final",
    "legal_conclusion",
    "motivazione_finale",
    "m07_closed",
    "m07_completed",
    "rac_approved",
    "rac_finalized",
    "ppav_closed",
)

CRITICAL_AUDIT_REQUIRED_STATUSES = {
    STATUS_DEGRADED,
    STATUS_BLOCKED,
    STATUS_REJECTED,
    STATUS_ERROR,
}


@dataclass(frozen=True)
class ResponseEnvelopeGateConfig:
    responder_module: str = "B22_ResponseEnvelopeGate"
    required_envelope_fields: Tuple[str, ...] = DEFAULT_REQUIRED_ENVELOPE_FIELDS
    required_documentary_packet_fields: Tuple[str, ...] = DEFAULT_REQUIRED_DOCUMENTARY_PACKET_FIELDS
    final_block_codes: Tuple[str, ...] = DEFAULT_FINAL_BLOCK_CODES
    forbidden_fields: Tuple[str, ...] = DEFAULT_FORBIDDEN_FIELDS


class FinalABResponseEnvelopeGate:
    """
    Technical post-mapper guard for the final ABResponseEnvelope.

    Responsibilities:
    - validate the final envelope contract;
    - prevent silent loss or downgrade of critical upstream blocks;
    - reject forbidden Level B fields in the final payload;
    - verify final documentary packet completeness;
    - require audit/shadow completeness on critical paths;
    - reconcile raw validation result with the mapped final response.
    """

    def __init__(self, config: Optional[ResponseEnvelopeGateConfig] = None) -> None:
        self.config = config or ResponseEnvelopeGateConfig()
        self._forbidden_field_set = {self._normalize_name(value) for value in self.config.forbidden_fields}
        self._final_block_set = {self._normalize_name(value) for value in self.config.final_block_codes}

    def validate(
        self,
        envelope: Mapping[str, Any],
        *,
        raw_validation_result: Optional[Mapping[str, Any]] = None,
        raw_response: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        candidate = self._deepcopy_mapping(envelope)
        raw_validation = self._deepcopy_mapping(raw_validation_result or {})
        raw = self._deepcopy_mapping(raw_response or {})

        self._ensure_core_collections(candidate)

        guard_errors: List[Dict[str, Any]] = []
        guard_warnings: List[Dict[str, Any]] = []
        guard_blocks: List[Dict[str, Any]] = []

        missing_envelope_fields = self._find_missing_fields(candidate, self.config.required_envelope_fields)
        if missing_envelope_fields:
            guard_errors.append(
                self._error(
                    code="FINAL_ENVELOPE_INCOMPLETE",
                    message=f"ABResponseEnvelope missing required fields: {', '.join(missing_envelope_fields)}",
                )
            )
            guard_blocks.append(
                self._block(
                    code="OUTPUT_NOT_OPPONIBLE",
                    reason="Final ABResponseEnvelope is incomplete after response mapping.",
                    category="CONTRACT",
                )
            )

        mapped_warnings = self._as_list(candidate.get("warnings", []))
        mapped_errors = self._as_list(candidate.get("errors", []))
        mapped_blocks = self._as_list(candidate.get("blocks", []))

        merged_warnings = self._merge_issue_lists(
            mapped_warnings, raw_validation.get("warnings", []), raw.get("warnings", [])
        )
        merged_errors = self._merge_issue_lists(
            mapped_errors, raw_validation.get("errors", []), raw.get("errors", [])
        )
        merged_blocks = self._merge_block_lists(
            mapped_blocks, raw_validation.get("blocks", []), raw.get("blocks", [])
        )

        candidate["warnings"] = merged_warnings
        candidate["errors"] = merged_errors
        candidate["blocks"] = merged_blocks

        forbidden_hits = self._scan_forbidden_fields(candidate.get("payload", {}))
        if forbidden_hits:
            guard_errors.append(
                self._error(
                    code="FORBIDDEN_LEVEL_B_FIELDS_PRESENT",
                    message="Forbidden Level B fields reappeared in final payload: " + ", ".join(sorted(forbidden_hits)),
                )
            )
            guard_blocks.append(
                self._block(
                    code="RAG_SCOPE_VIOLATION",
                    reason="Final payload contains forbidden conclusory or validation fields.",
                    category="SCOPE",
                )
            )

        documentary_packet = self._extract_documentary_packet(candidate)
        documentary_packet_missing = self._find_missing_documentary_packet_fields(documentary_packet)
        if documentary_packet_missing:
            guard_errors.append(
                self._error(
                    code="DOCUMENTARY_PACKET_INCOMPLETE",
                    message="Final DocumentaryPacket missing required fields: " + ", ".join(documentary_packet_missing),
                )
            )
            guard_blocks.append(
                self._block(
                    code="OUTPUT_NOT_OPPONIBLE",
                    reason="Final DocumentaryPacket is incomplete or not fully traceable.",
                    category="DOCUMENTARY_PACKET",
                )
            )

        upstream_critical_blocks = self._critical_blocks_from(raw_validation) + self._critical_blocks_from(raw)
        missing_critical_codes = self._find_missing_critical_block_codes(upstream_critical_blocks, mapped_blocks)
        if missing_critical_codes:
            guard_errors.append(
                self._error(
                    code="CRITICAL_BLOCK_LOSS_DETECTED",
                    message="Critical upstream blocks were lost or attenuated in final envelope: " + ", ".join(missing_critical_codes),
                )
            )
            for block_code in missing_critical_codes:
                guard_blocks.append(
                    self._block(
                        code=block_code,
                        reason="Critical upstream block was not preserved by final mapping and has been reinstated by the response-envelope gate.",
                        category="PROPAGATION",
                    )
                )

        raw_status = self._normalize_status(self._read_status(raw_validation) or self._read_status(raw))
        final_status_before_guard = self._normalize_status(candidate.get("status"))
        if self._is_improper_status_downgrade(raw_status, final_status_before_guard):
            guard_errors.append(
                self._error(
                    code="STATUS_DOWNGRADE_DETECTED",
                    message=f"Final status {final_status_before_guard} improperly downgrades upstream status {raw_status}.",
                )
            )
            guard_blocks.append(
                self._block(
                    code="OUTPUT_NOT_OPPONIBLE",
                    reason="Improper downgrade of upstream raw validation outcome detected.",
                    category="STATUS",
                )
            )

        if self._raw_validation_rejected_or_invalid(raw_validation) and final_status_before_guard in {
            STATUS_SUCCESS,
            STATUS_SUCCESS_WITH_WARNINGS,
            STATUS_DEGRADED,
        }:
            guard_errors.append(
                self._error(
                    code="RAW_VALIDATION_MISMATCH",
                    message="Raw validation result is blocking or invalid but final mapped response is less restrictive.",
                )
            )
            guard_blocks.append(
                self._block(
                    code="OUTPUT_NOT_OPPONIBLE",
                    reason="Final response is inconsistent with pre-mapper raw validation result.",
                    category="RAW_VALIDATION",
                )
            )

        all_blocks = self._merge_block_lists(candidate.get("blocks", []), guard_blocks)
        all_errors = self._merge_issue_lists(candidate.get("errors", []), guard_errors)
        all_warnings = self._merge_issue_lists(candidate.get("warnings", []), guard_warnings)

        audit_fragment = self._extract_audit_fragment(candidate, documentary_packet)
        shadow_fragment = self._extract_shadow_fragment(candidate, documentary_packet)
        critical_case = self._requires_audit_shadow(candidate.get("status"), all_errors, all_blocks)
        if critical_case:
            audit_missing = self._audit_fragment_missing(audit_fragment)
            shadow_missing = self._shadow_fragment_missing(shadow_fragment)
            if audit_missing:
                all_errors = self._merge_issue_lists(
                    all_errors,
                    [
                        self._error(
                            code="AUDIT_FRAGMENT_MISSING",
                            message="Critical final response lacks audit fragment completeness.",
                        )
                    ],
                )
                all_blocks = self._merge_block_lists(
                    all_blocks,
                    [
                        self._block(
                            code="AUDIT_INCOMPLETE",
                            reason="Critical response lacks required audit fragment completeness.",
                            category="AUDIT",
                        )
                    ],
                )
            if shadow_missing:
                all_errors = self._merge_issue_lists(
                    all_errors,
                    [
                        self._error(
                            code="SHADOW_FRAGMENT_MISSING",
                            message="Critical final response lacks shadow trace completeness.",
                        )
                    ],
                )
                all_blocks = self._merge_block_lists(
                    all_blocks,
                    [
                        self._block(
                            code="AUDIT_INCOMPLETE",
                            reason="Critical response lacks required shadow trace completeness.",
                            category="SHADOW",
                        )
                    ],
                )

        final_status = self._reconcile_status(candidate.get("status"), all_warnings, all_errors, all_blocks)

        candidate["warnings"] = all_warnings
        candidate["errors"] = all_errors
        candidate["blocks"] = all_blocks
        candidate["status"] = final_status
        candidate.setdefault("payload", {})
        if isinstance(candidate["payload"], MutableMapping):
            gate_report = {
                "gate_name": self.config.responder_module,
                "guard_applied": True,
                "raw_validation_status": raw_status,
                "final_status_before_guard": final_status_before_guard,
                "final_status_after_guard": final_status,
                "forbidden_field_hits": forbidden_hits,
                "missing_envelope_fields": missing_envelope_fields,
                "missing_documentary_packet_fields": documentary_packet_missing,
                "reinstated_critical_block_codes": missing_critical_codes,
                "audit_fragment_present": not self._audit_fragment_missing(audit_fragment),
                "shadow_fragment_present": not self._shadow_fragment_missing(shadow_fragment),
            }
            candidate["payload"]["response_envelope_gate_report"] = gate_report
            candidate["payload"]["raw_validation_status"] = raw_status
            candidate["payload"]["final_status_before_guard"] = final_status_before_guard

        return candidate

    def __call__(
        self,
        envelope: Mapping[str, Any],
        *,
        raw_validation_result: Optional[Mapping[str, Any]] = None,
        raw_response: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.validate(
            envelope,
            raw_validation_result=raw_validation_result,
            raw_response=raw_response,
        )

    def _find_missing_fields(self, data: Mapping[str, Any], required_fields: Iterable[str]) -> List[str]:
        missing: List[str] = []
        for field in required_fields:
            if field not in data:
                missing.append(field)
                continue
            value = data.get(field)
            if value is None:
                missing.append(field)
                continue
            if field in {"warnings", "errors", "blocks"} and not isinstance(value, list):
                missing.append(field)
        return missing

    def _find_missing_documentary_packet_fields(self, packet: Optional[Mapping[str, Any]]) -> List[str]:
        if not isinstance(packet, Mapping):
            return list(self.config.required_documentary_packet_fields)
        return self._find_missing_fields(packet, self.config.required_documentary_packet_fields)

    def _extract_documentary_packet(self, envelope: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
        payload = envelope.get("payload")
        if not isinstance(payload, Mapping):
            return None
        packet = payload.get("documentary_packet")
        if isinstance(packet, Mapping):
            return packet
        if all(field in payload for field in self.config.required_documentary_packet_fields):
            return payload
        return None

    def _extract_audit_fragment(
        self,
        envelope: Mapping[str, Any],
        packet: Optional[Mapping[str, Any]],
    ) -> Any:
        candidates = [
            envelope.get("audit"),
            envelope.get("audit_fragment"),
            self._get_nested(envelope, "payload", "audit"),
            self._get_nested(envelope, "payload", "audit_fragment"),
            packet.get("audit_fragment") if isinstance(packet, Mapping) else None,
        ]
        for item in candidates:
            if item not in (None, {}, [], ""):
                return item
        return None

    def _extract_shadow_fragment(
        self,
        envelope: Mapping[str, Any],
        packet: Optional[Mapping[str, Any]],
    ) -> Any:
        candidates = [
            envelope.get("shadow"),
            envelope.get("shadow_fragment"),
            self._get_nested(envelope, "payload", "shadow"),
            self._get_nested(envelope, "payload", "shadow_fragment"),
            packet.get("shadow_fragment") if isinstance(packet, Mapping) else None,
        ]
        for item in candidates:
            if item not in (None, {}, [], ""):
                return item
        return None

    def _requires_audit_shadow(
        self,
        status: Any,
        errors: Sequence[Mapping[str, Any]],
        blocks: Sequence[Mapping[str, Any]],
    ) -> bool:
        normalized_status = self._normalize_status(status)
        if normalized_status in CRITICAL_AUDIT_REQUIRED_STATUSES:
            return True
        if errors:
            return True
        for block in blocks:
            if self._is_critical_block(block):
                return True
        return False

    def _audit_fragment_missing(self, value: Any) -> bool:
        if value in (None, "", [], {}):
            return True
        if isinstance(value, Mapping):
            keys = {self._normalize_name(key) for key in value.keys()}
            return not ({"trace_id", "event_type"} <= keys or {"trace_id", "event_phase"} <= keys)
        return False

    def _shadow_fragment_missing(self, value: Any) -> bool:
        if value in (None, "", [], {}):
            return True
        if isinstance(value, Mapping):
            keys = {self._normalize_name(key) for key in value.keys()}
            return not ({"trace_id", "executed_modules"} <= keys or {"shadow_id", "executed_modules"} <= keys)
        return False

    def _is_improper_status_downgrade(self, raw_status: str, final_status: str) -> bool:
        if not raw_status or not final_status:
            return False
        return STATUS_ORDER.get(final_status, -1) < STATUS_ORDER.get(raw_status, -1)

    def _raw_validation_rejected_or_invalid(self, raw_validation: Mapping[str, Any]) -> bool:
        if not raw_validation:
            return False
        status = self._normalize_status(self._read_status(raw_validation))
        if status in {STATUS_BLOCKED, STATUS_REJECTED, STATUS_ERROR}:
            return True
        invalid_markers = [raw_validation.get("is_valid"), raw_validation.get("valid"), raw_validation.get("passed")]
        for marker in invalid_markers:
            if marker is False:
                return True
        return False

    def _read_status(self, data: Mapping[str, Any]) -> str:
        for key in ("status", "validation_status", "result_status"):
            value = data.get(key)
            if value:
                return str(value)
        return ""

    def _critical_blocks_from(self, data: Mapping[str, Any]) -> List[Dict[str, Any]]:
        return [block for block in self._as_list(data.get("blocks", [])) if self._is_critical_block(block)]

    def _find_missing_critical_block_codes(
        self,
        upstream_blocks: Sequence[Mapping[str, Any]],
        final_blocks: Sequence[Mapping[str, Any]],
    ) -> List[str]:
        final_codes = {self._extract_code(block) for block in final_blocks}
        missing: List[str] = []
        for block in upstream_blocks:
            code = self._extract_code(block)
            if code and code not in final_codes:
                missing.append(code)
        return sorted(set(missing))

    def _scan_forbidden_fields(self, payload: Any) -> List[str]:
        hits: set[str] = set()

        def visit(node: Any) -> None:
            if isinstance(node, Mapping):
                for key, value in node.items():
                    normalized_key = self._normalize_name(key)
                    if normalized_key in self._forbidden_field_set:
                        hits.add(str(key))
                    visit(value)
            elif isinstance(node, list):
                for item in node:
                    visit(item)

        visit(payload)
        return sorted(hits)

    def _reconcile_status(
        self,
        original_status: Any,
        warnings: Sequence[Mapping[str, Any]],
        errors: Sequence[Mapping[str, Any]],
        blocks: Sequence[Mapping[str, Any]],
    ) -> str:
        normalized = self._normalize_status(original_status)
        critical_blocks = [block for block in blocks if self._is_critical_block(block)]
        if critical_blocks:
            if any(self._extract_code(block) == "RAG_SCOPE_VIOLATION" for block in critical_blocks):
                return STATUS_REJECTED
            return STATUS_BLOCKED
        if errors:
            return STATUS_DEGRADED if normalized not in {STATUS_REJECTED, STATUS_ERROR} else normalized
        if warnings:
            return STATUS_SUCCESS_WITH_WARNINGS
        if normalized in STATUS_ORDER:
            return normalized
        return STATUS_SUCCESS

    def _is_critical_block(self, block: Mapping[str, Any]) -> bool:
        code = self._extract_code(block)
        severity = self._normalize_name(block.get("severity") or block.get("block_severity") or "")
        if code in self._final_block_set:
            return True
        return severity in {"critical", "alta", "high", "blocking"}

    def _extract_code(self, item: Mapping[str, Any]) -> str:
        for key in ("code", "block_code", "error_code", "warning_code"):
            value = item.get(key)
            if value:
                return str(value)
        return ""

    def _merge_block_lists(self, *collections: Iterable[Any]) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = []
        seen: set[Tuple[str, str, str]] = set()
        for collection in collections:
            for item in self._as_list(collection):
                normalized = self._normalize_block(item)
                identity = (
                    self._normalize_name(normalized.get("code") or normalized.get("block_code") or ""),
                    self._normalize_name(normalized.get("reason") or ""),
                    self._normalize_name(normalized.get("origin_module") or ""),
                )
                if identity in seen:
                    continue
                seen.add(identity)
                merged.append(normalized)
        return merged

    def _merge_issue_lists(self, *collections: Iterable[Any]) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = []
        seen: set[Tuple[str, str]] = set()
        for collection in collections:
            for item in self._as_list(collection):
                normalized = self._normalize_issue(item)
                identity = (
                    self._normalize_name(normalized.get("code") or ""),
                    self._normalize_name(normalized.get("message") or ""),
                )
                if identity in seen:
                    continue
                seen.add(identity)
                merged.append(normalized)
        return merged

    def _normalize_block(self, item: Any) -> Dict[str, Any]:
        if isinstance(item, Mapping):
            normalized = dict(item)
            code = normalized.get("code") or normalized.get("block_code") or "UNKNOWN_BLOCK"
            normalized.setdefault("code", code)
            normalized.setdefault("block_code", code)
            normalized.setdefault("severity", normalized.get("block_severity", "CRITICAL"))
            normalized.setdefault("category", normalized.get("block_category", "RUNTIME"))
            normalized.setdefault("origin_module", normalized.get("origin_module", self.config.responder_module))
            normalized.setdefault("reason", normalized.get("message", normalized.get("reason", "")))
            return normalized
        if isinstance(item, str):
            return self._block(code=item, reason=item)
        return self._block(code="UNKNOWN_BLOCK", reason=str(item))

    def _normalize_issue(self, item: Any) -> Dict[str, Any]:
        if isinstance(item, Mapping):
            normalized = dict(item)
            code = normalized.get("code") or normalized.get("error_code") or normalized.get("warning_code") or "UNKNOWN_ISSUE"
            normalized.setdefault("code", code)
            normalized.setdefault("message", normalized.get("reason", normalized.get("message", "")))
            return normalized
        if isinstance(item, str):
            return {"code": "TEXT_ISSUE", "message": item}
        return {"code": "UNKNOWN_ISSUE", "message": str(item)}

    def _block(self, code: str, reason: str, category: str = "RUNTIME", severity: str = "CRITICAL") -> Dict[str, Any]:
        return {
            "code": code,
            "block_code": code,
            "severity": severity,
            "category": category,
            "origin_module": self.config.responder_module,
            "reason": reason,
        }

    def _error(self, code: str, message: str) -> Dict[str, Any]:
        return {
            "code": code,
            "message": message,
            "origin_module": self.config.responder_module,
        }

    def _ensure_core_collections(self, envelope: MutableMapping[str, Any]) -> None:
        envelope.setdefault("warnings", [])
        envelope.setdefault("errors", [])
        envelope.setdefault("blocks", [])
        envelope.setdefault("payload", {})

    def _normalize_status(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value).strip().upper()
        if text == "WARNING":
            return STATUS_SUCCESS_WITH_WARNINGS
        if text == "WARN":
            return STATUS_SUCCESS_WITH_WARNINGS
        return text

    def _get_nested(self, data: Mapping[str, Any], *path: str) -> Any:
        current: Any = data
        for key in path:
            if not isinstance(current, Mapping):
                return None
            current = current.get(key)
        return current

    def _as_list(self, value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        return [value]

    def _normalize_name(self, value: Any) -> str:
        return str(value).strip().lower().replace("-", "_").replace(" ", "_")

    def _deepcopy_mapping(self, value: Any) -> Dict[str, Any]:
        if not isinstance(value, Mapping):
            return {}
        return deepcopy(dict(value))
