from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any, Callable, Dict, Iterable, List, Tuple


ADAPTER_MODULE_NAME = "ADAPTER_FINAL_AB_PRE_RUNTIME_V1"
FLOW_ID = "FINAL_AB_MIN_FLOW_V1"
API_VERSION = "1.0.0"

BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = BASE_DIR / "schemas"


class AdapterContractError(ValueError):
    """Raised when the adapter contract is violated."""


class AdapterScopeViolation(AdapterContractError):
    """Raised when the Level B payload exceeds its documentary scope."""


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: str = "ERROR"

    def to_error(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }


class FinalABPreRuntimeAdapter:
    """Strict pre-runtime adapter for the controlled A->B->A link.

    It validates the Level A request, receives a documentary response from a
    Level B provider, applies guardrails, propagates blocks, enforces the M07
    boundary, and returns a support-only envelope to Level A.
    """

    REQUEST_REQUIRED_FIELDS = {
        "request_id",
        "case_id",
        "trace_id",
        "flow_id",
        "api_version",
        "caller_module",
        "target_module",
        "target_endpoint",
        "level_a_phase",
        "m07_context",
        "block_policy",
        "payload",
        "timestamp",
    }

    RESPONSE_REQUIRED_FIELDS = {
        "request_id",
        "case_id",
        "trace_id",
        "api_version",
        "responder_module",
        "status",
        "documentary_packet",
        "warnings",
        "errors",
        "blocks",
        "timestamp",
    }

    DOCUMENTARY_PACKET_REQUIRED_FIELDS = {
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
    }

    ALLOWED_CALLER_MODULES = {
        "A1_OrchestratorePPAV",
        "A2_CaseClassifier",
        "A4_M07Governor",
    }

    ALLOWED_TARGET_MODULES = {
        "B10_HybridRetriever",
        "B15_CitationBuilder",
        "B13_VigenzaChecker",
        "B14_CrossReferenceResolver",
        "B16_M07SupportLayer",
        "B12_CoverageEstimator",
    }

    ALLOWED_TARGET_ENDPOINTS = {
        "/doc/retrieval/query",
        "/doc/citation/build",
        "/doc/vigenza/check",
        "/doc/crossref/resolve",
        "/doc/m07/support",
        "/doc/coverage/check",
    }

    CRITICAL_BLOCK_CODES = {
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
    }

    def __init__(self) -> None:
        self.block_registry = self._load_json("final_ab_block_propagation_registry_v1.json")
        self.m07_registry = self._load_json("final_ab_m07_boundary_registry_v1.json")

    def execute(
        self,
        request: Dict[str, Any],
        level_b_provider: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> Dict[str, Any]:
        request_issues = self.validate_request(request)
        if request_issues:
            return self._build_terminal_response(
                request=request,
                status="REJECTED",
                documentary_packet=self._empty_packet(),
                warnings=[],
                errors=[issue.to_error() for issue in request_issues],
                blocks=self._scope_block(
                    code="OUTPUT_NOT_OPPONIBLE",
                    reason="Invalid request contract prevents documentary support flow.",
                    origin_module=ADAPTER_MODULE_NAME,
                    case_id=request.get("case_id", "UNKNOWN_CASE"),
                ),
                propagated_blocks=self._scope_block(
                    code="OUTPUT_NOT_OPPONIBLE",
                    reason="Invalid request contract prevents documentary support flow.",
                    origin_module=ADAPTER_MODULE_NAME,
                    case_id=request.get("case_id", "UNKNOWN_CASE"),
                ),
                m07_boundary_state="NOT_REQUESTED",
                request_contract_valid=False,
                response_contract_valid=False,
                forbidden_fields_detected=[],
            )

        raw_response = level_b_provider(request)
        response_issues = self.validate_response(request, raw_response)
        forbidden_fields = self.detect_forbidden_fields(raw_response)
        m07_state, m07_issues = self.evaluate_m07_boundary(request, raw_response)

        all_issues = response_issues + m07_issues
        blocks = list(raw_response.get("blocks", []))
        warnings = list(raw_response.get("warnings", []))
        errors = list(raw_response.get("errors", []))

        if forbidden_fields:
            violation_block = self._scope_block(
                code="RAG_SCOPE_VIOLATION",
                reason=f"Forbidden Level B fields detected: {', '.join(sorted(forbidden_fields))}",
                origin_module=ADAPTER_MODULE_NAME,
                case_id=request["case_id"],
            )
            blocks.extend(violation_block)
            all_issues.append(
                ValidationIssue(
                    code="FORBIDDEN_LEVEL_B_FIELD",
                    message=violation_block[0]["block_reason"],
                    severity="CRITICAL",
                )
            )

        if all_issues:
            errors.extend(issue.to_error() for issue in all_issues)

        propagated_blocks = self.propagate_blocks(blocks)
        final_status = self.determine_status(
            raw_response_status=raw_response.get("status", "ERROR"),
            propagated_blocks=propagated_blocks,
            has_errors=bool(all_issues or errors),
            has_warnings=bool(warnings),
            forbidden_fields_detected=bool(forbidden_fields),
            m07_boundary_state=m07_state,
        )

        documentary_packet = raw_response.get("documentary_packet", self._empty_packet())
        return self._build_terminal_response(
            request=request,
            status=final_status,
            documentary_packet=documentary_packet,
            warnings=warnings,
            errors=errors,
            blocks=blocks,
            propagated_blocks=propagated_blocks,
            m07_boundary_state=m07_state,
            request_contract_valid=True,
            response_contract_valid=not response_issues,
            forbidden_fields_detected=sorted(forbidden_fields),
        )

    def validate_request(self, request: Dict[str, Any]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        missing = self.REQUEST_REQUIRED_FIELDS.difference(request.keys())
        for field in sorted(missing):
            issues.append(ValidationIssue(code=f"MISSING_{field.upper()}", message=f"Missing request field: {field}"))

        if request.get("flow_id") != FLOW_ID:
            issues.append(ValidationIssue(code="INVALID_FLOW_ID", message="flow_id must match the controlled A->B->A pre-runtime flow."))

        caller_module = request.get("caller_module")
        if caller_module and caller_module not in self.ALLOWED_CALLER_MODULES:
            issues.append(ValidationIssue(code="UNAUTHORIZED_CALLER_MODULE", message=f"Unauthorized caller_module: {caller_module}"))

        target_module = request.get("target_module")
        if target_module and target_module not in self.ALLOWED_TARGET_MODULES:
            issues.append(ValidationIssue(code="UNAUTHORIZED_TARGET_MODULE", message=f"Unauthorized target_module: {target_module}"))

        target_endpoint = request.get("target_endpoint")
        if target_endpoint and target_endpoint not in self.ALLOWED_TARGET_ENDPOINTS:
            issues.append(ValidationIssue(code="UNAUTHORIZED_TARGET_ENDPOINT", message=f"Unauthorized target_endpoint: {target_endpoint}"))

        payload = request.get("payload", {})
        if not isinstance(payload, dict):
            issues.append(ValidationIssue(code="INVALID_PAYLOAD", message="payload must be an object."))
        else:
            for required in ("query_text", "domain_target"):
                if required not in payload:
                    issues.append(ValidationIssue(code=f"MISSING_PAYLOAD_{required.upper()}", message=f"Missing payload field: {required}"))

        m07_context = request.get("m07_context", {})
        if not isinstance(m07_context, dict):
            issues.append(ValidationIssue(code="INVALID_M07_CONTEXT", message="m07_context must be an object."))
        else:
            for required in ("required", "support_requested", "human_completion_required"):
                if required not in m07_context:
                    issues.append(ValidationIssue(code=f"MISSING_M07_CONTEXT_{required.upper()}", message=f"Missing m07_context field: {required}"))

        block_policy = request.get("block_policy", {})
        if not isinstance(block_policy, dict):
            issues.append(ValidationIssue(code="INVALID_BLOCK_POLICY", message="block_policy must be an object."))
        else:
            expected_true_flags = {
                "propagate_critical",
                "reject_forbidden_fields",
                "reject_m07_closure_attempts",
            }
            for field in expected_true_flags:
                if block_policy.get(field) is not True:
                    issues.append(ValidationIssue(code=f"INVALID_BLOCK_POLICY_{field.upper()}", message=f"block_policy.{field} must be true."))

        return issues

    def validate_response(self, request: Dict[str, Any], response: Dict[str, Any]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        if not isinstance(response, dict):
            return [ValidationIssue(code="INVALID_RESPONSE_TYPE", message="Level B response must be an object.")]

        missing = self.RESPONSE_REQUIRED_FIELDS.difference(response.keys())
        for field in sorted(missing):
            issues.append(ValidationIssue(code=f"MISSING_RESPONSE_{field.upper()}", message=f"Missing response field: {field}"))

        for key in ("request_id", "case_id", "trace_id"):
            if key in response and key in request and response[key] != request[key]:
                issues.append(ValidationIssue(code=f"MISMATCH_{key.upper()}", message=f"Response {key} does not match the originating request."))

        packet = response.get("documentary_packet")
        if packet is None:
            issues.append(ValidationIssue(code="MISSING_DOCUMENTARY_PACKET", message="documentary_packet is required in the Level B response."))
        elif not isinstance(packet, dict):
            issues.append(ValidationIssue(code="INVALID_DOCUMENTARY_PACKET", message="documentary_packet must be an object."))
        else:
            missing_packet_fields = self.DOCUMENTARY_PACKET_REQUIRED_FIELDS.difference(packet.keys())
            for field in sorted(missing_packet_fields):
                issues.append(ValidationIssue(code=f"MISSING_PACKET_{field.upper()}", message=f"Missing documentary_packet field: {field}"))

        if "blocks" in response and not isinstance(response.get("blocks"), list):
            issues.append(ValidationIssue(code="INVALID_BLOCKS", message="blocks must be a list."))
        if "warnings" in response and not isinstance(response.get("warnings"), list):
            issues.append(ValidationIssue(code="INVALID_WARNINGS", message="warnings must be a list."))
        if "errors" in response and not isinstance(response.get("errors"), list):
            issues.append(ValidationIssue(code="INVALID_ERRORS", message="errors must be a list."))

        return issues

    def detect_forbidden_fields(self, response: Dict[str, Any]) -> List[str]:
        forbidden_fields = set(self.m07_registry.get("forbidden_fields", []))
        forbidden_fields.update(
            {
                "final_decision",
                "decision_status",
                "applicability_final",
                "output_authorized",
                "compliance_go",
                "m07_closed",
                "rac_approved",
                "signature_ready",
                "go_final",
                "no_go_final",
                "approved",
                "authorization",
            }
        )
        return sorted(field for field in self._collect_keys(response) if field in forbidden_fields)

    def evaluate_m07_boundary(self, request: Dict[str, Any], response: Dict[str, Any]) -> Tuple[str, List[ValidationIssue]]:
        m07_context = request.get("m07_context", {})
        packet = response.get("documentary_packet", {}) if isinstance(response, dict) else {}
        packet_shadow = packet.get("shadow_fragment", {}) if isinstance(packet, dict) else {}
        issues: List[ValidationIssue] = []

        if not m07_context.get("required") and request.get("target_endpoint") != "/doc/m07/support":
            return "NOT_REQUESTED", issues

        forbidden_fields = set(self.m07_registry.get("forbidden_fields", []))
        found_forbidden = [field for field in self._collect_keys(response) if field in forbidden_fields]
        if found_forbidden:
            issues.append(
                ValidationIssue(
                    code="M07_BOUNDARY_VIOLATION",
                    message=f"Forbidden M07 boundary field(s) detected: {', '.join(sorted(found_forbidden))}",
                    severity="CRITICAL",
                )
            )
            return "BOUNDARY_VIOLATION", issues

        if request.get("target_endpoint") == "/doc/m07/support":
            if m07_context.get("human_completion_required") is not True:
                issues.append(
                    ValidationIssue(
                        code="M07_CONTEXT_INVALID",
                        message="M07 support requests must keep human_completion_required = true at Level A request level.",
                        severity="CRITICAL",
                    )
                )
                return "BOUNDARY_VIOLATION", issues

            packet_human_completion = packet_shadow.get("human_completion_required")
            if packet_human_completion is False:
                issues.append(
                    ValidationIssue(
                        code="M07_SUPPORT_ILLEGALLY_COMPLETED",
                        message="Documentary packet suggests M07 human completion is not required.",
                        severity="CRITICAL",
                    )
                )
                return "BOUNDARY_VIOLATION", issues

        return "PREPARATORY_ONLY", issues

    def propagate_blocks(self, blocks: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        propagated: List[Dict[str, Any]] = []
        registry = {item["block_code"]: item for item in self.block_registry.get("blocks", [])}
        for block in blocks:
            if not isinstance(block, dict):
                continue
            code = block.get("block_code")
            if code in registry:
                merged = dict(block)
                merged["propagation_mode"] = registry[code]["propagation_mode"]
                merged["level_a_required_handling"] = registry[code]["level_a_required_handling"]
                merged["release_control"] = registry[code]["release_control"]
                propagated.append(merged)
        return propagated

    def determine_status(
        self,
        raw_response_status: str,
        propagated_blocks: List[Dict[str, Any]],
        has_errors: bool,
        has_warnings: bool,
        forbidden_fields_detected: bool,
        m07_boundary_state: str,
    ) -> str:
        if forbidden_fields_detected or m07_boundary_state == "BOUNDARY_VIOLATION":
            return "REJECTED"
        if any(block.get("block_code") in self.CRITICAL_BLOCK_CODES for block in propagated_blocks):
            return "BLOCKED"
        if has_errors:
            return "DEGRADED"
        if has_warnings or raw_response_status == "SUCCESS_WITH_WARNINGS":
            return "SUCCESS_WITH_WARNINGS"
        if raw_response_status == "DEGRADED":
            return "DEGRADED"
        return "SUCCESS"

    def _build_terminal_response(
        self,
        request: Dict[str, Any],
        status: str,
        documentary_packet: Dict[str, Any],
        warnings: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
        blocks: List[Dict[str, Any]],
        propagated_blocks: List[Dict[str, Any]],
        m07_boundary_state: str,
        request_contract_valid: bool,
        response_contract_valid: bool,
        forbidden_fields_detected: List[str],
    ) -> Dict[str, Any]:
        timestamp = self._utc_now()
        return {
            "request_id": request.get("request_id", "UNKNOWN_REQUEST"),
            "case_id": request.get("case_id", "UNKNOWN_CASE"),
            "trace_id": request.get("trace_id", "UNKNOWN_TRACE"),
            "flow_id": request.get("flow_id", FLOW_ID),
            "api_version": API_VERSION,
            "responder_module": ADAPTER_MODULE_NAME,
            "status": status,
            "documentary_packet": documentary_packet,
            "warnings": warnings,
            "errors": errors,
            "blocks": blocks,
            "propagated_blocks": propagated_blocks,
            "m07_boundary_state": m07_boundary_state,
            "support_only_flag": True,
            "opponibile_output_flag": False,
            "level_a_action_required": True,
            "shadow_fragment": {
                "adapter_version": API_VERSION,
                "flow_id": request.get("flow_id", FLOW_ID),
                "request_contract_valid": request_contract_valid,
                "response_contract_valid": response_contract_valid,
                "forbidden_fields_detected": forbidden_fields_detected,
                "propagated_block_codes": [block.get("block_code") for block in propagated_blocks],
                "m07_boundary_state": m07_boundary_state,
                "support_only_flag": True,
                "timestamp": timestamp,
            },
            "timestamp": timestamp,
        }

    def _scope_block(self, code: str, reason: str, origin_module: str, case_id: str) -> List[Dict[str, Any]]:
        return [
            {
                "block_id": f"blk_{code.lower()}",
                "case_id": case_id,
                "block_code": code,
                "block_category": "CONTRACT" if code == "OUTPUT_NOT_OPPONIBLE" else "SCOPE",
                "block_severity": "CRITICAL",
                "origin_module": origin_module,
                "affected_object_type": "ADAPTER_ENVELOPE",
                "affected_object_id": case_id,
                "block_reason": reason,
                "block_status": "OPEN",
            }
        ]

    def _empty_packet(self) -> Dict[str, Any]:
        return {
            "sources": [],
            "norm_units": [],
            "citations_valid": [],
            "citations_blocked": [],
            "vigenza_records": [],
            "cross_reference_records": [],
            "coverage_assessment": {},
            "warnings": [],
            "errors": [],
            "blocks": [],
            "shadow_fragment": {},
        }

    def _collect_keys(self, data: Any) -> List[str]:
        keys: List[str] = []
        if isinstance(data, dict):
            for key, value in data.items():
                keys.append(key)
                keys.extend(self._collect_keys(value))
        elif isinstance(data, list):
            for item in data:
                keys.extend(self._collect_keys(item))
        return keys

    def _load_json(self, filename: str) -> Dict[str, Any]:
        path = SCHEMAS_DIR / filename
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_demo_level_b_response(request: Dict[str, Any]) -> Dict[str, Any]:
    """Simple offline provider useful for local checks and tests."""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "request_id": request["request_id"],
        "case_id": request["case_id"],
        "trace_id": request["trace_id"],
        "api_version": request.get("api_version", API_VERSION),
        "responder_module": request["target_module"],
        "status": "SUCCESS",
        "documentary_packet": {
            "sources": [
                {
                    "source_id": "source_demo_001",
                    "atto_tipo": "D.Lgs.",
                    "atto_numero": "267",
                    "atto_anno": "2000",
                    "uri_ufficiale": "https://www.normattiva.it/"
                }
            ],
            "norm_units": [
                {
                    "norm_unit_id": "nu_demo_001",
                    "articolo": "42",
                    "comma": "1"
                }
            ],
            "citations_valid": [
                {
                    "citation_id": "cit_demo_001",
                    "citation_status": "VALID"
                }
            ],
            "citations_blocked": [],
            "vigenza_records": [
                {
                    "vigenza_id": "vig_demo_001",
                    "vigore_status": "VIGENTE_VERIFICATA"
                }
            ],
            "cross_reference_records": [],
            "coverage_assessment": {
                "coverage_id": "cov_demo_001",
                "coverage_status": "SUFFICIENT",
                "critical_gap_flag": False
            },
            "warnings": [],
            "errors": [],
            "blocks": [],
            "shadow_fragment": {
                "human_completion_required": True,
                "ordered_reading_sequence": ["nu_demo_001"]
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": now,
    }
