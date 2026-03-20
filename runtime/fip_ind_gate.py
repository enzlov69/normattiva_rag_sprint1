from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry


CANONICAL_QUESTIONS = {
    "Q01": "L'atto produce effetti diretti su terzi?",
    "Q02": "L'atto individua beneficiari o destinatari nominativi?",
    "Q03": "L'atto dispone o presuppone impegni di spesa, liquidazioni o pagamenti?",
    "Q04": "L'atto conclude un procedimento amministrativo o decide su istanze?",
    "Q05": "L'atto contiene prescrizioni operative esecutive puntuali per gli uffici?",
    "Q06": "L'atto affida, incarica o individua operatori economici/soggetti attuatori?",
    "Q07": "L'atto incide concretamente su posizioni giuridiche individuali?",
    "Q08": "L'atto dispone allocazioni di risorse o utilità con effetti immediati?",
    "Q09": "L'atto contiene un dispositivo amministrativo autoesecutivo?",
    "Q10": "L'atto presenta contenuti tipici di provvedimento gestionale più che di indirizzo?",
}

FORBIDDEN_LEVEL_B_KEYS = {
    "final_act_qualification",
    "gate_result",
    "output_authorized",
    "go_finale",
}


class FIPINDGateError(Exception):
    """Base exception for the FIP-IND gate."""


class FIPINDQuestionnaireValidationError(FIPINDGateError):
    """Raised when the questionnaire is invalid."""


class FIPINDDocumentarySupportValidationError(FIPINDGateError):
    """Raised when Level B documentary support is invalid."""


class FIPINDBoundaryViolationError(FIPINDGateError):
    """Raised when Level B attempts a conclusive semantic."""


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _schemas_dir() -> Path:
    return _project_root() / "schemas"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_bundle() -> dict[str, dict[str, Any]]:
    names = [
        "fip_ind_questionnaire_schema_v1.json",
        "fip_ind_gate_result_schema_v1.json",
        "fip_ind_documentary_support_request_schema_v1.json",
        "fip_ind_documentary_support_response_schema_v1.json",
        "fip_ind_evidence_pack_schema_v1.json",
    ]
    schemas_dir = _schemas_dir()
    return {name: _load_json(schemas_dir / name) for name in names}


def _build_registry() -> Registry[Any]:
    schemas = _schema_bundle()
    schemas_dir = _schemas_dir()
    pairs: list[tuple[str, Any]] = []

    for name, loaded_schema in schemas.items():
        path = (schemas_dir / name).resolve()
        pairs.append((path.as_uri(), loaded_schema))
        schema_id = loaded_schema.get("$id")
        if isinstance(schema_id, str) and schema_id:
            pairs.append((schema_id, loaded_schema))

    return Registry().with_contents(pairs)


def _validator(schema_name: str) -> Draft202012Validator:
    schemas = _schema_bundle()
    if schema_name not in schemas:
        raise FIPINDGateError(f"Schema non trovato: {schema_name}")
    return Draft202012Validator(schemas[schema_name], registry=_build_registry())


def build_question(
    question_id: str,
    answer: str,
    brief_reason: str = "",
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    if question_id not in CANONICAL_QUESTIONS:
        raise FIPINDGateError(f"question_id non riconosciuto: {question_id}")

    return {
        "question_id": question_id,
        "question_text": CANONICAL_QUESTIONS[question_id],
        "answer": answer,
        "brief_reason": brief_reason,
        "evidence_refs": evidence_refs or [],
    }


def validate_questionnaire(questionnaire: dict[str, Any]) -> None:
    try:
        _validator("fip_ind_questionnaire_schema_v1.json").validate(questionnaire)
    except ValidationError as exc:
        raise FIPINDQuestionnaireValidationError(str(exc)) from exc


def _scan_for_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []

    if isinstance(value, dict):
        for key, nested in value.items():
            current = f"{path}.{key}"
            if key in FORBIDDEN_LEVEL_B_KEYS:
                found.append(current)
            found.extend(_scan_for_forbidden_keys(nested, current))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            found.extend(_scan_for_forbidden_keys(item, f"{path}[{idx}]"))

    return found


def validate_documentary_support_response(response_payload: dict[str, Any]) -> None:
    forbidden = _scan_for_forbidden_keys(response_payload)
    if forbidden:
        raise FIPINDBoundaryViolationError(
            "Campi vietati rilevati nella response del Livello B: " + ", ".join(forbidden)
        )

    documentary_packet = response_payload.get("payload", {}).get("documentary_packet", {})
    if documentary_packet.get("support_only_flag") is not True:
        raise FIPINDBoundaryViolationError(
            "Il documentary packet del Livello B deve avere support_only_flag = true."
        )

    evidence_pack = documentary_packet.get("fip_ind_evidence_pack")
    if evidence_pack is not None:
        if evidence_pack.get("human_gate_required") is not True:
            raise FIPINDBoundaryViolationError(
                "FIPIndEvidencePack deve imporre human_gate_required = true."
            )
        if evidence_pack.get("source_layer") != "B":
            raise FIPINDBoundaryViolationError(
                "FIPIndEvidencePack deve dichiarare source_layer = 'B'."
            )

    try:
        _validator("fip_ind_documentary_support_response_schema_v1.json").validate(response_payload)
    except ValidationError as exc:
        raise FIPINDDocumentarySupportValidationError(str(exc)) from exc


def evaluate_gate(questionnaire: dict[str, Any]) -> dict[str, Any]:
    validate_questionnaire(questionnaire)

    answers = [q["answer"] for q in questionnaire["questions"]]
    total_yes = sum(1 for answer in answers if answer == "YES")
    total_no = sum(1 for answer in answers if answer == "NO")
    total_unknown = sum(1 for answer in answers if answer == "UNKNOWN")

    if total_yes >= 5:
        gate_result = "FALSO_INDIRIZZO_BLOCKED"
        blocked = True
        requalification_required = True
        block_code = "FIP_IND_THRESHOLD_BLOCK"
        notes = "Soglia >= 5 YES: falso indirizzo, blocco del flusso come atto di indirizzo."
    elif total_yes >= 3:
        gate_result = "PROVVEDIMENTO_SOSTANZIALE"
        blocked = False
        requalification_required = True
        block_code = None
        notes = "Soglia 3-4 YES: l'atto va trattato come provvedimento sostanziale."
    elif total_yes >= 1 or total_unknown >= 1:
        gate_result = "RISCHIO_FIP_IND"
        blocked = False
        requalification_required = False
        block_code = None
        notes = "Presenza di 1-2 YES o UNKNOWN: rischio FIP-IND, necessario approfondimento del Livello A."
    else:
        gate_result = "INDIRIZZO_PURO"
        blocked = False
        requalification_required = False
        block_code = None
        notes = "0 YES e 0 UNKNOWN: indirizzo puro."

    result: dict[str, Any] = {
        "case_id": questionnaire["case_id"],
        "trace_id": questionnaire["trace_id"],
        "total_yes": total_yes,
        "total_no": total_no,
        "total_unknown": total_unknown,
        "gate_result": gate_result,
        "blocked": blocked,
        "requalification_required": requalification_required,
        "human_review_required": True,
        "notes": notes,
        "answered_questions": [q["question_id"] for q in questionnaire["questions"]],
    }

    if block_code:
        result["triggered_block_code"] = block_code

    try:
        _validator("fip_ind_gate_result_schema_v1.json").validate(result)
    except ValidationError as exc:
        raise FIPINDGateError(str(exc)) from exc

    return result