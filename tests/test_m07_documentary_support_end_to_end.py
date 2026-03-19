def simulate_m07_documentary_support(case: dict) -> dict:
    """
    Simulatore minimale E2E del solo adapter documentale.
    Non conclude il caso, non produce GO/NO_GO e non chiude M07.
    """

    response = {
        "request_id": case["request_id"],
        "case_id": case["case_id"],
        "trace_id": case["trace_id"],
        "api_version": "2.0",
        "responder_module": "B16_M07SupportLayer",
        "status": "SUCCESS",
        "payload": {
            "documentary_packet": {
                "source_ids": case.get("source_ids", []),
                "norm_unit_ids": case.get("norm_unit_ids", []),
                "support_only_flag": True
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": "2026-03-19T10:00:01Z"
    }

    if case.get("citation_incomplete"):
        response["status"] = "BLOCKED"
        response["blocks"].append({
            "block_id": "blk_cit_001",
            "case_id": case["case_id"],
            "block_code": "CITATION_INCOMPLETE",
            "block_category": "CITATION",
            "block_severity": "CRITICAL",
            "origin_module": "B15_CitationBuilder",
            "block_reason": "citazione incompleta",
            "block_status": "OPEN"
        })

    if case.get("vigenza_uncertain"):
        response["status"] = "DEGRADED" if response["status"] == "SUCCESS" else response["status"]
        response["blocks"].append({
            "block_id": "blk_vig_001",
            "case_id": case["case_id"],
            "block_code": "VIGENZA_UNCERTAIN",
            "block_category": "VIGENZA",
            "block_severity": "HIGH",
            "origin_module": "B13_VigenzaChecker",
            "block_reason": "vigenza incerta su punto essenziale",
            "block_status": "OPEN"
        })

    if case.get("crossref_unresolved"):
        response["status"] = "BLOCKED"
        response["blocks"].append({
            "block_id": "blk_xref_001",
            "case_id": case["case_id"],
            "block_code": "CROSSREF_UNRESOLVED",
            "block_category": "CROSSREF",
            "block_severity": "CRITICAL",
            "origin_module": "B14_CrossReferenceResolver",
            "block_reason": "rinvio essenziale irrisolto",
            "block_status": "OPEN"
        })

    if case.get("audit_missing"):
        response["status"] = "BLOCKED"
        response["blocks"].append({
            "block_id": "blk_audit_001",
            "case_id": case["case_id"],
            "block_code": "AUDIT_INCOMPLETE",
            "block_category": "AUDIT",
            "block_severity": "CRITICAL",
            "origin_module": "B19_AuditLogger",
            "block_reason": "audit mancante su snodo critico",
            "block_status": "OPEN"
        })

    if case.get("conclusive_attempt"):
        response["status"] = "REJECTED"
        response["blocks"].append({
            "block_id": "blk_scope_001",
            "case_id": case["case_id"],
            "block_code": "RAG_SCOPE_VIOLATION",
            "block_category": "BOUNDARY",
            "block_severity": "CRITICAL",
            "origin_module": "B17_GuardrailEngine",
            "block_reason": "tentativo di sconfinamento conclusivo",
            "block_status": "OPEN"
        })

    if case.get("m07_required", True):
        response["payload"]["documentary_packet"]["m07_evidence_pack"] = {
            "record_id": "rec_m07_001",
            "record_type": "M07EvidencePack",
            "m07_pack_id": "m07pack_001",
            "case_id": case["case_id"],
            "source_ids": case.get("source_ids", []),
            "norm_unit_ids": case.get("norm_unit_ids", []),
            "ordered_reading_sequence": [],
            "annex_refs": [],
            "crossref_refs": [],
            "coverage_ref_id": "cov_001",
            "missing_elements": [],
            "m07_support_status": "READY_FOR_HUMAN_READING",
            "human_completion_required": True,
            "created_at": "2026-03-19T10:00:00Z",
            "updated_at": "2026-03-19T10:00:00Z",
            "schema_version": "1.0",
            "record_version": 1,
            "source_layer": "B",
            "trace_id": case["trace_id"],
            "active_flag": True
        }

    return response


def test_e2e_ordinary_case_returns_support_only_packet() -> None:
    case = {
        "request_id": "req_0001",
        "case_id": "case_001",
        "trace_id": "trace_001",
        "source_ids": ["source_tuel_267_2000"],
        "norm_unit_ids": ["normunit_art107"],
        "m07_required": True
    }

    response = simulate_m07_documentary_support(case)

    assert response["status"] == "SUCCESS"
    assert response["payload"]["documentary_packet"]["support_only_flag"] is True
    assert "m07_evidence_pack" in response["payload"]["documentary_packet"]
    assert response["payload"]["documentary_packet"]["m07_evidence_pack"]["human_completion_required"] is True


def test_e2e_citation_incomplete_blocks_flow() -> None:
    case = {
        "request_id": "req_0002",
        "case_id": "case_002",
        "trace_id": "trace_002",
        "citation_incomplete": True,
        "m07_required": True
    }

    response = simulate_m07_documentary_support(case)

    assert response["status"] == "BLOCKED"
    assert any(block["block_code"] == "CITATION_INCOMPLETE" for block in response["blocks"])


def test_e2e_vigenza_uncertain_degrades_or_blocks() -> None:
    case = {
        "request_id": "req_0003",
        "case_id": "case_003",
        "trace_id": "trace_003",
        "vigenza_uncertain": True,
        "m07_required": True
    }

    response = simulate_m07_documentary_support(case)

    assert response["status"] in {"DEGRADED", "BLOCKED"}
    assert any(block["block_code"] == "VIGENZA_UNCERTAIN" for block in response["blocks"])


def test_e2e_crossref_unresolved_blocks_flow() -> None:
    case = {
        "request_id": "req_0004",
        "case_id": "case_004",
        "trace_id": "trace_004",
        "crossref_unresolved": True,
        "m07_required": True
    }

    response = simulate_m07_documentary_support(case)

    assert response["status"] == "BLOCKED"
    assert any(block["block_code"] == "CROSSREF_UNRESOLVED" for block in response["blocks"])


def test_e2e_conclusive_attempt_is_rejected() -> None:
    case = {
        "request_id": "req_0005",
        "case_id": "case_005",
        "trace_id": "trace_005",
        "conclusive_attempt": True,
        "m07_required": True
    }

    response = simulate_m07_documentary_support(case)

    assert response["status"] == "REJECTED"
    assert any(block["block_code"] == "RAG_SCOPE_VIOLATION" for block in response["blocks"])


def test_e2e_missing_audit_blocks_release() -> None:
    case = {
        "request_id": "req_0006",
        "case_id": "case_006",
        "trace_id": "trace_006",
        "audit_missing": True,
        "m07_required": True
    }

    response = simulate_m07_documentary_support(case)

    assert response["status"] == "BLOCKED"
    assert any(block["block_code"] == "AUDIT_INCOMPLETE" for block in response["blocks"])