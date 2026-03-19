from __future__ import annotations

from typing import Any, Dict, List


FASE_0_BIS_PHASE_ID = "FASE_0_BIS"
FASE_0_BIS_PHASE_NAME = "Presidi_Trasversali_di_Compliance"
FASE_0_BIS_METHOD_VERSION = "PPAV_2_2_ALIGNED_2_3"

PRESIDI_KEYS = [
    "anticorruzione",
    "trasparenza",
    "privacy",
    "performance_piao",
    "sicurezza_lavoro",
    "codice_comportamento",
]


def _safe_bool(value: Any) -> bool:
    return bool(value)


def _make_presidio(status: str, reason: str) -> Dict[str, str]:
    return {
        "status": status,
        "reason": reason,
    }


def _extract_input_from_phase0(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "natura_output": payload.get("natura_output"),
        "tipologia_atto": payload.get("tipologia_atto"),
        "materia_prevalente": payload.get("materia_prevalente"),
        "sensibilita": {
            "dati_personali": _safe_bool(payload.get("sensibilita", {}).get("dati_personali", False)),
            "benefici_economici": _safe_bool(payload.get("sensibilita", {}).get("benefici_economici", False)),
            "pnrr_o_finanziamenti_vincolati": _safe_bool(
                payload.get("sensibilita", {}).get("pnrr_o_finanziamenti_vincolati", False)
            ),
            "impatto_esterno_rilevante": _safe_bool(
                payload.get("sensibilita", {}).get("impatto_esterno_rilevante", False)
            ),
        },
        "rischio_iniziale": payload.get("rischio_iniziale"),
        "intensita_applicativa": payload.get("intensita_applicativa"),
        "fast_track": _safe_bool(payload.get("fast_track", False)),
        "zone_rosse": payload.get("zone_rosse", []),
    }


