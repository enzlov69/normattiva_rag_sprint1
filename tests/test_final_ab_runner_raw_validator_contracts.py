import copy

from runtime.final_ab_runner_raw_validator import FinalABRunnerRawValidator

def make_minimal_valid_raw():
    return {
        "sources": [],
        "norm_units": [],
        "citations_valid": [],
        "citations_blocked": [],
        "vigenza_records": [],
        "cross_reference_records": [],
        "coverage_assessment": None,
        "warnings": [],
        "errors": [],
        "blocks": [],
        "shadow_fragment": {"executed_modules": ["B10", "B15"], "technical_notes": []}
    }



def test_accepts_minimum_conform_raw_output():
    validator = FinalABRunnerRawValidator()
    raw = make_minimal_valid_raw()

    result = validator.validate(raw)

    assert result.status == "SUCCESS"
    assert result.errors == []
    assert result.blocks == []


def test_rejects_missing_required_control_channels():
    validator = FinalABRunnerRawValidator()
    raw = make_minimal_valid_raw()
    raw.pop("warnings")
    raw.pop("errors")
    raw.pop("blocks")

    result = validator.validate(raw)

    assert result.status == "REJECTED"
    block_codes = {block["block_code"] for block in result.blocks}
    assert "RAW_CONTRACT_MISSING" in block_codes


def test_degrades_when_noncritical_documentary_nuclei_are_missing():
    validator = FinalABRunnerRawValidator()
    raw = make_minimal_valid_raw()
    raw.pop("sources")
    raw.pop("norm_units")
    raw.pop("coverage_assessment")

    result = validator.validate(raw)

    assert result.status == "DEGRADED"
    warning_codes = {warning["block_code"] for warning in result.warnings}
    assert "RAW_STRUCTURE_INCOMPLETE" in warning_codes


def test_errors_on_type_mismatch():
    validator = FinalABRunnerRawValidator()
    raw = make_minimal_valid_raw()
    raw["warnings"] = {}

    result = validator.validate(raw)

    assert result.status == "ERROR"
    error_codes = {error["block_code"] for error in result.errors}
    assert "RAW_PAYLOAD_TYPE_MISMATCH" in error_codes
