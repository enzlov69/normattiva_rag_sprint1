from __future__ import annotations

from typing import Any, Dict, List


FASE_0_TER_PHASE_ID = "FASE_0_TER"
FASE_0_TER_PHASE_NAME = "Inquadramento_Normativo_Settoriale"
FASE_0_TER_METHOD_VERSION = "PPAV_2_2"

ALLOWED_MATERIE = {
    "CONTABILE_BILANCIO",
    "CONTRATTI_AFFIDAMENTI",
    "PERSONALE_ORGANIZZAZIONE",
    "SERVIZI_ALLA_PERSONA",
    "DEMOGRAFICI",
    "CULTURA_EVENTI",
    "TURISMO_SPORT",
    "INNOVAZIONE_ICT",
    "TRIBUTI",
    "PATRIMONIO",
    "ALTRO",
}

BASE_MAPPING = {
    "CONTABILE_BILANCIO": {
        "normativa_attivata": [
            "D.Lgs. 267/2000 (TUEL)",
            "D.Lgs. 118/2011",
        ],
        "regolamenti_rilevanti": [
            "Regolamento di contabilità",
        ],
        "vincoli_attivati": [
            "vincoli_contabili",
            "equilibri_bilancio",
            "copertura_finanziaria",
        ],
        "obblighi_operativi": [
            "verifica_copertura_finanziaria",
            "verifica_competenza_esigibilita",
        ],
    },
    "CONTRATTI_AFFIDAMENTI": {
        "normativa_attivata": [
            "D.Lgs. 267/2000 (TUEL)",
            "D.Lgs. 36/2023",
            "L. 241/1990",
        ],
        "regolamenti_rilevanti": [
            "Regolamento comunale per affidamenti/contratti",
        ],
        "vincoli_attivati": [
            "vincoli_contrattuali",
            "obblighi_tracciabilita",
            "principi_risultato_fiducia_accesso",
        ],
        "obblighi_operativi": [
            "verifica_procedura_affidamento",
            "verifica_cig_se_dovuto",
            "verifica_documentazione_operatore",
        ],
    },
    "PERSONALE_ORGANIZZAZIONE": {
        "normativa_attivata": [
            "D.Lgs. 267/2000 (TUEL)",
            "D.Lgs. 165/2001",
            "D.Lgs. 150/2009",
            "L. 241/1990",
        ],
        "regolamenti_rilevanti": [
            "Regolamento uffici e servizi",
            "Regolamento personale / EQ",
        ],
        "vincoli_attivati": [
            "vincoli_ordinamentali_personale",
            "coerenza_organizzativa",
        ],
        "obblighi_operativi": [
            "verifica_competenza_organo",
            "verifica_coerenza_assetto_organizzativo",
        ],
    },
    "SERVIZI_ALLA_PERSONA": {
        "normativa_attivata": [
            "D.Lgs. 267/2000 (TUEL)",
            "L. 241/1990",
        ],
        "regolamenti_rilevanti": [
            "Regolamento servizi sociali / interventi alla persona",
        ],
        "vincoli_attivati": [
            "vincoli_procedimentali",
            "vincoli_settoriali_servizi_persona",
        ],
        "obblighi_operativi": [
            "verifica_requisiti_accesso_beneficio_servizio",
            "verifica_istruttoria_sociale_se_necessaria",
        ],
    },
    "DEMOGRAFICI": {
        "normativa_attivata": [
            "D.Lgs. 267/2000 (TUEL)",
            "D.P.R. 223/1989",
            "L. 241/1990",
        ],
        "regolamenti_rilevanti": [
            "Regolamento servizi demografici",
        ],
        "vincoli_attivati": [
            "vincoli_anagrafici",
            "vincoli_procedimentali",
        ],
        "obblighi_operativi": [
            "verifica_presupposti_anagrafici",
            "verifica_titolo_legittimante",
        ],
    },
    "CULTURA_EVENTI": {
        "normativa_attivata": [
            "D.Lgs. 267/2000 (TUEL)",
            "L. 241/1990",
        ],
        "regolamenti_rilevanti": [
            "Regolamento contributi/patrocini",
            "Regolamento manifestazioni/eventi",
        ],
        "vincoli_attivati": [
            "vincoli_procedimentali",
            "vincoli_eventuali_autorizzazioni_evento",
        ],
        "obblighi_operativi": [
            "verifica_titolo_evento_o_beneficio",
            "verifica_eventuali_autorizzazioni_collaudate",
        ],
    },
    "TURISMO_SPORT": {
        "normativa_attivata": [
            "D.Lgs. 267/2000 (TUEL)",
            "L. 241/1990",
        ],
        "regolamenti_rilevanti": [
            "Regolamento impianti sportivi",
            "Regolamento iniziative turistiche/sportive",
        ],
        "vincoli_attivati": [
            "vincoli_settoriali_sport_turismo",
            "vincoli_procedimentali",
        ],
        "obblighi_operativi": [
            "verifica_titolo_utilizzo_impianto_o_iniziativa",
            "verifica_presupposti_settoriali",
        ],
    },
    "INNOVAZIONE_ICT": {
        "normativa_attivata": [
            "D.Lgs. 267/2000 (TUEL)",
            "D.Lgs. 82/2005 (CAD)",
        ],
        "regolamenti_rilevanti": [
            "Regolamento utilizzo sistemi informativi / sicurezza ICT",
        ],
        "vincoli_attivati": [
            "vincoli_digitali",
            "vincoli_organizzativi_ict",
        ],
        "obblighi_operativi": [
            "verifica_coerenza_cad",
            "verifica_presidi_digitali_minimi",
        ],
    },
    "TRIBUTI": {
        "normativa_attivata": [
            "D.Lgs. 267/2000 (TUEL)",
            "L. 241/1990",
        ],
        "regolamenti_rilevanti": [
            "Regolamento entrate / tributi comunali",
        ],
        "vincoli_attivati": [
            "vincoli_tributari",
            "vincoli_procedimentali",
        ],
        "obblighi_operativi": [
            "verifica_base_regolamentare_tributaria",
            "verifica_presupposto_impositivo_o_agevolativo",
        ],
    },
    "PATRIMONIO": {
        "normativa_attivata": [
            "D.Lgs. 267/2000 (TUEL)",
            "L. 241/1990",
        ],
        "regolamenti_rilevanti": [
            "Regolamento patrimonio / beni comunali",
        ],
        "vincoli_attivati": [
            "vincoli_patrimoniali",
            "vincoli_procedimentali",
        ],
        "obblighi_operativi": [
            "verifica_titolo_disponibilita_bene",
            "verifica_competenza_e_regime_del_bene",
        ],
    },
    "ALTRO": {
        "normativa_attivata": [
            "D.Lgs. 267/2000 (TUEL)",
        ],
        "regolamenti_rilevanti": [],
        "vincoli_attivati": [
            "inquadramento_settoriale_da_completare",
        ],
        "obblighi_operativi": [
            "completare_mappatura_normativa_settoriale",
        ],
    },
}


