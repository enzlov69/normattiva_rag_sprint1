from typing import Dict, Any, List


ALLOWED_NATURE = [
    "ANALISI ISTRUTTORIA",
    "PARERE",
    "ATTO NON OPPONIBILE",
    "ATTO OPPONIBILE",
    "COMUNICAZIONE ISTITUZIONALE",
]

ALLOWED_MATERIE = [
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
]


def run_fase0(payload: Dict[str, Any]) -> Dict[str, Any]:

    blocking_reasons: List[str] = []
    warnings: List[str] = []

    natura = payload.get("natura_output")
    tipo_atto = payload.get("tipologia_atto")
    materia = payload.get("materia_prevalente")
    sensibilita = payload.get("sensibilita", {})
    zone_rosse = payload.get("zone_rosse", [])

    fast_track_requested = payload.get("fast_track_requested", False)
    urgenza_motivata = payload.get("urgenza_motivata", False)

    debito = payload.get("debito_fuori_bilancio", False)
    impatto_economico = payload.get("impatto_economico_significativo", False)
    contenzioso = payload.get("profilo_contenzioso_potenziale", False)

    # -------------------------
    # VALIDAZIONI BLOCCANTI
    # -------------------------

    if natura not in ALLOWED_NATURE:
        blocking_reasons.append("Natura output non classificabile")

    if materia not in ALLOWED_MATERIE:
        blocking_reasons.append("Materia prevalente non valida o assente")

    if natura in ["ATTO OPPONIBILE", "ATTO NON OPPONIBILE"]:
        if not tipo_atto:
            blocking_reasons.append("Tipologia atto obbligatoria per ATTO")
    else:
        if tipo_atto:
            blocking_reasons.append("Tipologia atto non ammessa per natura_output non ATTO")

    if fast_track_requested and not urgenza_motivata:
        blocking_reasons.append("FAST-TRACK richiesto senza urgenza motivata")

    # -------------------------
    # RISCHIO
    # -------------------------

    rischio = "BASSO"

    condizioni_alto = [
        bool(zone_rosse),
        sensibilita.get("pnrr_vincoli") == "SI",
        tipo_atto == "Regolamento",
        debito,
        impatto_economico,
        contenzioso,
    ]

    if any(condizioni_alto):
        rischio = "ALTO"
    else:
        condizioni_medio = [
            sensibilita.get("benefici_economici") == "SI",
            sensibilita.get("impatto_esterno") == "SI",
            sensibilita.get("dati_personali") == "SI",
        ]
        if any(condizioni_medio):
            rischio = "MEDIO"

    # -------------------------
    # INTENSITÀ
    # -------------------------

    intensita_map = {
        "BASSO": "ESSENZIALE",
        "MEDIO": "STANDARD",
        "ALTO": "RAFFORZATA",
    }

    intensita = intensita_map[rischio]

    # -------------------------
    # MODULI ATTIVATI (base)
    # -------------------------

    moduli = ["FASE_0", "FASE_0_BIS"]

    if rischio == "ALTO":
        moduli.append("CRITIC_v4")

    if zona_rosse := bool(zone_rosse):
        moduli.append("M02_M03_ZONE_ROSSE")

    # -------------------------
    # ESITO
    # -------------------------

    status = "BLOCKED" if blocking_reasons else "OK"

    return {
        "phase_id": "FASE_0",
        "phase_name": "Classificazione Automatica dell’Output",
        "method_version": payload.get("method_version"),
        "session_id": payload.get("session_id"),
        "status": status,
        "gate_outcome": "BLOCCO" if blocking_reasons else "OK",
        "natura_output": natura,
        "tipologia_atto": tipo_atto,
        "materia_prevalente": materia,
        "sensibilita": sensibilita,
        "zone_rosse": zone_rosse,
        "rischio_iniziale": rischio,
        "intensita_applicativa": intensita,
        "fast_track": "SI" if fast_track_requested else "NO",
        "moduli_attivati": moduli,
        "next_phase": "FASE_0_BIS" if status == "OK" else None,
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
        "trace": {
            "validation_layer": "ROOT_RUNTIME",
            "risk_evaluation": condizioni_alto,
        },
    }