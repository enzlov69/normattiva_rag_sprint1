from runtime.fase0ter_normative_gate import run_fase0ter


def test_fase0ter_ok_contratti():
    payload = {
        "session_id": "test-0ter-001",
        "method_version": "PPAV_2_2",
        "natura_output": "ATTO OPPONIBILE",
        "tipologia_atto": "Determina",
        "materia_prevalente": "CONTRATTI_AFFIDAMENTI",
        "sensibilita": {
            "dati_personali": False,
            "benefici_economici": False,
            "pnrr_o_finanziamenti_vincolati": False,
            "impatto_esterno_rilevante": True
        },
        "rischio_iniziale": "ALTO",
        "fast_track": False,
        "zone_rosse": ["affidamento"]
    }

    result = run_fase0ter(payload)

    assert result["status"] == "OK"
    assert "D.Lgs. 36/2023" in " | ".join(result["normativa_attivata"])
    assert "Regolamento comunale per affidamenti/contratti" in result["regolamenti_rilevanti"]
    assert result["next_phase"] == "FIP_IND"


def test_fase0ter_ok_contabile_con_privacy_trasparenza():
    payload = {
        "session_id": "test-0ter-002",
        "method_version": "PPAV_2_2",
        "natura_output": "ATTO OPPONIBILE",
        "tipologia_atto": "Determina",
        "materia_prevalente": "CONTABILE_BILANCIO",
        "sensibilita": {
            "dati_personali": True,
            "benefici_economici": True,
            "pnrr_o_finanziamenti_vincolati": False,
            "impatto_esterno_rilevante": False
        },
        "rischio_iniziale": "MEDIO",
        "fast_track": False,
        "zone_rosse": ["impegno"]
    }

    result = run_fase0ter(payload)

    assert result["status"] == "OK"
    assert any("GDPR" in x for x in result["normativa_attivata"])
    assert any("D.Lgs. 33/2013" in x for x in result["normativa_attivata"])
    assert "vincoli_privacy" in result["vincoli_attivati"]
    assert "obblighi_trasparenza" in result["vincoli_attivati"]


def test_fase0ter_fast_track():
    payload = {
        "session_id": "test-0ter-003",
        "method_version": "PPAV_2_2",
        "natura_output": "ATTO OPPONIBILE",
        "tipologia_atto": "Determina",
        "materia_prevalente": "SERVIZI_ALLA_PERSONA",
        "sensibilita": {
            "dati_personali": False,
            "benefici_economici": False,
            "pnrr_o_finanziamenti_vincolati": False,
            "impatto_esterno_rilevante": True
        },
        "rischio_iniziale": "MEDIO",
        "fast_track": True,
        "zone_rosse": []
    }

    result = run_fase0ter(payload)

    assert result["status"] == "OK"
    assert result["next_phase"] == "M07_LPR_FAST_TRACK"
    assert any("FAST_TRACK" in x for x in result["warning"])


def test_fase0ter_block_invalid_materia():
    payload = {
        "session_id": "test-0ter-004",
        "method_version": "PPAV_2_2",
        "materia_prevalente": "MATERIA_NON_VALIDA",
        "rischio_iniziale": "BASSO"
    }

    result = run_fase0ter(payload)

    assert result["status"] == "BLOCKED"
    assert "Materia prevalente non mappata" in result["blocking_reasons"]
    assert result["next_phase"] == "NONE"