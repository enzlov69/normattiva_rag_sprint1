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



def test_rejects_explicit_m07_completion_flag():
    validator = FinalABRunnerRawValidator()
    raw = make_minimal_valid_raw()
    raw["m07_completed"] = True

    result = validator.validate(raw)

    assert result.status == "REJECTED"
    assert any(block["block_code"] == "RAG_SCOPE_VIOLATION" for block in result.blocks)


def test_rejects_m07_certification_value():
    validator = FinalABRunnerRawValidator()
    raw = make_minimal_valid_raw()
    raw["m07_status"] = "M07 completed"

    result = validator.validate(raw)

    assert result.status == "REJECTED"
    assert any(block["block_code"] == "RAG_SCOPE_VIOLATION" for block in result.blocks)


def test_allows_documentary_m07_support_without_closure():
    validator = FinalABRunnerRawValidator()
    raw = make_minimal_valid_raw()
    raw["m07_support"] = {
        "ordered_reading_sequence": ["art_1", "art_2"],
        "missing_elements": [],
        "human_completion_required": True,
        "support_status": "PREPARATORY"
    }

    result = validator.validate(raw)

    assert result.status == "SUCCESS"