def _validate_required_payload(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    required_fields = [
        "session_id",
        "method_version",
        "materia_prevalente",
        "sensibilita",
        "rischio_iniziale",
        "intensita_applicativa",
    ]

    for field in required_fields:
        if field not in payload:
            errors.append(f"Missing required field: {field}")

    if "sensibilita" in payload and not isinstance(payload["sensibilita"], dict):
        errors.append("Field sensibilita must be an object")

    if "zone_rosse" in payload and not isinstance(payload["zone_rosse"], list):
        errors.append("Field zone_rosse must be an array")

    return errors


def run_fase0bis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    FASE 0-bis – Presidi Trasversali di Compliance

    Gate ex ante di compliance trasversale, non di merito.
    In regime ordinario, la fase successiva è sempre FASE_0_TER.
    In FAST-TRACK il controllo può essere recuperato ex post; qui il gate
    restituisce comunque la qualificazione del flow_mode e della next_phase.
    """

    validation_errors = _validate_required_payload(payload)
    if validation_errors:
        return {
            "phase_id": FASE_0_BIS_PHASE_ID,
            "phase_name": FASE_0_BIS_PHASE_NAME,
            "method_version": str(payload.get("method_version", "UNKNOWN")),
            "session_id": str(payload.get("session_id", "UNKNOWN")),
            "status": "BLOCKED",
            "input_from_phase_0": _extract_input_from_phase0(payload),
            "presidi": {key: _make_presidio("NON_RILEVANTE", "") for key in PRESIDI_KEYS},
            "presidi_attivati": [],
            "warning": [],
            "blocking_reasons": validation_errors,
            "native_block_scope": [
                "conflitto_interessi_non_gestito",
                "obbligo_pubblicazione_non_considerato",
                "trattamento_dati_non_conforme",
            ],
            "next_phase": "NONE",
            "trace": {
                "flow_mode": "FAST_TRACK" if _safe_bool(payload.get("fast_track", False)) else "ORDINARIO",
                "sequenza_ordinaria": "FASE_0 > FASE_0_BIS > FASE_0_TER > FIP_IND",
                "note": "Input schema validation failed",
            },
        }

    session_id = str(payload["session_id"])
    method_version = str(payload["method_version"])
    materia_prevalente = str(payload["materia_prevalente"])
    rischio_iniziale = str(payload["rischio_iniziale"])
    intensita_applicativa = str(payload["intensita_applicativa"])
    fast_track = _safe_bool(payload.get("fast_track", False))
    sensibilita = payload["sensibilita"]

    conflitto_interessi_rilevato = _safe_bool(payload.get("conflitto_interessi_rilevato", False))
    conflitto_interessi_gestito = _safe_bool(payload.get("conflitto_interessi_gestito", True))

    obbligo_pubblicazione_rilevato = _safe_bool(payload.get("obbligo_pubblicazione_rilevato", False))
    obbligo_pubblicazione_considerato = _safe_bool(payload.get("obbligo_pubblicazione_considerato", True))

    trattamento_dati_personali_rilevato = _safe_bool(payload.get("trattamento_dati_personali_rilevato", False))
    trattamento_dati_conforme = _safe_bool(payload.get("trattamento_dati_conforme", True))
    necessita_omissis = _safe_bool(payload.get("necessita_omissis", False))

    incidenza_su_obiettivi_piao = _safe_bool(payload.get("incidenza_su_obiettivi_piao", False))
    pertinenza_sicurezza_lavoro = _safe_bool(payload.get("pertinenza_sicurezza_lavoro", False))
    obblighi_specifici_codice_comportamento = _safe_bool(payload.get("obblighi_specifici_codice_comportamento", False))

    presidi: Dict[str, Dict[str, str]] = {}
    presidi_attivati: List[str] = []
    warnings: List[str] = []
    blocking_reasons: List[str] = []

    # Anticorruzione
    anticorruzione_attivo = conflitto_interessi_rilevato or rischio_iniziale in {"MEDIO", "ALTO"}
    if anticorruzione_attivo:
        reason = "Possibile incidenza di conflitto/interesse o profilo di rischio che richiede presidio anticorruzione"
        presidi["anticorruzione"] = _make_presidio("ATTIVO", reason)
        presidi_attivati.append("anticorruzione")
    else:
        presidi["anticorruzione"] = _make_presidio("NON_RILEVANTE", "Nessuna incidenza rilevata")

    # Trasparenza
    trasparenza_attiva = _safe_bool(sensibilita.get("benefici_economici", False)) or obbligo_pubblicazione_rilevato
    if trasparenza_attiva:
        reason = "Presenza di benefici economici o obblighi di pubblicazione potenzialmente rilevanti"
        presidi["trasparenza"] = _make_presidio("ATTIVO", reason)
        presidi_attivati.append("trasparenza")
    else:
        presidi["trasparenza"] = _make_presidio("NON_RILEVANTE", "Nessuna incidenza rilevata")

    # Privacy
    privacy_attiva = _safe_bool(sensibilita.get("dati_personali", False)) or trattamento_dati_personali_rilevato
    if privacy_attiva:
        reason = "Presenza di dati personali o trattamento dati rilevato"
        if necessita_omissis:
            reason += "; verificare omissis/minimizzazione"
            warnings.append("Necessita_omissis_rilevata")
        presidi["privacy"] = _make_presidio("ATTIVO", reason)
        presidi_attivati.append("privacy")
    else:
        presidi["privacy"] = _make_presidio("NON_RILEVANTE", "Nessuna incidenza rilevata")

    # Performance / PIAO
    performance_attiva = incidenza_su_obiettivi_piao
    if performance_attiva:
        presidi["performance_piao"] = _make_presidio(
            "ATTIVO",
            "Possibile incidenza su obiettivi organizzativi / PIAO",
        )
        presidi_attivati.append("performance_piao")
    else:
        presidi["performance_piao"] = _make_presidio("NON_RILEVANTE", "Nessuna incidenza rilevata")

    # Sicurezza sul lavoro
    sicurezza_attiva = pertinenza_sicurezza_lavoro
    if sicurezza_attiva:
        presidi["sicurezza_lavoro"] = _make_presidio(
            "ATTIVO",
            "Attività o contesto con possibile rilevanza in materia di sicurezza sul lavoro",
        )
        presidi_attivati.append("sicurezza_lavoro")
    else:
        presidi["sicurezza_lavoro"] = _make_presidio("NON_RILEVANTE", "Nessuna incidenza rilevata")

    # Codice di comportamento
    codice_attivo = obblighi_specifici_codice_comportamento
    if codice_attivo:
        presidi["codice_comportamento"] = _make_presidio(
            "ATTIVO",
            "Obblighi specifici di comportamento rilevati nel contesto dell'atto",
        )
        presidi_attivati.append("codice_comportamento")
    else:
        presidi["codice_comportamento"] = _make_presidio("NON_RILEVANTE", "Nessuna incidenza rilevata")

    # Blocchi propri della fase
    if conflitto_interessi_rilevato and not conflitto_interessi_gestito:
        blocking_reasons.append("Conflitto di interessi non gestito")

    if obbligo_pubblicazione_rilevato and not obbligo_pubblicazione_considerato:
        blocking_reasons.append("Obbligo di pubblicazione non considerato")

    if privacy_attiva and not trattamento_dati_conforme:
        blocking_reasons.append("Trattamento dati non conforme")

    status = "BLOCKED" if blocking_reasons else "OK"

    if fast_track:
        next_phase = "M07_LPR_FAST_TRACK" if status == "OK" else "NONE"
        flow_mode = "FAST_TRACK"
        trace_note = (
            "In FAST-TRACK il pacchetto minimo pre-adozione può recuperare 0-bis/0-ter ex post entro 30 giorni"
        )
    else:
        next_phase = "FASE_0_TER" if status == "OK" else "NONE"
        flow_mode = "ORDINARIO"
        trace_note = "Sequenza ordinaria vincolante"

    return {
        "phase_id": FASE_0_BIS_PHASE_ID,
        "phase_name": FASE_0_BIS_PHASE_NAME,
        "method_version": method_version,
        "session_id": session_id,
        "status": status,
        "input_from_phase_0": {
            "natura_output": payload.get("natura_output"),
            "tipologia_atto": payload.get("tipologia_atto"),
            "materia_prevalente": materia_prevalente,
            "sensibilita": {
                "dati_personali": _safe_bool(sensibilita.get("dati_personali", False)),
                "benefici_economici": _safe_bool(sensibilita.get("benefici_economici", False)),
                "pnrr_o_finanziamenti_vincolati": _safe_bool(
                    sensibilita.get("pnrr_o_finanziamenti_vincolati", False)
                ),
                "impatto_esterno_rilevante": _safe_bool(
                    sensibilita.get("impatto_esterno_rilevante", False)
                ),
            },
            "rischio_iniziale": rischio_iniziale,
            "intensita_applicativa": intensita_applicativa,
            "fast_track": fast_track,
            "zone_rosse": payload.get("zone_rosse", []),
        },
        "presidi": presidi,
        "presidi_attivati": presidi_attivati,
        "warning": warnings,
        "blocking_reasons": blocking_reasons,
        "native_block_scope": [
            "conflitto_interessi_non_gestito",
            "obbligo_pubblicazione_non_considerato",
            "trattamento_dati_non_conforme",
        ],
        "next_phase": next_phase,
        "trace": {
            "flow_mode": flow_mode,
            "sequenza_ordinaria": "FASE_0 > FASE_0_BIS > FASE_0_TER > FIP_IND",
            "note": trace_note,
        },
    }