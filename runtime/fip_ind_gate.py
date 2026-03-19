from __future__ import annotations

from typing import Any, Dict, List


PHASE_ID = "FIP_IND"
PHASE_NAME = "Filtro_Indirizzo_vs_Provvedimento"
METHOD_VERSION = "PPAV_2_2"

KEYWORDS_PROVVEDIMENTO = [
    "affida",
    "impegna",
    "liquida",
    "dispone",
    "concede",
    "approva schema di contratto",
    "aggiudica",
    "affidamento",
]

KEYWORDS_INDIRIZZO = [
    "indirizza",
    "fornisce indirizzi",
    "fornisce indirizzo",
    "definisce linee",
    "definiscono indirizzi",
    "definisce indirizzi",
    "stabilisce obiettivi",
    "stabilisce obiettivi",
    "linee di indirizzo",
    "indirizzi",
]


def _validate_payload(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    if "natura_output" not in payload:
        errors.append("Missing natura_output")

    if "testo" not in payload:
        errors.append("Missing testo")

    natura_output = payload.get("natura_output")
    if natura_output is not None and natura_output not in {"INDIRIZZO", "ATTO"}:
        errors.append("Invalid natura_output")

    testo = payload.get("testo")
    if testo is not None and not isinstance(testo, str):
        errors.append("Field testo must be a string")

    return errors


def _contains_keywords(text: str, keywords: List[str]) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)


def run_fip_ind(payload: Dict[str, Any]) -> Dict[str, Any]:
    errors = _validate_payload(payload)

    if errors:
        return {
            "phase_id": PHASE_ID,
            "phase_name": PHASE_NAME,
            "status": "BLOCKED",
            "qualificazione": {
                "indirizzo": False,
                "provvedimento": False,
            },
            "warning": [],
            "blocking_reasons": errors,
            "next_phase": "NONE",
        }

    natura_output = payload.get("natura_output")
    testo = payload.get("testo", "")

    has_provvedimento = _contains_keywords(testo, KEYWORDS_PROVVEDIMENTO)
    has_indirizzo = _contains_keywords(testo, KEYWORDS_INDIRIZZO)

    blocking_reasons: List[str] = []
    warning: List[str] = []

    # Caso critico: falso indirizzo
    if natura_output == "INDIRIZZO" and has_provvedimento:
        blocking_reasons.append("Falso indirizzo: contiene effetti gestionali")

    # Caso ibrido: contenuto misto
    if has_provvedimento and has_indirizzo:
        warning.append("Contenuto misto indirizzo/provvedimento")

    status = "BLOCKED" if blocking_reasons else "OK"
    next_phase = "M07_LPR" if status == "OK" else "NONE"

    return {
        "phase_id": PHASE_ID,
        "phase_name": PHASE_NAME,
        "status": status,
        "qualificazione": {
            "indirizzo": has_indirizzo,
            "provvedimento": has_provvedimento,
        },
        "warning": warning,
        "blocking_reasons": blocking_reasons,
        "next_phase": next_phase,
    }