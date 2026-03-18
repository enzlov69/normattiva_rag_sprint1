import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "schemas" / "final_ab_runtime_anomaly_registry_v1.json"
CANON_PATH = ROOT / "schemas" / "final_ab_runtime_severity_canon_v1.json"
MATRIX_PATH = ROOT / "schemas" / "final_ab_runtime_propagation_matrix_v1.json"


REQUIRED_CODES = {
    "MISSING_REQUEST_ID",
    "MISSING_CASE_ID",
    "MISSING_TRACE_ID",
    "MISSING_API_VERSION",
    "MISSING_CALLER_MODULE",
    "MISSING_TARGET_MODULE",
    "RESPONSE_ENVELOPE_MISSING",
    "RESPONSE_STATUS_INVALID",
    "RESPONSE_TIMESTAMP_MISSING",
    "RESPONSE_PAYLOAD_MISSING",
    "RESPONSE_WARNINGS_INCONSISTENT",
    "RESPONSE_ERRORS_INCONSISTENT",
    "RESPONSE_BLOCKS_INCONSISTENT",
    "RESPONDER_MODULE_MISMATCH",
    "DOCUMENTARY_PACKET_MISSING",
    "DOCUMENTARY_PACKET_INCOMPLETE",
    "DOCUMENTARY_PACKET_TRACE_MISSING",
    "DOCUMENTARY_PACKET_INTEGRITY_BROKEN",
    "SOURCE_UNVERIFIED",
    "CITATION_INCOMPLETE",
    "VIGENZA_UNCERTAIN",
    "CROSSREF_UNRESOLVED",
    "COVERAGE_INADEQUATE",
    "AUDIT_INCOMPLETE",
    "SHADOW_INCOMPLETE",
    "RAG_SCOPE_VIOLATION",
    "M07_BOUNDARY_VIOLATION",
    "FORBIDDEN_FIELD_PRESENT",
    "OUTPUT_NOT_OPPONIBLE",
}


REQUIRED_FIELDS = {
    "anomaly_code",
    "title",
    "family",
    "description",
    "default_severity",
    "default_signal_class",
    "default_runtime_effect",
    "default_envelope_status",
    "propagate_to_level_a",
    "level_a_effect",
    "blocks_opponibility",
    "boundary_sensitive",
    "m07_sensitive",
    "documentary_integrity_sensitive",
    "traceability_sensitive",
    "release_allowed",
    "notes",
}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_registry_has_required_codes_and_no_duplicates():
    registry = _load(REGISTRY_PATH)
    anomalies = registry["anomalies"]

    codes = [item["anomaly_code"] for item in anomalies]
    assert len(codes) == len(set(codes))
    assert REQUIRED_CODES.issubset(set(codes))


def test_registry_entries_have_all_required_fields():
    registry = _load(REGISTRY_PATH)
    for item in registry["anomalies"]:
        assert REQUIRED_FIELDS.issubset(item.keys())


def test_registry_values_are_defined_in_severity_canon():
    registry = _load(REGISTRY_PATH)
    canon = _load(CANON_PATH)

    severities = {row["name"] for row in canon["severities"]}
    signal_classes = set(canon["signal_classes"])
    runtime_effects = set(canon["runtime_effects"])
    envelope_statuses = set(canon["envelope_statuses"])
    level_a_effects = set(canon["level_a_effects"])

    for item in registry["anomalies"]:
        assert item["default_severity"] in severities
        assert item["default_signal_class"] in signal_classes
        assert item["default_runtime_effect"] in runtime_effects
        assert item["default_envelope_status"] in envelope_statuses
        assert item["level_a_effect"] in level_a_effects


def test_each_registry_anomaly_has_resolvable_matrix_trajectory():
    registry = _load(REGISTRY_PATH)
    matrix = _load(MATRIX_PATH)

    trajectories = {
        (row["family"], row["severity"], row["signal_class"])
        for row in matrix["rows"]
    }

    for item in registry["anomalies"]:
        key = (item["family"], item["default_severity"], item["default_signal_class"])
        assert key in trajectories


def test_blocks_opponibility_true_is_never_internal_signal():
    registry = _load(REGISTRY_PATH)

    for item in registry["anomalies"]:
        if item["blocks_opponibility"] is True:
            assert item["default_signal_class"] != "INTERNAL"


def test_blocked_or_rejected_release_is_forbidden_without_explicit_exception():
    registry = _load(REGISTRY_PATH)

    for item in registry["anomalies"]:
        status = item["default_envelope_status"]
        if status not in {"BLOCKED", "REJECTED"}:
            continue
        if item["release_allowed"] is True:
            assert "EXCEPTION:" in item["notes"]
        else:
            assert item["release_allowed"] is False


def test_registry_families_cover_required_set():
    registry = _load(REGISTRY_PATH)
    families = {item["family"] for item in registry["anomalies"]}
    assert {"CONTRACTUAL", "DOCUMENTARY", "TRACEABILITY", "BOUNDARY", "COMPLETENESS"}.issubset(families)