def _safe_bool(value: Any) -> bool:
    return bool(value)


def _validate_payload(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    required_fields = [
        "session_id",
        "method_version",
        "materia_prevalente",
        "rischio_iniziale",
    ]

    for field in required_fields:
        if field not in payload:
            errors.append(f"Missing required field: {field}")

    materia = payload.get("materia_prevalente")
    if materia is not None and materia not in ALLOWED_MATERIE:
        errors.append("Materia prevalente non mappata")

    if "zone_rosse" in payload and not isinstance(payload["zone_rosse"], list):
        errors.append("Field zone_rosse must be an array")

    return errors


def run_fase0ter(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    FASE 0-ter – Inquadramento normativo settoriale

    Gate di attivazione normativa settoriale e regolamentare.
    Non interpreta nel merito e non attiva moduli PPAV.
    """

    validation_errors = _validate_payload(payload)
    if validation_errors:
        return {
            "phase_id": FASE_0_TER_PHASE_ID,
            "phase_name": FASE_0_TER_PHASE_NAME,
            "method_version": str(payload.get("method_version", "UNKNOWN")),
            "session_id": str(payload.get("session_id", "UNKNOWN")),
            "status": "BLOCKED",
            "normativa_attivata": [],
            "regolamenti_rilevanti": [],
            "vincoli_attivati": [],
            "obblighi_operativi": [],
            "warning": [],
            "blocking_reasons": validation_errors,
            "next_phase": "NONE",
            "trace": {
                "mapping_normativo": "FAILED",
                "coerenza_verificata": False,
                "note": "Input validation failed",
            },
        }

    session_id = str(payload["session_id"])
    method_version = str(payload["method_version"])
    materia = str(payload["materia_prevalente"])
    natura_output = payload.get("natura_output")
    tipologia_atto = payload.get("tipologia_atto")
    sensibilita = payload.get("sensibilita", {})
    rischio_iniziale = str(payload["rischio_iniziale"])
    fast_track = _safe_bool(payload.get("fast_track", False))
    zone_rosse = payload.get("zone_rosse", [])

    mapping = BASE_MAPPING.get(materia)
    if not mapping:
        return {
            "phase_id": FASE_0_TER_PHASE_ID,
            "phase_name": FASE_0_TER_PHASE_NAME,
            "method_version": method_version,
            "session_id": session_id,
            "status": "BLOCKED",
            "normativa_attivata": [],
            "regolamenti_rilevanti": [],
            "vincoli_attivati": [],
            "obblighi_operativi": [],
            "warning": [],
            "blocking_reasons": ["Normativa settoriale non individuabile"],
            "next_phase": "NONE",
            "trace": {
                "mapping_normativo": "NOT_FOUND",
                "coerenza_verificata": False,
                "note": "Missing sectoral mapping",
            },
        }

    normativa_attivata = list(mapping["normativa_attivata"])
    regolamenti_rilevanti = list(mapping["regolamenti_rilevanti"])
    vincoli_attivati = list(mapping["vincoli_attivati"])
    obblighi_operativi = list(mapping["obblighi_operativi"])

    warnings: List[str] = []
    blocking_reasons: List[str] = []

    # Attivazioni coerenti ma non automatiche di compliance/documentazione
    if _safe_bool(sensibilita.get("dati_personali", False)):
        normativa_attivata.append("Regolamento (UE) 2016/679 (GDPR)")
        vincoli_attivati.append("vincoli_privacy")

    if _safe_bool(sensibilita.get("benefici_economici", False)):
        normativa_attivata.append("D.Lgs. 33/2013")
        vincoli_attivati.append("obblighi_trasparenza")

    if _safe_bool(sensibilita.get("pnrr_o_finanziamenti_vincolati", False)):
        vincoli_attivati.append("vincoli_finanziamento_vincolato")
        warnings.append("Presenza di PNRR_o_finanziamenti_vincolati: approfondire quadro speciale di finanziamento")

    if _safe_bool(sensibilita.get("impatto_esterno_rilevante", False)):
        vincoli_attivati.append("attenzione_impatto_esterno")

    if natura_output in {"ATTO OPPONIBILE", "ATTO NON OPPONIBILE"}:
        vincoli_attivati.append("coerenza_forma_atto")

    if tipologia_atto == "Regolamento":
        obblighi_operativi.append("verifica_iter_approvazione_regolamento")
        vincoli_attivati.append("vincoli_regolamentari")

    if fast_track:
        warnings.append("FAST_TRACK: il gate è tracciato ma può essere recuperato ex post nel rientro PPAV")

    if materia == "ALTRO":
        warnings.append("Materia ALTRO: mappatura settoriale da affinare")

    if materia == "CONTABILE_BILANCIO" and "vincoli_contabili" not in vincoli_attivati:
        blocking_reasons.append("Vincoli contabili non correttamente attivati")

    if materia == "CONTRATTI_AFFIDAMENTI" and "vincoli_contrattuali" not in vincoli_attivati:
        blocking_reasons.append("Vincoli contrattuali non correttamente attivati")

    if materia != "ALTRO" and not regolamenti_rilevanti:
        blocking_reasons.append("Assenza di regolamento comunale rilevante per materia")

    # Deduplica mantenendo ordine
    def dedupe(seq: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for item in seq:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out

    normativa_attivata = dedupe(normativa_attivata)
    regolamenti_rilevanti = dedupe(regolamenti_rilevanti)
    vincoli_attivati = dedupe(vincoli_attivati)
    obblighi_operativi = dedupe(obblighi_operativi)
    warnings = dedupe(warnings)
    blocking_reasons = dedupe(blocking_reasons)

    status = "BLOCKED" if blocking_reasons else "OK"
    next_phase = "FIP_IND" if status == "OK" and not fast_track else ("NONE" if status == "BLOCKED" else "M07_LPR_FAST_TRACK")

    return {
        "phase_id": FASE_0_TER_PHASE_ID,
        "phase_name": FASE_0_TER_PHASE_NAME,
        "method_version": method_version,
        "session_id": session_id,
        "status": status,
        "normativa_attivata": normativa_attivata,
        "regolamenti_rilevanti": regolamenti_rilevanti,
        "vincoli_attivati": vincoli_attivati,
        "obblighi_operativi": obblighi_operativi,
        "warning": warnings,
        "blocking_reasons": blocking_reasons,
        "next_phase": next_phase,
        "trace": {
            "mapping_normativo": materia,
            "coerenza_verificata": status == "OK",
            "note": f"Rischio iniziale: {rischio_iniziale}; zone_rosse={len(zone_rosse)}",
        },
    }