from __future__ import annotations

from typing import Any, Dict, List


def build_level_b_response(
    *,
    documentary_status: str = "DOCUMENTARY_OK",
    blocks: List[Dict[str, Any]] | None = None,
    warnings: List[str] | None = None,
    citations: List[Dict[str, Any]] | None = None,
    coverage_status: str = "FULL",
    m07_completion_declared: bool = False,
) -> Dict[str, Any]:
    return {
        "response_id": "RESP-ABA-BLOCK-0001",
        "request_id": "REQ-ABA-BLOCK-0001",
        "source_level": "LEVEL_B",
        "target_level": "LEVEL_A",
        "response_kind": "DOCUMENTARY_SUPPORT_RESPONSE",
        "documentary_status": documentary_status,
        "documentary_packet": {
            "documentary_only": True,
            "contains_decision": False,
        },
        "citations": citations
        if citations is not None
        else [
            {
                "source_type": "norma",
                "citation_text": "D.Lgs. 267/2000, art. 107",
                "official_source": True,
                "idonea": True,
            }
        ],
        "coverage_report": {
            "coverage_status": coverage_status,
        },
        "warnings": warnings or [],
        "errors": [],
        "blocks": blocks or [],
        "m07_documentary_support": {
            "support_provided": True,
            "documentary_only": True,
            "completion_declared": m07_completion_declared,
        },
    }


def evaluate_level_a_after_level_b(response_payload: Dict[str, Any]) -> Dict[str, Any]:
    blocks = response_payload.get("blocks", [])
    citations = response_payload.get("citations", [])
    coverage_status = response_payload.get("coverage_report", {}).get("coverage_status", "UNKNOWN")
    m07_support = response_payload.get("m07_documentary_support", {})

    block_codes = {block["code"] for block in blocks}
    has_critical_block = "CRITICAL_DOCUMENTARY_BLOCK" in block_codes
    has_m07_documentary_incomplete = "M07_DOCUMENTARY_INCOMPLETE" in block_codes
    has_coverage_insufficient = "COVERAGE_INSUFFICIENT" in block_codes
    has_citation_not_idonea = "CITATION_NOT_IDONEA" in block_codes
    has_vigency_uncertain = "VIGENCY_UNCERTAIN" in block_codes

    citation_idoneita = all(citation.get("idonea", False) for citation in citations)

    can_build_valid_rac = not has_m07_documentary_incomplete
    can_mark_full_opposability = (
        not has_critical_block
        and not has_coverage_insufficient
        and not has_citation_not_idonea
        and not has_vigency_uncertain
        and coverage_status == "FULL"
        and citation_idoneita
    )
    can_emit_firma_ready = can_mark_full_opposability and can_build_valid_rac

    if has_critical_block:
        level_a_status = "BLOCKED_BY_LEVEL_B_DOCUMENTARY_BLOCK"
    elif not can_mark_full_opposability:
        level_a_status = "DOCUMENTARY_DEGRADED_REVIEW_REQUIRED"
    else:
        level_a_status = "DOCUMENTARY_OK_FOR_LEVEL_A_REVIEW"

    return {
        "decided_by_level": "LEVEL_A",
        "documentary_block_propagated": len(blocks) > 0,
        "block_codes_received": sorted(block_codes),
        "level_a_status": level_a_status,
        "can_continue_useful_opposable_flow": not has_critical_block,
        "can_build_valid_rac": can_build_valid_rac,
        "can_mark_full_opposability": can_mark_full_opposability,
        "can_emit_firma_ready": can_emit_firma_ready,
        "m07_can_be_considered_complete_by_level_b": bool(
            m07_support.get("completion_declared", False)
        ),
    }


def test_critical_documentary_block_is_propagated_to_level_a() -> None:
    response = build_level_b_response(
        documentary_status="DOCUMENTARY_BLOCKED",
        blocks=[
            {
                "code": "CRITICAL_DOCUMENTARY_BLOCK",
                "severity": "HIGH",
                "documentary_only": True,
            }
        ],
    )

    result = evaluate_level_a_after_level_b(response)

    assert result["documentary_block_propagated"] is True
    assert "CRITICAL_DOCUMENTARY_BLOCK" in result["block_codes_received"]
    assert result["level_a_status"] == "BLOCKED_BY_LEVEL_B_DOCUMENTARY_BLOCK"
    assert result["can_continue_useful_opposable_flow"] is False
    assert result["can_mark_full_opposability"] is False
    assert result["can_emit_firma_ready"] is False
    assert result["decided_by_level"] == "LEVEL_A"


