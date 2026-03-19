from runtime.s_pred_gate import run_s_pred

payload = {
    "session_id": "test-session-001",
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
    "ranking_status": "OK"
}

print(run_s_pred(payload))
