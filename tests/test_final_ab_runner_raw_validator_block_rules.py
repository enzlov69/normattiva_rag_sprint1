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



def test_blocks_incomplete_essential_citation():
    validator = FinalABRunnerRawValidator()
    raw = make_minimal_valid_raw()
    raw["citations_valid"] = [
        {
            "atto_tipo": "D.Lgs.",
            "atto_numero": "267",
            "atto_anno": "2000",
            "articolo": "107",
            "uri_ufficiale": "",
            "stato_vigenza": "VIGENTE_VERIFICATA",
        }
    ]

    result = validator.validate(raw)

    assert result.status == "BLOCKED"
    assert any(block["block_code"] == "CITATION_INCOMPLETE" for block in result.blocks)


def test_blocks_uncertain_essential_vigenza():
    validator = FinalABRunnerRawValidator()
    raw = make_minimal_valid_raw()
    raw["vigenza_records"] = [
        {
            "vigore_status": "VIGENZA_INCERTA",
            "essential_point_flag": True,
            "block_if_uncertain_flag": True,
        }
    ]
    raw["warnings"] = []
    raw["errors"] = []
    raw["blocks"] = []

    result = validator.validate(raw)

    block_codes = {block["block_code"] for block in result.blocks}
    assert result.status == "BLOCKED"
    assert "VIGENZA_UNCERTAIN" in block_codes
    assert "RAW_SIGNAL_INCONSISTENT" in block_codes


def test_blocks_unresolved_essential_cross_reference():
    validator = FinalABRunnerRawValidator()
    raw = make_minimal_valid_raw()
    raw["cross_reference_records"] = [
        {
            "resolution_status": "UNRESOLVED",
            "essential_ref_flag": True,
            "resolved_flag": False,
        }
    ]

    result = validator.validate(raw)

    assert result.status == "BLOCKED"
    assert any(block["block_code"] == "CROSSREF_UNRESOLVED" for block in result.blocks)


def test_blocks_inadequate_essential_coverage():
    validator = FinalABRunnerRawValidator()
    raw = make_minimal_valid_raw()
    raw["coverage_assessment"] = {
        "coverage_status": "INADEQUATE",
        "critical_gap_flag": True,
    }

    result = validator.validate(raw)

    assert result.status == "BLOCKED"
    assert any(block["block_code"] == "COVERAGE_INADEQUATE" for block in result.blocks)
