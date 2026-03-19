from runtime.fip_ind_gate import run_fip_ind


def test_fip_ind_ok_indirizzo_puro():
    payload = {
        "natura_output": "INDIRIZZO",
        "testo": "La Giunta fornisce indirizzi per la programmazione culturale."
    }

    result = run_fip_ind(payload)

    assert result["status"] == "OK"
    assert result["qualificazione"]["indirizzo"] is True
    assert result["qualificazione"]["provvedimento"] is False


def test_fip_ind_block_falso_indirizzo():
    payload = {
        "natura_output": "INDIRIZZO",
        "testo": "La Giunta affida il servizio e definisce indirizzi."
    }

    result = run_fip_ind(payload)

    assert result["status"] == "BLOCKED"
    assert "Falso indirizzo" in result["blocking_reasons"][0]


def test_fip_ind_ok_provvedimento():
    payload = {
        "natura_output": "ATTO",
        "testo": "Il Responsabile impegna la somma e affida il servizio."
    }

    result = run_fip_ind(payload)

    assert result["status"] == "OK"
    assert result["qualificazione"]["provvedimento"] is True


def test_fip_ind_warning_misto():
    payload = {
        "natura_output": "ATTO",
        "testo": "Si definiscono indirizzi e si dispone l'affidamento."
    }

    result = run_fip_ind(payload)

    assert result["status"] == "OK"
    assert len(result["warning"]) > 0