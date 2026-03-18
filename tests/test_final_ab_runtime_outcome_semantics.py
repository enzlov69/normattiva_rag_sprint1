import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "schemas" / "final_ab_runtime_anomaly_registry_v1.json"
CANON_PATH = ROOT / "schemas" / "final_ab_runtime_severity_canon_v1.json"
MATRIX_PATH = ROOT / "schemas" / "final_ab_runtime_propagation_matrix_v1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _registry_index():
    registry = _load(REGISTRY_PATH)
    return {item["anomaly_code"]: item for item in registry["anomalies"]}


def test_warning_rows_do_not_block_without_explicit_matrix_exception():
    matrix = _load(MATRIX_PATH)
    for row in matrix["rows"]:
        if row["signal_class"] != "WARNING":
            continue
        if row["envelope_status"] in {"BLOCKED", "REJECTED"}:
            assert "EXCEPTION:" in row.get("notes", "")


def test_internal_rows_never_mark_opponibility_block():
    matrix = _load(MATRIX_PATH)
    for row in matrix["rows"]:
        if row["signal_class"] == "INTERNAL":
            assert row["blocks_opponibility"] is False


def test_boundary_critical_is_always_blocked_or_rejected():
    matrix = _load(MATRIX_PATH)
    for row in matrix["rows"]:
        if row["family"] == "BOUNDARY" and row["severity"] == "CRITICAL":
            assert row["envelope_status"] in {"BLOCKED", "REJECTED"}
            assert row["runtime_effect"] in {"BLOCK_RESPONSE", "REJECT_RESPONSE"}


def test_documentary_critical_never_internal_and_never_release_allowed():
    anomalies = _registry_index()
    for item in anomalies.values():
        if item["family"] == "DOCUMENTARY" and item["default_severity"] == "CRITICAL":
            assert item["default_signal_class"] != "INTERNAL"
            assert item["release_allowed"] is False


def test_traceability_critical_not_cosmetic_when_opponibility_is_affected():
    anomalies = _registry_index()
    for item in anomalies.values():
        if item["family"] == "TRACEABILITY" and item["default_severity"] == "CRITICAL":
            assert item["blocks_opponibility"] is True
            assert item["propagate_to_level_a"] is True
            assert item["default_signal_class"] in {"ERROR", "BLOCK"}


def test_forbidden_field_and_rag_scope_have_restrictive_outcomes():
    anomalies = _registry_index()
    for code in ("FORBIDDEN_FIELD_PRESENT", "RAG_SCOPE_VIOLATION"):
        item = anomalies[code]
        assert item["default_envelope_status"] in {"BLOCKED", "REJECTED"}
        assert item["default_runtime_effect"] in {"BLOCK_RESPONSE", "REJECT_RESPONSE"}
        assert item["propagate_to_level_a"] is True


def test_m07_boundary_violation_is_boundary_and_m07_sensitive():
    item = _registry_index()["M07_BOUNDARY_VIOLATION"]
    assert item["family"] == "BOUNDARY"
    assert item["boundary_sensitive"] is True
    assert item["m07_sensitive"] is True
    assert item["default_envelope_status"] in {"BLOCKED", "REJECTED"}


def test_documentary_packet_integrity_broken_blocks_full_reliability():
    item = _registry_index()["DOCUMENTARY_PACKET_INTEGRITY_BROKEN"]
    assert item["documentary_integrity_sensitive"] is True
    assert item["blocks_opponibility"] is True
    assert item["default_envelope_status"] in {"BLOCKED", "REJECTED"}


def test_audit_shadow_incomplete_have_traceability_blocking_semantics():
    anomalies = _registry_index()
    for code in ("AUDIT_INCOMPLETE", "SHADOW_INCOMPLETE"):
        item = anomalies[code]
        assert item["traceability_sensitive"] is True
        assert item["default_envelope_status"] in {"BLOCKED", "REJECTED"}
        assert item["default_signal_class"] == "BLOCK"


def test_canon_hard_rules_are_represented_by_matrix_rows():
    canon = _load(CANON_PATH)
    matrix = _load(MATRIX_PATH)

    assert "LOW cannot map to BLOCK_RESPONSE." in canon["hard_rules"]
    assert "CRITICAL cannot map to INTERNAL signal class." in canon["hard_rules"]

    for row in matrix["rows"]:
        if row["severity"] == "LOW":
            assert row["runtime_effect"] != "BLOCK_RESPONSE"
        if row["severity"] == "CRITICAL":
            assert row["signal_class"] != "INTERNAL"
