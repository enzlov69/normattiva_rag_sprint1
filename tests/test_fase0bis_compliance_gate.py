from runtime.fase0bis_compliance_gate import run_fase0bis


def test_fase0bis_ok_ordinario():
    payload = {
        "session_id": "test-0bis-001",
        "method_version": "PPAV_2_2_ALIGNED_2_3",
        "natura_output": "ATTO OPPONIBILE",
        "tipologia_atto": "Determina",
        "materia_prevalente": "SERVIZI_ALLA_PERSONA",
        "sensibilita": {
            "dati_personali": True,
            "benefici_economici": True,
            "pnrr_o_finanziamenti_vincolati": False,
            "impatto_esterno_rilevante": True,
        },
        "rischio_iniziale": "MEDIO",
        "intensita_applicativa": "STANDARD",
        "fast_track": False,
        "zone_rosse": [],
        "conflitto_interessi_rilevato": False,
        "conflitto_interessi_gestito": True,
        "obbligo_pubblicazione_rilevato": True,
        "obbligo_pubblicazione_considerato": True,
        "trattamento_dati_personali_rilevato": True,
        "trattamento_dati_conforme": True,
        "necessita_omissis": True,
        "incidenza_su_obiettivi_piao": False,
        "pertinenza_sicurezza_lavoro": False,
        "obblighi_specifici_codice_comportamento": False,
    }

    result = run_fase0bis(payload)

    assert result["status"] == "OK"
    assert result["next_phase"] == "FASE_0_TER"
    assert "privacy" in result["presidi_attivati"]
    assert "trasparenza" in result["presidi_attivati"]
    assert "Necessita_omissis_rilevata" in result["warning"]


def test_fase0bis_block_conflitto_non_gestito():
    payload = {
        "session_id": "test-0bis-002",
        "method_version": "PPAV_2_2_ALIGNED_2_3",
        "natura_output": "ATTO OPPONIBILE",
        "tipologia_atto": "Delibera GC",
        "materia_prevalente": "PATRIMONIO",
        "sensibilita": {
            "dati_personali": False,
            "benefici_economici": False,
            "pnrr_o_finanziamenti_vincolati": False,
            "impatto_esterno_rilevante": False,
        },
        "rischio_iniziale": "MEDIO",
        "intensita_applicativa": "STANDARD",
        "fast_track": False,
        "zone_rosse": [],
        "conflitto_interessi_rilevato": True,
        "conflitto_interessi_gestito": False,
        "obbligo_pubblicazione_rilevato": False,
        "obbligo_pubblicazione_considerato": True,
        "trattamento_dati_personali_rilevato": False,
        "trattamento_dati_conforme": True,
        "necessita_omissis": False,
        "incidenza_su_obiettivi_piao": False,
        "pertinenza_sicurezza_lavoro": False,
        "obblighi_specifici_codice_comportamento": False,
    }

    result = run_fase0bis(payload)

    assert result["status"] == "BLOCKED"
    assert "Conflitto di interessi non gestito" in result["blocking_reasons"]
    assert result["next_phase"] == "NONE"


def test_fase0bis_ok_fast_track():
    payload = {
        "session_id": "test-0bis-003",
        "method_version": "PPAV_2_2_ALIGNED_2_3",
        "natura_output": "ATTO OPPONIBILE",
        "tipologia_atto": "Determina",
        "materia_prevalente": "CONTRATTI_AFFIDAMENTI",
        "sensibilita": {
            "dati_personali": False,
            "benefici_economici": False,
            "pnrr_o_finanziamenti_vincolati": False,
            "impatto_esterno_rilevante": True,
        },
        "rischio_iniziale": "ALTO",
        "intensita_applicativa": "RAFFORZATA",
        "fast_track": True,
        "zone_rosse": ["affidamento"],
        "conflitto_interessi_rilevato": False,
        "conflitto_interessi_gestito": True,
        "obbligo_pubblicazione_rilevato": False,
        "obbligo_pubblicazione_considerato": True,
        "trattamento_dati_personali_rilevato": False,
        "trattamento_dati_conforme": True,
        "necessita_omissis": False,
        "incidenza_su_obiettivi_piao": False,
        "pertinenza_sicurezza_lavoro": False,
        "obblighi_specifici_codice_comportamento": False,
    }

    result = run_fase0bis(payload)

    assert result["status"] == "OK"
    assert result["next_phase"] == "M07_LPR_FAST_TRACK"
    assert result["trace"]["flow_mode"] == "FAST_TRACK"