def test_level_a_cannot_ignore_critical_block_from_level_b() -> None:
    response = build_level_b_response(
        documentary_status="DOCUMENTARY_BLOCKED",
        blocks=[
            {
                "code": "CRITICAL_DOCUMENTARY_BLOCK",
                "severity": "HIGH",
                "documentary_only": True,
            }
        ],
    )

    result = evaluate_level_a_after_level_b(response)

    assert result["can_continue_useful_opposable_flow"] is False
    assert result["can_emit_firma_ready"] is False


def test_m07_documentary_incomplete_prevents_valid_rac_building() -> None:
    response = build_level_b_response(
        documentary_status="DOCUMENTARY_BLOCKED",
        blocks=[
            {
                "code": "M07_DOCUMENTARY_INCOMPLETE",
                "severity": "HIGH",
                "documentary_only": True,
            }
        ],
    )

    result = evaluate_level_a_after_level_b(response)

    assert "M07_DOCUMENTARY_INCOMPLETE" in result["block_codes_received"]
    assert result["can_build_valid_rac"] is False
    assert result["can_emit_firma_ready"] is False
    assert result["decided_by_level"] == "LEVEL_A"


def test_coverage_insufficient_prevents_full_opposability() -> None:
    response = build_level_b_response(
        documentary_status="DOCUMENTARY_WARNING",
        coverage_status="PARTIAL",
        blocks=[
            {
                "code": "COVERAGE_INSUFFICIENT",
                "severity": "HIGH",
                "documentary_only": True,
            }
        ],
    )

    result = evaluate_level_a_after_level_b(response)

    assert "COVERAGE_INSUFFICIENT" in result["block_codes_received"]
    assert result["can_mark_full_opposability"] is False
    assert result["can_emit_firma_ready"] is False
    assert result["level_a_status"] == "DOCUMENTARY_DEGRADED_REVIEW_REQUIRED"


def test_citation_not_idonea_prevents_full_opposability() -> None:
    response = build_level_b_response(
        documentary_status="DOCUMENTARY_WARNING",
        citations=[
            {
                "source_type": "norma",
                "citation_text": "Riferimento incompleto",
                "official_source": True,
                "idonea": False,
            }
        ],
        blocks=[
            {
                "code": "CITATION_NOT_IDONEA",
                "severity": "HIGH",
                "documentary_only": True,
            }
        ],
    )

    result = evaluate_level_a_after_level_b(response)

    assert "CITATION_NOT_IDONEA" in result["block_codes_received"]
    assert result["can_mark_full_opposability"] is False
    assert result["can_emit_firma_ready"] is False


def test_vigency_uncertain_prevents_full_opposability() -> None:
    response = build_level_b_response(
        documentary_status="DOCUMENTARY_WARNING",
        blocks=[
            {
                "code": "VIGENCY_UNCERTAIN",
                "severity": "HIGH",
                "documentary_only": True,
            }
        ],
    )

    result = evaluate_level_a_after_level_b(response)

    assert "VIGENCY_UNCERTAIN" in result["block_codes_received"]
    assert result["can_mark_full_opposability"] is False
    assert result["can_emit_firma_ready"] is False


def test_documentary_warning_without_critical_block_keeps_final_decision_in_level_a() -> None:
    response = build_level_b_response(
        documentary_status="DOCUMENTARY_WARNING",
        warnings=["Coverage da riesaminare nel Livello A"],
        coverage_status="PARTIAL",
        blocks=[
            {
                "code": "COVERAGE_INSUFFICIENT",
                "severity": "MEDIUM",
                "documentary_only": True,
            }
        ],
    )

    result = evaluate_level_a_after_level_b(response)

    assert result["decided_by_level"] == "LEVEL_A"
    assert result["can_continue_useful_opposable_flow"] is True
    assert result["can_mark_full_opposability"] is False
    assert result["can_emit_firma_ready"] is False


def test_clean_documentary_response_does_not_auto_authorize_output() -> None:
    response = build_level_b_response(
        documentary_status="DOCUMENTARY_OK",
        coverage_status="FULL",
        blocks=[],
    )

    result = evaluate_level_a_after_level_b(response)

    assert result["level_a_status"] == "DOCUMENTARY_OK_FOR_LEVEL_A_REVIEW"
    assert result["can_mark_full_opposability"] is True
    assert result["can_emit_firma_ready"] is True
    assert result["decided_by_level"] == "LEVEL_A"