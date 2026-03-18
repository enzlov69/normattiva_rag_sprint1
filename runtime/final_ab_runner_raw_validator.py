from __future__ import annotations

import copy
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

from runtime.final_ab_runner_raw_validation_registry import (
    load_raw_block_rules_registry,
    load_raw_forbidden_fields_registry,
    load_raw_minimum_schema,
    registry_versions,
)


STATUS_ORDER = {
    "SUCCESS": 0,
    "SUCCESS_WITH_WARNINGS": 1,
    "DEGRADED": 2,
    "BLOCKED": 3,
    "REJECTED": 4,
    "ERROR": 5,
}


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _is_empty_signal(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 0


def _deep_iter(node: Any, path: str = "$") -> Iterable[Tuple[str, Any]]:
    yield path, node
    if isinstance(node, dict):
        for key, value in node.items():
            child_path = f"{path}.{key}"
            yield from _deep_iter(value, child_path)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            child_path = f"{path}[{index}]"
            yield from _deep_iter(value, child_path)


@dataclass
class ValidationFinding:
    anomaly_code: str
    path: str
    message: str
    status: str
    severity: str
    block_code: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RawValidationResult:
    status: str
    validated_raw_payload: Optional[Dict[str, Any]]
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    blocks: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    registry_versions: Dict[str, str] = field(default_factory=dict)
    trace: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "validated_raw_payload": self.validated_raw_payload,
            "warnings": self.warnings,
            "errors": self.errors,
            "blocks": self.blocks,
            "findings": self.findings,
            "registry_versions": self.registry_versions,
            "trace": self.trace,
        }


