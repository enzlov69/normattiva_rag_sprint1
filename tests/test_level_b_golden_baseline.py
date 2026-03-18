from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.level_b_golden_rules import (
    assert_basic_status_coherence,
    audit_present,
    collect_block_codes,
    collect_error_codes,
    collect_warning_codes,
    find_forbidden_fields,
    has_conclusive_semantics,
    load_json,
    m07_support_requires_human_completion,
    run_existing_validator,
    shadow_present,
    status_matches_family,
    valid_citations_without_uri,
)

REGISTRY_PATH = ROOT / "schemas" / "level_b_golden_baseline_registry_v1.json"


def load_registry() -> dict:
    return load_json(REGISTRY_PATH)


def iter_cases() -> list[dict]:
    registry = load_registry()
    return registry["cases"]


@pytest.mark.parametrize("case_meta", iter_cases(), ids=lambda c: c["case_id"])
def test_level_b_golden_baseline(case_meta: dict) -> None:
    fixture_path = ROOT / case_meta["fixture_path"]
    assert fixture_path.exists(), f"Fixture mancante: {fixture_path}"

    payload = load_json(fixture_path)
    status = str(payload.get("status", "")).upper()

    assert status == case_meta["expected_status"], (
        f"{case_meta['case_id']}: status atteso {case_meta['expected_status']}, ottenuto {status}"
    )
    assert status_matches_family(status, case_meta["family"]), (
        f"{case_meta['case_id']}: famiglia {case_meta['family']} incoerente con status {status}"
    )

    coherence_problems = assert_basic_status_coherence(payload)
    assert not coherence_problems, f"{case_meta['case_id']}: incoerenze status -> {coherence_problems}"

    expected_blocks = sorted(case_meta.get("expected_blocks", []))
    expected_errors = sorted(case_meta.get("expected_errors", []))
    expected_warnings = sorted(case_meta.get("expected_warnings", []))

    actual_blocks = sorted(collect_block_codes(payload))
    actual_errors = sorted(collect_error_codes(payload))
    actual_warnings = sorted(collect_warning_codes(payload))

    assert actual_blocks == expected_blocks, (
        f"{case_meta['case_id']}: blocks attesi {expected_blocks}, ottenuti {actual_blocks}"
    )
    assert actual_errors == expected_errors, (
        f"{case_meta['case_id']}: errors attesi {expected_errors}, ottenuti {actual_errors}"
    )
    assert actual_warnings == expected_warnings, (
        f"{case_meta['case_id']}: warnings attesi {expected_warnings}, ottenuti {actual_warnings}"
    )

    if case_meta["expected_status"] in {"SUCCESS", "DEGRADED"}:
        assert not find_forbidden_fields(payload), f"{case_meta['case_id']}: campi vietati presenti"
        assert not has_conclusive_semantics(payload), f"{case_meta['case_id']}: semantica conclusiva non ammessa"
        assert audit_present(payload), f"{case_meta['case_id']}: audit obbligatorio assente"
        assert shadow_present(payload), f"{case_meta['case_id']}: SHADOW obbligatorio assente"

    if "M07" in case_meta["case_id"] or "m07" in case_meta["fixture_path"]:
        assert m07_support_requires_human_completion(payload), (
            f"{case_meta['case_id']}: human_completion_required deve essere true"
        )

    if case_meta["case_id"] == "GB-REJECT-003":
        assert valid_citations_without_uri(payload), (
            f"{case_meta['case_id']}: il caso golden deve contenere una citazione VALID senza URI"
        )
    else:
        assert not valid_citations_without_uri(payload), (
            f"{case_meta['case_id']}: non deve esistere alcuna citazione VALID senza URI"
        )

    validator_result = run_existing_validator(payload)
    if validator_result is not None:
        validator_status = str(validator_result.get("status", status)).upper()
        assert validator_status == case_meta["expected_status"], (
            f"{case_meta['case_id']}: il validator esistente ha restituito {validator_status}, "
            f"atteso {case_meta['expected_status']}"
        )
