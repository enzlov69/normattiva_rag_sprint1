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



def test_rejects_explicit_forbidden_field():
    validator = FinalABRunnerRawValidator()
    raw = make_minimal_valid_raw()
    raw["final_decision"] = "GO"

    result = validator.validate(raw)

    assert result.status == "REJECTED"
    assert any(block["block_code"] == "RAG_SCOPE_VIOLATION" for block in result.blocks)


def test_rejects_alias_equivalent_field():
    validator = FinalABRunnerRawValidator()
    raw = make_minimal_valid_raw()
    raw["readyToSign"] = True

    result = validator.validate(raw)

    assert result.status == "REJECTED"
    assert any(block["block_code"] == "RAG_SCOPE_VIOLATION" for block in result.blocks)


def test_rejects_forbidden_conclusive_value_pattern():
    validator = FinalABRunnerRawValidator()
    raw = make_minimal_valid_raw()
    raw["summary"] = "Output authorized"

    result = validator.validate(raw)

    assert result.status == "REJECTED"
    assert any(block["block_code"] == "RAG_SCOPE_VIOLATION" for block in result.blocks)
