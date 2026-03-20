from __future__ import annotations

from typing import Any, Dict, List


PHASE_ID = "RAC"
PHASE_NAME = "Report_Applicativo_Comunale"
METHOD_VERSION = "PPAV_2_2"


def _validate_payload(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    required = [
        "session_id",
        "method_version",
        "norma",
        "articoli_rilevanti"
    ]

    for field in required:
        if field not in payload:
            errors.append(f"Missing required field: {field}")

    if not isinstance(payload.get("articoli_rilevanti", []), list):
        errors.append("articoli_rilevanti must be a list")

    return errors


def run_rac(payload: Dict[str, Any]) -> Dict[str, Any]:

    errors = _validate_payload(payload)

    if errors:
        return {
            "phase_id": PHASE_ID,
            "phase_name": PHASE_NAME,
            "method_version": payload.get("method_version", "UNKNOWN"),
            "session_id": payload.get("session_id", "UNKNOWN"),
            "status": "BLOCKED",
            "output": {},
            "blocking_reasons": errors,
            "next_phase": "NONE"
        }

    norma = payload.get("norma", "")
    articoli = payload.get("articoli_rilevanti", [])
    rischio_input = payload.get("rischio_interpretativo_m07", "BASSO")

    blocking_reasons: List[str] = []

    # Verifiche minime obbligatorie RAC
    if not norma:
        blocking_reasons.append("Norma non indicata")

    if not articoli:
        blocking_reasons.append("Articoli rilevanti non individuati")

    # Simulazione struttura RAC (placeholder, evolveremo)
    competenza = "VERIFICATA"
    applicabilita = "DIRETTA"

    atti = ["Determina dirigenziale"]
    uffici = ["IV Settore"]
    vincoli = []
    prove = []

    adempimenti = {
        "amministrativi": ["istruttoria"],
        "contabili": [],
        "procedurali": [],
        "temporali": [],
        "trasparenza": []
    }

    # BLOCCO strutturale
    if blocking_reasons:
        return {
            "phase_id": PHASE_ID,
            "phase_name": PHASE_NAME,
            "method_version": payload.get("method_version"),
            "session_id": payload.get("session_id"),
            "status": "BLOCKED",
            "output": {},
            "blocking_reasons": blocking_reasons,
            "next_phase": "NONE"
        }

    return {
        "phase_id": PHASE_ID,
        "phase_name": PHASE_NAME,
        "method_version": payload.get("method_version"),
        "session_id": payload.get("session_id"),
        "status": "OK",
        "output": {
            "competenza_comunale": competenza,
            "applicabilita": applicabilita,
            "atti_da_adottare": atti,
            "adempimenti": adempimenti,
            "uffici_coinvolti": uffici,
            "vincoli": vincoli,
            "prove_documentali_richieste": prove,
            "rischio_interpretativo": rischio_input,
            "esito_rac": "OK"
        },
        "blocking_reasons": [],
        "next_phase": "M07_LPR",
        "note": [
            "Il RAC è opponibile come istruttoria",
            "Il RAC non è l'atto",
            "Non abilita firma diretta"
        ]
    }