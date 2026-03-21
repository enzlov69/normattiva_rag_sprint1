from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft202012Validator


JsonDict = Dict[str, Any]

API_VERSION = "1.0"
TARGET_MODULE = "B_REAL_FEDERATED_RUNNER"
REQUEST_TYPE = "DOCUMENTARY_SUPPORT_REQUEST"
REQUEST_KIND = "METHOD_DOCUMENTARY_SUPPORT"
DEFAULT_ALLOWED_CHANNELS = (
    "FEDERATED_ONLY",
    "FEDERATED_PLUS_INSTITUTIONAL_WEB",
    "INSTITUTIONAL_WEB_ONLY",
)

REQUIRED_INPUT_FIELDS = (
    "request_id",
    "case_id",
    "trace_id",
    "natura_output",
    "tipologia_atto",
    "materia_prevalente",
    "sensibilita",
    "rischio_iniziale",
    "intensita_applicativa",
    "zone_rosse",
    "fast_track",
    "moduli_attivati",
    "esigenza_documentale",
    "obiettivo_documentale",
    "query_guidata",
    "corpora_preferiti",
    "contesto_metodologico",
    "caller_module",
)

FORBIDDEN_DECISION_KEYS = {
    "final_decision",
    "decision_status",
    "go_no_go",
    "output_authorized",
    "rac_finalized",
    "rac_approved",
    "m07_closed",
    "m07_completed",
    "m07_certified",
}


class DocumentaryRequestBuilderError(ValueError):
    """Raised when the classified input cannot be adapted to the A-side documentary contract."""


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_schema() -> JsonDict:
    path = _project_root() / "schemas" / "method_documentary_request_schema_v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validate_minimum_input(classified_case: JsonDict) -> None:
    missing = [field for field in REQUIRED_INPUT_FIELDS if field not in classified_case]
    if missing:
        raise DocumentaryRequestBuilderError(
            f"Missing required classified input fields: {', '.join(missing)}"
        )

    forbidden_hits = sorted(FORBIDDEN_DECISION_KEYS.intersection(classified_case.keys()))
    if forbidden_hits:
        raise DocumentaryRequestBuilderError(
            "Classified input already contains forbidden decision fields: "
            + ", ".join(forbidden_hits)
        )

    if not isinstance(classified_case.get("moduli_attivati"), list):
        raise DocumentaryRequestBuilderError("moduli_attivati must be a list.")
    if not isinstance(classified_case.get("corpora_preferiti"), list):
        raise DocumentaryRequestBuilderError("corpora_preferiti must be a list.")
    if not isinstance(classified_case.get("zone_rosse"), list):
        raise DocumentaryRequestBuilderError("zone_rosse must be a list.")
    if not isinstance(classified_case.get("contesto_metodologico"), dict):
        raise DocumentaryRequestBuilderError("contesto_metodologico must be an object.")


def _normalize_tipologia_atto(classified_case: JsonDict) -> Any:
    natura_output = str(classified_case.get("natura_output") or "").upper()
    if natura_output != "ATTO":
        return None
    return classified_case.get("tipologia_atto")


def _build_documentary_payload(classified_case: JsonDict) -> JsonDict:
    payload = {
        "request_kind": REQUEST_KIND,
        "request_type": REQUEST_TYPE,
        "documentary_channel_policy": {
            "preferred_channel": "FEDERATED_ONLY",
            "allowed_channels": list(DEFAULT_ALLOWED_CHANNELS),
            "federated_is_not_official_source": True,
            "institutional_web_allowed_only_for": [
                "missing_norm_or_act_recovery",
                "official_uri_verification",
                "vigenza_verification",
                "rinvii_reconstruction",
                "coverage_completion",
                "official_source_confirmation",
            ],
        },
        "documentary_request": {
            "natura_output": classified_case["natura_output"],
            "tipologia_atto": _normalize_tipologia_atto(classified_case),
            "materia_prevalente": classified_case["materia_prevalente"],
            "sensibilita": classified_case["sensibilita"],
            "rischio_iniziale": classified_case["rischio_iniziale"],
            "intensita_applicativa": classified_case["intensita_applicativa"],
            "zone_rosse": deepcopy(classified_case["zone_rosse"]),
            "fast_track": bool(classified_case["fast_track"]),
            "moduli_attivati": deepcopy(classified_case["moduli_attivati"]),
            "esigenza_documentale": classified_case["esigenza_documentale"],
            "obiettivo_documentale": classified_case["obiettivo_documentale"],
            "query_guidata": classified_case["query_guidata"],
            "corpora_preferiti": deepcopy(classified_case["corpora_preferiti"]),
            "contesto_metodologico": deepcopy(classified_case["contesto_metodologico"]),
        },
        "documentary_scope": {
            "must_return_documentary_only": True,
            "level_b_is_non_decisional": True,
            "support_only": True,
            "propagate_critical_blocks": True,
            "allow_only_documentary_outputs": True,
            "official_source_required_for_opponibility": True,
        },
        "expected_documentary_outputs": [
            "documentary_packet",
            "citations",
            "vigenza_status",
            "rinvii_status",
            "coverage",
            "official_source_confirmation",
            "warnings",
            "errors",
            "blocks",
            "audit",
            "shadow",
        ],
        "audit_context": {
            "required": True,
            "shadow_required": True,
            "human_approval_required": True,
            "stage": "A1_TER_DOCUMENTARY_ORCHESTRATION",
        },
    }
    return payload


def validate_documentary_request_envelope(request_envelope: JsonDict) -> None:
    validator = Draft202012Validator(_load_schema())
    errors = sorted(validator.iter_errors(request_envelope), key=lambda error: error.path)
    if errors:
        raise DocumentaryRequestBuilderError(errors[0].message)


def build_documentary_request_envelope(
    classified_case: JsonDict,
    *,
    timestamp: str | None = None,
) -> JsonDict:
    _validate_minimum_input(classified_case)

    request_envelope = {
        "request_id": classified_case["request_id"],
        "case_id": classified_case["case_id"],
        "trace_id": classified_case["trace_id"],
        "api_version": API_VERSION,
        "caller_module": classified_case["caller_module"],
        "target_module": TARGET_MODULE,
        "timestamp": timestamp or _utc_now_iso(),
        "status": "READY_FOR_LEVEL_B",
        "warnings": [],
        "errors": [],
        "blocks": [],
        "payload": _build_documentary_payload(classified_case),
        "audit": {
            "trail_events": [
                {
                    "event": "A1_TER_DOCUMENTARY_REQUEST_BUILT",
                    "request_id": classified_case["request_id"],
                }
            ]
        },
        "shadow": {
            "fragments": [
                {
                    "trace_id": classified_case["trace_id"],
                    "kind": "a1_ter_documentary_request",
                    "documentary_only": True,
                }
            ]
        },
    }

    validate_documentary_request_envelope(request_envelope)
    return request_envelope
