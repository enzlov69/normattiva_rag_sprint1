from runtime.rac_gate import run_rac


def test_rac_ok():
    payload = {
        "session_id": "rac-001",
        "method_version": "PPAV_2_2",
        "norma": "D.Lgs. 267/2000",
        "articoli_rilevanti": ["art. 107"]
    }

    result = run_rac(payload)

    assert result["status"] == "OK"
    assert result["output"]["esito_rac"] == "OK"
    assert result["next_phase"] == "M07_LPR"


def test_rac_block_missing_norma():
    payload = {
        "session_id": "rac-002",
        "method_version": "PPAV_2_2",
        "norma": "",
        "articoli_rilevanti": ["art. 107"]
    }

    result = run_rac(payload)

    assert result["status"] == "BLOCKED"


def test_rac_block_missing_articoli():
    payload = {
        "session_id": "rac-003",
        "method_version": "PPAV_2_2",
        "norma": "TUEL",
        "articoli_rilevanti": []
    }

    result = run_rac(payload)

    assert result["status"] == "BLOCKED"