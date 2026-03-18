"""Helper offline per la suite Golden Baseline del Livello B.

Questo modulo:
- non introduce logica runtime;
- non introduce logica decisoria;
- non modifica i validator esistenti;
- centralizza solo utility di test per evitare duplicazioni sporche.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

FORBIDDEN_FIELDS = {
    "final_decision",
    "final_applicability",
    "legal_conclusion",
    "motivazione_finale",
    "output_authorized",
    "m07_closed",
    "ppav_closed",
    "go_finale",
}

FORBIDDEN_PHRASES = (
    "si autorizza",
    "autorizzato",
    "caso risolto",
    "si conclude che",
    "conclusione finale",
    "atto autorizzato",
    "m07 completato",
    "m07 chiuso",
)

STATUS_FAMILIES = {
    "SUCCESS": "pass",
    "DEGRADED": "degrade",
    "BLOCKED": "reject",
    "REJECTED": "reject",
}


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_result_object(result: Any) -> Dict[str, Any]:
    if result is None:
        return {}
    if isinstance(result, dict):
        return result
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    if hasattr(result, "__dict__"):
        return dict(result.__dict__)
    raise TypeError(f"Unsupported validator result type: {type(result)!r}")


def resolve_validator_callable() -> Optional[Any]:
    try:
        module = importlib.import_module("validators.level_b_payload_validator")
    except ModuleNotFoundError:
        return None
    candidates = (
        "validate_level_b_payload",
        "validate_payload",
        "validate_level_b_response",
        "validate_response",
        "validate",
    )
    for name in candidates:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    klass = getattr(module, "LevelBPayloadValidator", None)
    if klass is not None:
        instance = klass()
        for name in candidates:
            fn = getattr(instance, name, None)
            if callable(fn):
                return fn
    return None


def run_existing_validator(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    validator = resolve_validator_callable()
    if validator is None:
        return None
    for kwargs in ({}, {"strict": True}):
        try:
            result = validator(payload, **kwargs)
            return normalize_result_object(result)
        except TypeError:
            continue
    result = validator(payload)
    return normalize_result_object(result)


def walk_json(node: Any, path: str = "") -> Iterable[Tuple[str, Any]]:
    if isinstance(node, dict):
        for key, value in node.items():
            next_path = f"{path}.{key}" if path else key
            yield next_path, value
            yield from walk_json(value, next_path)
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            next_path = f"{path}[{idx}]"
            yield next_path, value
            yield from walk_json(value, next_path)


def find_forbidden_fields(payload: Dict[str, Any]) -> List[str]:
    hits: List[str] = []
    for path, value in walk_json(payload):
        if path.split(".")[-1] in FORBIDDEN_FIELDS:
            hits.append(path)
        if isinstance(value, dict):
            for key in value.keys():
                if key in FORBIDDEN_FIELDS:
                    hits.append(f"{path}.{key}" if path else key)
    return sorted(set(hits))


def collect_text_fragments(payload: Dict[str, Any]) -> List[str]:
    texts: List[str] = []
    for _, value in walk_json(payload):
        if isinstance(value, str):
            texts.append(value.lower())
    return texts


def has_conclusive_semantics(payload: Dict[str, Any]) -> bool:
    texts = collect_text_fragments(payload)
    return any(phrase in text for phrase in FORBIDDEN_PHRASES for text in texts)


def get_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    value = payload.get("payload")
    return value if isinstance(value, dict) else {}


def collect_valid_citations(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = get_payload(payload)
    citations = data.get("citations_valid") or []
    return [c for c in citations if isinstance(c, dict)]


def valid_citations_without_uri(payload: Dict[str, Any]) -> List[str]:
    bad: List[str] = []
    for citation in collect_valid_citations(payload):
        status = str(citation.get("citation_status", "")).upper()
        uri = citation.get("uri_ufficiale")
        cid = citation.get("citation_id", "<missing>")
        if status == "VALID" and (uri is None or str(uri).strip() == ""):
            bad.append(str(cid))
    return bad


def m07_support_requires_human_completion(payload: Dict[str, Any]) -> bool:
    m07_support = get_payload(payload).get("m07_support")
    if not isinstance(m07_support, dict):
        return True
    return m07_support.get("human_completion_required") is True


def audit_present(payload: Dict[str, Any]) -> bool:
    audit = get_payload(payload).get("audit_trail")
    if not isinstance(audit, dict):
        return False
    return audit.get("present") is True and bool(audit.get("event_ids"))


def shadow_present(payload: Dict[str, Any]) -> bool:
    shadow = get_payload(payload).get("shadow")
    if not isinstance(shadow, dict):
        return False
    return shadow.get("present") is True and bool(shadow.get("executed_modules"))


def collect_codes(items: Any, key_names: Tuple[str, ...]) -> List[str]:
    codes: List[str] = []
    if not isinstance(items, list):
        return codes
    for item in items:
        if isinstance(item, str):
            codes.append(item)
        elif isinstance(item, dict):
            for key in key_names:
                value = item.get(key)
                if value:
                    codes.append(str(value))
                    break
    return codes


def collect_block_codes(payload: Dict[str, Any]) -> List[str]:
    return collect_codes(payload.get("blocks"), ("block_code", "code"))


def collect_error_codes(payload: Dict[str, Any]) -> List[str]:
    return collect_codes(payload.get("errors"), ("error_code", "code"))


def collect_warning_codes(payload: Dict[str, Any]) -> List[str]:
    return collect_codes(payload.get("warnings"), ("warning_code", "code"))


def status_matches_family(status: str, family: str) -> bool:
    return STATUS_FAMILIES.get(status) == family


def assert_basic_status_coherence(payload: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    status = str(payload.get("status", "")).upper()
    warnings = collect_warning_codes(payload)
    errors = collect_error_codes(payload)
    blocks = collect_block_codes(payload)

    if status == "SUCCESS":
        if warnings or errors or blocks:
            problems.append("SUCCESS must not contain warnings, errors or blocks")
    elif status == "DEGRADED":
        if errors:
            problems.append("DEGRADED should not contain hard errors")
    elif status == "BLOCKED":
        if not blocks:
            problems.append("BLOCKED must expose at least one block code")
    elif status == "REJECTED":
        if not errors and not blocks:
            problems.append("REJECTED must expose at least one error or block")
    else:
        problems.append(f"Unexpected status: {status}")

    return problems
