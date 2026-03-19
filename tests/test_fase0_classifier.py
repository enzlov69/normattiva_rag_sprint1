from runtime.fase0_classifier import run_fase0


def test_fase0_ok():
    payload = {
        "session_id": "test-001",
        "method_version": "PPAV_2_2",
        "natura_output": "ATTO OPPONIBILE",
        "tipologia_atto": "Determina",
        "materia_prevalente": "CONTRATTI_AFFIDAMENTI",
        "sensibilita": {
            "dati_personali": "NO",
            "benefici_economici": "SI",
            "pnrr_vincoli": "NO",
            "impatto_esterno": "SI"
        },
        "zone_rosse": ["affidamento"],
        "fast_track_requested": False,
        "urgenza_motivata": False,
        "debito_fuori_bilancio": False,
        "impatto_economico_significativo": True,
        "profilo_contenzioso_potenziale": False
    }

    result = run_fase0(payload)

    assert result["status"] == "OK"
    assert result["rischio_iniziale"] == "ALTO"
    assert result["next_phase"] == "FASE_0_BIS"


def test_fase0_block_missing_tipo():
    payload = {
        "session_id": "test-002",
        "method_version": "PPAV_2_2",
        "natura_output": "ATTO OPPONIBILE",
        "materia_prevalente": "TRIBUTI"
    }

    result = run_fase0(payload)

    assert result["status"] == "BLOCKED"
    assert "Tipologia atto obbligatoria" in result["blocking_reasons"][0]