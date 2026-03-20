from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, MutableMapping, Optional, Sequence, Set


ALWAYS_ON_PRESIDIA: Set[str] = {
    "OP_ANTI_ALLUCINAZIONI_NORMATIVE",
    "OP_DOPPIA_LENTE_RATIO",
    "OP_COT++",
}

ALLOWED_REQUEST_FIELDS: Set[str] = {
    "request_id",
    "case_id",
    "trace_id",
    "source_level",
    "target_level",
    "request_kind",
    "source_phase",
    "documentary_scope",
    "expected_documentary_outputs",
    "active_presidia",
    "audit",
    "shadow",
}

FORBIDDEN_REQUEST_FIELDS: Set[str] = {
    "final_decision",
    "go_no_go",
    "firma_ready",
    "output_authorized",
    "final_opposability",
    "rac_final_outcome",
    "cf_atti_result",
    "m07_closed",
    "m07_completed",
    "m07_approved",
    "final_validation",
    "output_layer_final",
    "layer_atto_firma_ready",
}

REQUIRED_REQUEST_FIELDS: Set[str] = {
    "request_id",
    "case_id",
    "trace_id",
    "source_level",
    "target_level",
    "request_kind",
    "source_phase",
    "documentary_scope",
    "expected_documentary_outputs",
    "active_presidia",
    "audit",
}

ALLOWED_RESPONSE_FIELDS: Set[str] = {
    "response_id",
    "request_id",
    "source_level",
    "target_level",
    "response_kind",
    "documentary_status",
    "documentary_packet",
    "citations",
    "vigency_checks",
    "cross_references",
    "coverage_report",
    "warnings",
    "errors",
    "blocks",
    "m07_documentary_support",
    "audit",
    "shadow",
}

FORBIDDEN_RESPONSE_FIELDS: Set[str] = {
    "final_decision",
    "go_no_go",
    "firma_ready",
    "output_authorized",
    "final_opposability",
    "rac_final_outcome",
    "cf_atti_result",
    "m07_closed",
    "m07_completed",
    "m07_approved",
    "final_validation",
    "output_layer_final",
    "layer_atto_firma_ready",
}

REQUIRED_RESPONSE_FIELDS: Set[str] = {
    "response_id",
    "request_id",
    "source_level",
    "target_level",
    "response_kind",
    "documentary_status",
    "documentary_packet",
    "warnings",
    "errors",
    "blocks",
    "audit",
}

ALLOWED_REQUEST_KIND = "DOCUMENTARY_SUPPORT_REQUEST"
ALLOWED_RESPONSE_KIND = "DOCUMENTARY_SUPPORT_RESPONSE"

ALLOWED_RESPONSE_STATUSES: Set[str] = {
    "DOCUMENTARY_OK",
    "DOCUMENTARY_WARNING",
    "DOCUMENTARY_BLOCKED",
}

CRITICAL_BLOCK_CODES: Set[str] = {
    "CRITICAL_DOCUMENTARY_BLOCK",
    "M07_DOCUMENTARY_INCOMPLETE",
}

