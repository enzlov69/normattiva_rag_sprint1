from __future__ import annotations

from typing import Any, Dict


def build_level_a_request_for_m07() -> Dict[str, Any]:
    return {
        "request_id": "REQ-M07-0001",
        "source_level": "LEVEL_A",
        "target_level": "LEVEL_B",
        "request_kind": "DOCUMENTARY_SUPPORT_REQUEST",
        "source_phase": "S3",
        "documentary_scope": {
            "objective": "Supporto documentale a M07-LPR",
            "must_return_documentary_only": True,
            "level_b_is_non_decisional": True,
        },
        "expected_documentary_outputs": [
            "sources",
            "citations",
            "cross_references",
            "warnings",
            "errors",
            "blocks",
            "documentary_support_packet",
        ],
    }


def build_level_b_m07_response(*, completion_declared: bool = False) -> Dict[str, Any]:
    return {
        "response_id": "RESP-M07-0001",
        "request_id": "REQ-M07-0001",
        "source_level": "LEVEL_B",
        "target_level": "LEVEL_A",
        "response_kind": "DOCUMENTARY_SUPPORT_RESPONSE",
        "documentary_status": "DOCUMENTARY_OK",
        "m07_documentary_support": {
            "support_provided": True,
            "documentary_only": True,
            "completion_declared": completion_declared,
            "last_comma_checked": True,
            "cross_references_rebuilt": True,
        },
        "blocks": [],
        "warnings": [],
        "errors": [],
    }


def evaluate_m07_roundtrip_boundary(
    request_payload: Dict[str, Any],
    response_payload: Dict[str, Any],
    *,
    level_a_formal_completion: bool = False,
) -> Dict[str, Any]:
    request_is_documentary_only = (
        request_payload["documentary_scope"]["must_return_documentary_only"] is True
    )
    level_b_completion_declared = response_payload["m07_documentary_support"]["completion_declared"]

    level_b_can_close_m07 = False
    level_a_can_treat_m07_as_complete = bool(level_a_formal_completion)

    if level_b_completion_declared:
        boundary_status = "LEVEL_B_OVERREACH_ON_M07"
    elif level_a_can_treat_m07_as_complete:
        boundary_status = "M07_COMPLETED_BY_LEVEL_A_ONLY"
    else:
        boundary_status = "M07_DOCUMENTARY_SUPPORT_ONLY"

    return {
        "request_is_documentary_only": request_is_documentary_only,
        "level_b_can_close_m07": level_b_can_close_m07,
        "level_b_completion_declared": level_b_completion_declared,
        "level_a_can_treat_m07_as_complete": level_a_can_treat_m07_as_complete,
        "boundary_status": boundary_status,
    }


def test_level_a_can_request_documentary_support_for_m07() -> None:
    request = build_level_a_request_for_m07()

    assert request["source_phase"] == "S3"
    assert request["documentary_scope"]["must_return_documentary_only"] is True
    assert request["documentary_scope"]["level_b_is_non_decisional"] is True


def test_level_b_can_support_m07_documentally_but_cannot_close_it() -> None:
    request = build_level_a_request_for_m07()
    response = build_level_b_m07_response(completion_declared=False)

    result = evaluate_m07_roundtrip_boundary(request, response)

    assert result["request_is_documentary_only"] is True
    assert result["level_b_can_close_m07"] is False
    assert result["level_b_completion_declared"] is False
    assert result["boundary_status"] == "M07_DOCUMENTARY_SUPPORT_ONLY"


def test_level_b_declared_completion_is_an_overreach() -> None:
    request = build_level_a_request_for_m07()
    response = build_level_b_m07_response(completion_declared=True)

    result = evaluate_m07_roundtrip_boundary(request, response)

    assert result["level_b_completion_declared"] is True
    assert result["level_b_can_close_m07"] is False
    assert result["boundary_status"] == "LEVEL_B_OVERREACH_ON_M07"


def test_only_level_a_can_consider_m07_formally_completed() -> None:
    request = build_level_a_request_for_m07()
    response = build_level_b_m07_response(completion_declared=False)

    result = evaluate_m07_roundtrip_boundary(
        request,
        response,
        level_a_formal_completion=True,
    )

    assert result["level_b_can_close_m07"] is False
    assert result["level_a_can_treat_m07_as_complete"] is True
    assert result["boundary_status"] == "M07_COMPLETED_BY_LEVEL_A_ONLY"


def test_level_b_documentary_support_does_not_equate_to_m07_completion() -> None:
    request = build_level_a_request_for_m07()
    response = build_level_b_m07_response(completion_declared=False)

    result = evaluate_m07_roundtrip_boundary(request, response)

    assert response["m07_documentary_support"]["support_provided"] is True
    assert response["m07_documentary_support"]["documentary_only"] is True
    assert result["level_a_can_treat_m07_as_complete"] is False


def test_level_b_cannot_complete_m07_even_if_last_comma_and_cross_references_are_present() -> None:
    request = build_level_a_request_for_m07()
    response = build_level_b_m07_response(completion_declared=False)

    support = response["m07_documentary_support"]
    assert support["last_comma_checked"] is True
    assert support["cross_references_rebuilt"] is True

    result = evaluate_m07_roundtrip_boundary(request, response)

    assert result["level_b_can_close_m07"] is False
    assert result["boundary_status"] == "M07_DOCUMENTARY_SUPPORT_ONLY"


def test_m07_boundary_preserves_final_governance_in_level_a() -> None:
    request = build_level_a_request_for_m07()
    response = build_level_b_m07_response(completion_declared=False)

    result = evaluate_m07_roundtrip_boundary(request, response)

    assert result["request_is_documentary_only"] is True
    assert result["level_b_can_close_m07"] is False
    assert result["level_a_can_treat_m07_as_complete"] is False