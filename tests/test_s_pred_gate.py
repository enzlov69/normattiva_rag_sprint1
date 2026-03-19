from runtime.s_pred_gate import run_s_pred


def _base_payload():
    return {
        "session_id": "sess-001",
        "method_version": "PPAV_2_2",
        "corpus_available": True,
        "modules_available": True,
        "safeguards_available": True,
        "retrieval_available": True,
        "citations_available": True,
        "audit_trail_available": True,
        "block_propagation_available": True,
        "version_alignment_ok": True,
        "indexing_status": "OK",
        "ranking_status": "OK",
        "shadow_store_available": True,
    }


def test_s_pred_available_when_all_blocking_checks_pass():
    result = run_s_pred(_base_payload())
    assert result["status"] == "AVAILABLE"
    assert result["can_start_fase0"] is True
    assert result["transition_allowed"] is True
    assert result["next_phase"] == "FASE_0"
    assert result["gate_outcome"] == "DISPONIBILE"
    assert result["blocking_reasons"] == []


def test_s_pred_blocked_when_corpus_is_missing():
    payload = _base_payload()
    payload["corpus_available"] = False
    result = run_s_pred(payload)
    assert result["status"] == "BLOCKED"
    assert result["can_start_fase0"] is False
    assert any("Corpus" in reason for reason in result["blocking_reasons"])


def test_s_pred_blocked_when_retrieval_is_not_available():
    payload = _base_payload()
    payload["retrieval_available"] = False
    result = run_s_pred(payload)
    assert result["status"] == "BLOCKED"
    assert any("Retrieval" in reason for reason in result["blocking_reasons"])


def test_s_pred_blocked_when_audit_trail_is_not_available():
    payload = _base_payload()
    payload["audit_trail_available"] = False
    result = run_s_pred(payload)
    assert result["status"] == "BLOCKED"
    assert any("Audit trail" in reason for reason in result["blocking_reasons"])


def test_s_pred_blocked_when_input_is_incomplete():
    result = run_s_pred({"session_id": "sess-001"})
    assert result["status"] == "BLOCKED"
    assert result["can_start_fase0"] is False
    assert result["checks"] == []
    assert len(result["blocking_reasons"]) > 0


def test_s_pred_available_with_warnings_for_degraded_indexing_and_ranking():
    payload = _base_payload()
    payload["indexing_status"] = "DEGRADED"
    payload["ranking_status"] = "STALE"
    result = run_s_pred(payload)
    assert result["status"] == "AVAILABLE"
    assert len(result["warnings"]) == 2