DEGRADING_BLOCK_CODES: Set[str] = {
    "COVERAGE_INSUFFICIENT",
    "CITATION_NOT_IDONEA",
    "VIGENCY_UNCERTAIN",
}


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    status: str
    errors: List[str]
    warnings: List[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "status": self.status,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def _sorted_list(items: Sequence[str] | Set[str]) -> List[str]:
    return sorted(set(items))


def _missing_required_fields(payload: Mapping[str, Any], required_fields: Set[str]) -> List[str]:
    return sorted(field for field in required_fields if field not in payload)


def _forbidden_fields_present(payload: Mapping[str, Any], forbidden_fields: Set[str]) -> List[str]:
    return sorted(field for field in forbidden_fields if field in payload)


def _unexpected_fields_present(payload: Mapping[str, Any], allowed_fields: Set[str]) -> List[str]:
    return sorted(field for field in payload.keys() if field not in allowed_fields)


def validate_level_a_request(payload: Mapping[str, Any]) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []

    missing_fields = _missing_required_fields(payload, REQUIRED_REQUEST_FIELDS)
    forbidden_fields = _forbidden_fields_present(payload, FORBIDDEN_REQUEST_FIELDS)
    unexpected_fields = _unexpected_fields_present(payload, ALLOWED_REQUEST_FIELDS)

    if missing_fields:
        errors.append(f"Missing required request fields: {', '.join(missing_fields)}")
    if forbidden_fields:
        errors.append(f"Forbidden request fields present: {', '.join(forbidden_fields)}")
    if unexpected_fields:
        errors.append(f"Unexpected request fields present: {', '.join(unexpected_fields)}")

    if payload.get("source_level") != "LEVEL_A":
        errors.append("source_level must be LEVEL_A")

    if payload.get("target_level") != "LEVEL_B":
        errors.append("target_level must be LEVEL_B")

    if payload.get("request_kind") != ALLOWED_REQUEST_KIND:
        errors.append("request_kind must be DOCUMENTARY_SUPPORT_REQUEST")

    documentary_scope = payload.get("documentary_scope")
    if not isinstance(documentary_scope, Mapping):
        errors.append("documentary_scope must be a mapping")
    else:
        if documentary_scope.get("must_return_documentary_only") is not True:
            errors.append("documentary_scope.must_return_documentary_only must be True")
        if documentary_scope.get("level_b_is_non_decisional") is not True:
            errors.append("documentary_scope.level_b_is_non_decisional must be True")

    expected_outputs = payload.get("expected_documentary_outputs")
    if not isinstance(expected_outputs, list) or len(expected_outputs) == 0:
        errors.append("expected_documentary_outputs must be a non-empty list")

    active_presidia = payload.get("active_presidia")
    if not isinstance(active_presidia, list):
        errors.append("active_presidia must be a list")
    else:
        missing_presidia = ALWAYS_ON_PRESIDIA.difference(active_presidia)
        if missing_presidia:
            errors.append(
                "Missing always-on presidia in request: "
                + ", ".join(_sorted_list(missing_presidia))
            )

    audit = payload.get("audit")
    if not isinstance(audit, Mapping):
        errors.append("audit must be a mapping")
    else:
        if "created_by" not in audit:
            warnings.append("audit.created_by not present")
        if audit.get("internal_only") is not True:
            warnings.append("audit.internal_only should be True")

    status = "REQUEST_VALID" if not errors else "REQUEST_INVALID"
    return ValidationResult(
        is_valid=not errors,
        status=status,
        errors=errors,
        warnings=warnings,
    )


def validate_level_b_response(payload: Mapping[str, Any]) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []

    missing_fields = _missing_required_fields(payload, REQUIRED_RESPONSE_FIELDS)
    forbidden_fields = _forbidden_fields_present(payload, FORBIDDEN_RESPONSE_FIELDS)
    unexpected_fields = _unexpected_fields_present(payload, ALLOWED_RESPONSE_FIELDS)

    if missing_fields:
        errors.append(f"Missing required response fields: {', '.join(missing_fields)}")
    if forbidden_fields:
        errors.append(f"Forbidden response fields present: {', '.join(forbidden_fields)}")
    if unexpected_fields:
        errors.append(f"Unexpected response fields present: {', '.join(unexpected_fields)}")

    if payload.get("source_level") != "LEVEL_B":
        errors.append("source_level must be LEVEL_B")

    if payload.get("target_level") != "LEVEL_A":
        errors.append("target_level must be LEVEL_A")

    if payload.get("response_kind") != ALLOWED_RESPONSE_KIND:
        errors.append("response_kind must be DOCUMENTARY_SUPPORT_RESPONSE")

    documentary_status = payload.get("documentary_status")
    if documentary_status not in ALLOWED_RESPONSE_STATUSES:
        errors.append(
            "documentary_status must be one of: "
            + ", ".join(_sorted_list(ALLOWED_RESPONSE_STATUSES))
        )

    documentary_packet = payload.get("documentary_packet")
    if not isinstance(documentary_packet, Mapping):
        errors.append("documentary_packet must be a mapping")
    else:
        if documentary_packet.get("documentary_only") is not True:
            errors.append("documentary_packet.documentary_only must be True")
        if documentary_packet.get("contains_decision") is not False:
            errors.append("documentary_packet.contains_decision must be False")

    for list_field in ("warnings", "errors", "blocks"):
        value = payload.get(list_field)
        if not isinstance(value, list):
            errors.append(f"{list_field} must be a list")

    m07_support = payload.get("m07_documentary_support")
    if m07_support is not None:
        if not isinstance(m07_support, Mapping):
            errors.append("m07_documentary_support must be a mapping when present")
        else:
            if m07_support.get("documentary_only") is not True:
                errors.append("m07_documentary_support.documentary_only must be True")
            if m07_support.get("completion_declared") is True:
                errors.append("Level B cannot declare m07 completion")

    audit = payload.get("audit")
    if not isinstance(audit, Mapping):
        errors.append("audit must be a mapping")
    else:
        if audit.get("internal_only") is not True:
            warnings.append("audit.internal_only should be True")

    status = "RESPONSE_VALID" if not errors else "RESPONSE_INVALID"
    return ValidationResult(
        is_valid=not errors,
        status=status,
        errors=errors,
        warnings=warnings,
    )


def propagate_documentary_blocks(response_payload: Mapping[str, Any]) -> Dict[str, Any]:
    blocks = response_payload.get("blocks", [])
    block_codes = {
        block.get("code")
        for block in blocks
        if isinstance(block, Mapping) and "code" in block
    }

    has_critical_block = bool(block_codes.intersection(CRITICAL_BLOCK_CODES))
    has_degrading_block = bool(block_codes.intersection(DEGRADING_BLOCK_CODES))

    if has_critical_block:
        runtime_status = "ROUNDTRIP_BLOCKED"
    elif has_degrading_block:
        runtime_status = "ROUNDTRIP_DEGRADED"
    else:
        runtime_status = "ROUNDTRIP_GREEN"

    return {
        "runtime_status": runtime_status,
        "documentary_block_propagated": len(block_codes) > 0,
        "critical_block_present": has_critical_block,
        "degrading_block_present": has_degrading_block,
        "block_codes_received": _sorted_list({code for code in block_codes if code}),
        "can_emit_go_no_go": False,
        "can_emit_firma_ready": False,
        "can_authorize_output": False,
    }


def build_level_a_internal_envelope(
    request_payload: Mapping[str, Any],
    response_payload: Mapping[str, Any],
    propagation_result: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "envelope_kind": "LEVEL_A_INTERNAL_DOCUMENTARY_RETURN",
        "request_id": request_payload.get("request_id"),
        "response_id": response_payload.get("response_id"),
        "case_id": request_payload.get("case_id"),
        "trace_id": request_payload.get("trace_id"),
        "source_level": "LEVEL_B",
        "target_level": "LEVEL_A",
        "runtime_status": propagation_result.get("runtime_status"),
        "documentary_block_propagated": propagation_result.get("documentary_block_propagated"),
        "critical_block_present": propagation_result.get("critical_block_present"),
        "degrading_block_present": propagation_result.get("degrading_block_present"),
        "block_codes_received": propagation_result.get("block_codes_received", []),
        "documentary_payload": dict(response_payload),
        "audit": {
            "internal_only": True,
            "request_validated": True,
            "response_validated": True,
            "blocks_propagated": True,
        },
        "shadow": {
            "internal_use_only": True,
            "non_opposable": True,
            "contains_no_final_decision": True,
        },
        "can_emit_go_no_go": False,
        "can_emit_firma_ready": False,
        "can_authorize_output": False,
    }


def perform_runtime_roundtrip(
    request_payload: Mapping[str, Any],
    level_b_invoker: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> Dict[str, Any]:
    request_validation = validate_level_a_request(request_payload)
    if not request_validation.is_valid:
        return {
            "runtime_status": "REQUEST_INVALID",
            "request_validation": request_validation.as_dict(),
            "response_validation": None,
            "internal_envelope": None,
        }

    response_payload = level_b_invoker(request_payload)

    response_validation = validate_level_b_response(response_payload)
    if not response_validation.is_valid:
        return {
            "runtime_status": "RESPONSE_INVALID",
            "request_validation": request_validation.as_dict(),
            "response_validation": response_validation.as_dict(),
            "internal_envelope": None,
        }

    propagation_result = propagate_documentary_blocks(response_payload)
    internal_envelope = build_level_a_internal_envelope(
        request_payload=request_payload,
        response_payload=response_payload,
        propagation_result=propagation_result,
    )

    return {
        "runtime_status": propagation_result["runtime_status"],
        "request_validation": request_validation.as_dict(),
        "response_validation": response_validation.as_dict(),
        "internal_envelope": internal_envelope,
    }