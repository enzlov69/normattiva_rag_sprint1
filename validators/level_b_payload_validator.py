from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json

from .level_b_result_model import LevelBPayloadResult, ValidationReport
from .level_b_semantic_rules import (
    scan_for_forbidden_fields,
    validate_audit_shadow,
    validate_blocks,
    validate_citations,
    validate_m07_boundaries,
    validate_minimum_contract,
    validate_status_coherence,
)

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "level_b_payload_schema_v1.json"

try:
    import jsonschema
except Exception:  # pragma: no cover
    jsonschema = None


def _validate_with_jsonschema(data: Dict[str, Any], report: ValidationReport) -> None:
    if jsonschema is None:
        return
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for error in validator.iter_errors(data):
        path = "/" + "/".join(str(part) for part in error.absolute_path)
        report.add("SCHEMA_VALIDATION_FAILED", "ERROR", error.message, path)


def validate_level_b_payload(data: Dict[str, Any]) -> ValidationReport:
    report = ValidationReport(ok=True)

    validate_minimum_contract(data, report)
    _validate_with_jsonschema(data, report)

    # Stop parsing only if the minimum contract is broken beyond safe instantiation.
    if report.error_count and any(f.code in {"INVALID_STATUS", "MISSING_PAYLOAD"} for f in report.findings):
        report.ok = False
        return report

    try:
        result = LevelBPayloadResult.from_dict(data)
    except Exception as exc:  # pragma: no cover
        report.add("SCHEMA_VALIDATION_FAILED", "ERROR", f"Impossibile materializzare il result model: {exc}")
        report.ok = False
        return report

    scan_for_forbidden_fields(data, report)
    validate_status_coherence(result, report)
    validate_blocks(result, report)
    validate_audit_shadow(result.payload, report)
    validate_m07_boundaries(result.payload, report)
    validate_citations(result.payload, report)

    report.ok = report.error_count == 0
    return report