class FinalABRunnerRawValidator:
    """
    Raw pre-mapper validator for the federated runner output.

    The validator is intentionally mechanical:
    - type and minimum-structure checks
    - forbidden field / forbidden value detection
    - M07 boundary protection
    - documentary minimum consistency checks

    It does not infer missing content and does not interpret legal meaning.
    """

    def __init__(
        self,
        minimum_schema: Optional[Dict[str, Any]] = None,
        forbidden_registry: Optional[Dict[str, Any]] = None,
        block_rules_registry: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.minimum_schema = minimum_schema or load_raw_minimum_schema()
        self.forbidden_registry = forbidden_registry or load_raw_forbidden_fields_registry()
        self.block_rules_registry = block_rules_registry or load_raw_block_rules_registry()
        self._rule_map = self.block_rules_registry["rules"]
        self._compiled_key_patterns = [
            re.compile(pattern) for pattern in self.forbidden_registry.get("key_regex_patterns", [])
        ]
        self._compiled_value_patterns = [
            re.compile(pattern) for pattern in self.forbidden_registry.get("value_regex_patterns", [])
        ]
        self._allowed_near_misses = {
            _normalize_name(item) for item in self.forbidden_registry.get("allowed_near_misses", [])
        }
        self._exact_forbidden_normalized = {
            _normalize_name(item) for item in self.forbidden_registry.get("exact_fields", [])
        }
        for aliases in self.forbidden_registry.get("aliases", {}).values():
            self._exact_forbidden_normalized.update(_normalize_name(item) for item in aliases)

    def validate(
        self,
        raw_output: Any,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> RawValidationResult:
        findings: List[ValidationFinding] = []

        if not isinstance(raw_output, dict):
            findings.append(self._finding("RAW_NOT_OBJECT", "$", "Raw runner output must be a dictionary."))
            return self._build_result(None, findings, request_context)

        payload = copy.deepcopy(raw_output)
        self._validate_minimum_structure(payload, findings)
        self._detect_forbidden_fields_and_values(payload, findings)
        self._validate_citations(payload, findings)
        self._validate_vigenza(payload, findings)
        self._validate_crossrefs(payload, findings)
        self._validate_coverage(payload, findings)
        self._validate_signal_channels(payload, findings)

        return self._build_result(payload, findings, request_context)

    def _validate_minimum_structure(self, payload: Dict[str, Any], findings: List[ValidationFinding]) -> None:
        required_fields = self.minimum_schema.get("required_top_level_fields", [])
        typed_fields = self.minimum_schema.get("typed_fields", {})
        documentary_nuclei = self.minimum_schema.get("documentary_nuclei", {})

        for field_name in required_fields:
            if field_name not in payload:
                findings.append(
                    self._finding(
                        "RAW_REQUIRED_FIELD_MISSING",
                        f"$.{field_name}",
                        f"Required raw control field '{field_name}' is missing.",
                    )
                )

        for field_name, spec in documentary_nuclei.items():
            if field_name not in payload:
                if spec.get("absent_policy") == "degrade_if_missing":
                    findings.append(
                        self._finding(
                            "RAW_OPTIONAL_FIELD_MISSING",
                            f"$.{field_name}",
                            f"Optional documentary nucleus '{field_name}' is missing.",
                        )
                    )
                continue

        for field_name, expected in typed_fields.items():
            if field_name not in payload:
                continue
            value = payload[field_name]
            if not self._type_matches(value, expected):
                findings.append(
                    self._finding(
                        "RAW_FIELD_TYPE_MISMATCH",
                        f"$.{field_name}",
                        f"Field '{field_name}' has incompatible type.",
                    )
                )

    def _detect_forbidden_fields_and_values(self, payload: Dict[str, Any], findings: List[ValidationFinding]) -> None:
        for path, node in _deep_iter(payload):
            if isinstance(node, dict):
                for key, value in node.items():
                    key_path = f"{path}.{key}"
                    anomaly = self._classify_key_violation(key, value)
                    if anomaly:
                        findings.append(self._finding(anomaly, key_path, f"Forbidden field detected: '{key}'."))

            if isinstance(node, str):
                for pattern in self._compiled_value_patterns:
                    if pattern.search(node):
                        anomaly = "M07_SCOPE_VIOLATION" if "m07" in node.lower() else "FORBIDDEN_VALUE"
                        findings.append(
                            self._finding(anomaly, path, f"Forbidden conclusive string detected: '{node}'.")
                        )

    def _classify_key_violation(self, key: str, value: Any) -> Optional[str]:
        normalized = _normalize_name(key)
        if normalized in self._allowed_near_misses:
            return None

        if normalized in self._exact_forbidden_normalized:
            if normalized.startswith("m07"):
                return "M07_SCOPE_VIOLATION"
            return "FORBIDDEN_FIELD"

        for pattern in self._compiled_key_patterns:
            if pattern.search(key):
                if re.search(r"(?i)^m07", key):
                    return "M07_SCOPE_VIOLATION"
                return "FORBIDDEN_FIELD"

        if normalized.startswith("m07") and isinstance(value, str):
            if re.search(r"(?i)\b(closed|completed|certified|complete|chiuso|completato|certificato)\b", value):
                return "M07_SCOPE_VIOLATION"

        return None

    def _validate_citations(self, payload: Dict[str, Any], findings: List[ValidationFinding]) -> None:
        required_fields = self.minimum_schema.get("citation_required_fields", [])
        citations = payload.get("citations_valid", [])
        if not isinstance(citations, list):
            return

        for index, citation in enumerate(citations):
            if not isinstance(citation, dict):
                findings.append(
                    self._finding(
                        "CITATION_MISSING_ESSENTIAL",
                        f"$.citations_valid[{index}]",
                        "Citation item is not an object.",
                    )
                )
                continue

            missing = [field for field in required_fields if not citation.get(field)]
            if missing:
                findings.append(
                    self._finding(
                        "CITATION_MISSING_ESSENTIAL",
                        f"$.citations_valid[{index}]",
                        f"Essential citation fields missing: {', '.join(missing)}.",
                    )
                )

    def _validate_vigenza(self, payload: Dict[str, Any], findings: List[ValidationFinding]) -> None:
        uncertain_values = {value.upper() for value in self.minimum_schema.get("vigenza_uncertain_values", [])}
        records = payload.get("vigenza_records", [])
        if not isinstance(records, list):
            return

        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            essential = bool(
                record.get("essential_point_flag")
                or record.get("block_if_uncertain_flag")
                or record.get("essential")
            )
            status = str(record.get("vigore_status", "")).upper()
            if essential and status in uncertain_values:
                findings.append(
                    self._finding(
                        "VIGENZA_ESSENTIAL_UNCERTAIN",
                        f"$.vigenza_records[{index}]",
                        "Vigenza is uncertain on an essential point.",
                    )
                )

    def _validate_crossrefs(self, payload: Dict[str, Any], findings: List[ValidationFinding]) -> None:
        unresolved_values = {value.upper() for value in self.minimum_schema.get("crossref_unresolved_values", [])}
        records = payload.get("cross_reference_records", [])
        if not isinstance(records, list):
            return

        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            essential = bool(
                record.get("essential_ref_flag")
                or record.get("block_if_unresolved_flag")
                or record.get("essential")
            )
            resolved_flag = record.get("resolved_flag")
            resolution_status = str(record.get("resolution_status", "")).upper()
            unresolved = resolved_flag is False or resolution_status in unresolved_values
            if essential and unresolved:
                findings.append(
                    self._finding(
                        "CROSSREF_ESSENTIAL_UNRESOLVED",
                        f"$.cross_reference_records[{index}]",
                        "Essential cross-reference is unresolved.",
                    )
                )

    def _validate_coverage(self, payload: Dict[str, Any], findings: List[ValidationFinding]) -> None:
        record = payload.get("coverage_assessment")
        if not isinstance(record, dict):
            return

        critical_gap = bool(record.get("critical_gap_flag") or record.get("essential_gap_flag"))
        coverage_status = str(record.get("coverage_status", "")).upper()
        block_values = {value.upper() for value in self.minimum_schema.get("coverage_block_values", [])}
        if critical_gap or coverage_status in block_values:
            findings.append(
                self._finding(
                    "COVERAGE_ESSENTIAL_INADEQUATE",
                    "$.coverage_assessment",
                    "Coverage is inadequate on an essential point.",
                )
            )

    def _validate_signal_channels(self, payload: Dict[str, Any], findings: List[ValidationFinding]) -> None:
        has_critical_finding = any(
            finding.anomaly_code in {
                "CITATION_MISSING_ESSENTIAL",
                "VIGENZA_ESSENTIAL_UNCERTAIN",
                "CROSSREF_ESSENTIAL_UNRESOLVED",
                "COVERAGE_ESSENTIAL_INADEQUATE",
            }
            for finding in findings
        )
        if not has_critical_finding:
            return

        if (
            _is_empty_signal(payload.get("warnings"))
            and _is_empty_signal(payload.get("errors"))
            and _is_empty_signal(payload.get("blocks"))
        ):
            findings.append(
                self._finding(
                    "SIGNALS_MISSING_WITH_EVIDENT_CRITICALITY",
                    "$",
                    "Critical documentary issues detected but warnings/errors/blocks are all empty.",
                )
            )

    def _build_result(
        self,
        payload: Optional[Dict[str, Any]],
        findings: List[ValidationFinding],
        request_context: Optional[Dict[str, Any]],
    ) -> RawValidationResult:
        effective_status = "SUCCESS"
        warnings: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        blocks: List[Dict[str, Any]] = []

        for finding in findings:
            if STATUS_ORDER[finding.status] > STATUS_ORDER[effective_status]:
                effective_status = finding.status

            finding_dict = finding.as_dict()
            if finding.status in {"SUCCESS_WITH_WARNINGS", "DEGRADED"}:
                warnings.append(finding_dict)
            elif finding.status in {"BLOCKED", "REJECTED"}:
                blocks.append(finding_dict)
            elif finding.status == "ERROR":
                errors.append(finding_dict)

        if effective_status == "SUCCESS" and warnings:
            effective_status = "SUCCESS_WITH_WARNINGS"

        trace = {
            "validator_module": "runtime.final_ab_runner_raw_validator.FinalABRunnerRawValidator",
            "request_context": request_context or {},
            "effective_status": effective_status,
            "detected_anomalies": [finding.anomaly_code for finding in findings],
            "detected_forbidden_paths": [
                finding.path for finding in findings if finding.anomaly_code in {"FORBIDDEN_FIELD", "FORBIDDEN_VALUE"}
            ],
            "detected_m07_scope_paths": [
                finding.path for finding in findings if finding.anomaly_code == "M07_SCOPE_VIOLATION"
            ],
        }

        return RawValidationResult(
            status=effective_status,
            validated_raw_payload=payload if effective_status in {"SUCCESS", "SUCCESS_WITH_WARNINGS", "DEGRADED", "BLOCKED", "REJECTED"} else None,
            warnings=warnings,
            errors=errors,
            blocks=blocks,
            findings=[finding.as_dict() for finding in findings],
            registry_versions=registry_versions(),
            trace=trace,
        )

    def _finding(self, anomaly_code: str, path: str, message: str) -> ValidationFinding:
        rule = self._rule_map[anomaly_code]
        return ValidationFinding(
            anomaly_code=anomaly_code,
            path=path,
            message=message,
            status=rule["status"],
            severity=rule["severity"],
            block_code=rule.get("block_code"),
        )

    @staticmethod
    def _type_matches(value: Any, expected: Any) -> bool:
        if isinstance(expected, list):
            return any(FinalABRunnerRawValidator._type_matches(value, item) for item in expected)

        mapping = {
            "object": dict,
            "list": list,
            "string": str,
            "null": type(None),
            "boolean": bool,
            "number": (int, float),
        }
        expected_type = mapping.get(expected)
        if expected_type is None:
            return False
        return isinstance(value, expected_type)
