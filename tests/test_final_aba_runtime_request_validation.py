from __future__ import annotations

from runtime.final_aba_runtime_handoff_service import (
    ALWAYS_ON_PRESIDIA,
    validate_level_a_request,
)


def build_valid_runtime_request() -> dict:
    return {
        "request_id": "REQ-RUNTIME-0001",
        "case_id": "CASE-RUNTIME-0001",
        "trace_id": "TRACE-RUNTIME-0001",
        "source_level": "LEVEL_A",
        "target_level": "LEVEL_B",
        "request_kind": "DOCUMENTARY_SUPPORT_REQUEST",
        "source_phase": "S3",
        "documentary_scope": {
            "must_return_documentary_only": True,
            "level_b_is_non_decisional": True,
            "objective": "Supporto documentale controllato A->B",
        },
        "expected_documentary_outputs": [
            "sources",
            "citations",
            "vigency_checks",
            "cross_references",
            "coverage_report",
            "warnings",
            "errors",
            "blocks",
        ],
        "active_presidia": sorted(ALWAYS_ON_PRESIDIA),
        "audit": {
            "created_by": "LEVEL_A_RUNTIME",
            "internal_only": True,
        },
        "shadow": {
            "internal_use_only": True,
        },
    }


def test_valid_runtime_request_is_accepted() -> None:
    payload = build_valid_runtime_request()

    result = validate_level_a_request(payload)

    assert result.is_valid is True
    assert result.status == "REQUEST_VALID"
    assert result.errors == []


def test_request_requires_level_a_as_source() -> None:
    payload = build_valid_runtime_request()
    payload["source_level"] = "LEVEL_B"

    result = validate_level_a_request(payload)

    assert result.is_valid is False
    assert "source_level must be LEVEL_A" in result.errors


def test_request_requires_level_b_as_target() -> None:
    payload = build_valid_runtime_request()
    payload["target_level"] = "LEVEL_A"

    result = validate_level_a_request(payload)

    assert result.is_valid is False
    assert "target_level must be LEVEL_B" in result.errors


def test_request_requires_documentary_support_request_kind() -> None:
    payload = build_valid_runtime_request()
    payload["request_kind"] = "FINAL_DECISION_REQUEST"

    result = validate_level_a_request(payload)

    assert result.is_valid is False
    assert "request_kind must be DOCUMENTARY_SUPPORT_REQUEST" in result.errors


def test_request_rejects_forbidden_decisional_field() -> None:
    payload = build_valid_runtime_request()
    payload["firma_ready"] = True

    result = validate_level_a_request(payload)

    assert result.is_valid is False
    assert any("Forbidden request fields present" in error for error in result.errors)
    assert any("firma_ready" in error for error in result.errors)


def test_request_rejects_missing_required_field() -> None:
    payload = build_valid_runtime_request()
    payload.pop("trace_id")

    result = validate_level_a_request(payload)

    assert result.is_valid is False
    assert any("Missing required request fields" in error for error in result.errors)
    assert any("trace_id" in error for error in result.errors)


def test_request_rejects_unexpected_field() -> None:
    payload = build_valid_runtime_request()
    payload["unexpected_field"] = "not_allowed"

    result = validate_level_a_request(payload)

    assert result.is_valid is False
    assert any("Unexpected request fields present" in error for error in result.errors)
    assert any("unexpected_field" in error for error in result.errors)


def test_request_requires_documentary_scope_flags() -> None:
    payload = build_valid_runtime_request()
    payload["documentary_scope"]["must_return_documentary_only"] = False
    payload["documentary_scope"]["level_b_is_non_decisional"] = False

    result = validate_level_a_request(payload)

    assert result.is_valid is False
    assert "documentary_scope.must_return_documentary_only must be True" in result.errors
    assert "documentary_scope.level_b_is_non_decisional must be True" in result.errors


def test_request_requires_expected_documentary_outputs_non_empty() -> None:
    payload = build_valid_runtime_request()
    payload["expected_documentary_outputs"] = []

    result = validate_level_a_request(payload)

    assert result.is_valid is False
    assert "expected_documentary_outputs must be a non-empty list" in result.errors


def test_request_requires_all_always_on_presidia() -> None:
    payload = build_valid_runtime_request()
    payload["active_presidia"] = ["OP_COT++"]

    result = validate_level_a_request(payload)

    assert result.is_valid is False
    assert any("Missing always-on presidia in request" in error for error in result.errors)


def test_request_accepts_shadow_as_internal_only_optional_section() -> None:
    payload = build_valid_runtime_request()

    result = validate_level_a_request(payload)

    assert result.is_valid is True
    assert payload["shadow"]["internal_use_only"] is True


def test_request_without_created_by_in_audit_is_warning_not_hard_error() -> None:
    payload = build_valid_runtime_request()
    payload["audit"].pop("created_by")

    result = validate_level_a_request(payload)

    assert result.is_valid is True
    assert "audit.created_by not present" in result.warnings


def test_request_with_audit_internal_only_false_generates_warning() -> None:
    payload = build_valid_runtime_request()
    payload["audit"]["internal_only"] = False

    result = validate_level_a_request(payload)

    assert result.is_valid is True
    assert "audit.internal_only should be True" in result.warnings