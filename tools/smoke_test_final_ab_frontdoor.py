import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.final_ab_runner_frontdoor import FinalABRunnerFrontDoor


def dummy_adapter_bridge(request_envelope):
    return {
        "request_id": request_envelope["request_id"],
        "case_id": request_envelope["case_id"],
        "trace_id": request_envelope["trace_id"],
        "api_version": request_envelope["api_version"],
        "responder_module": "B10_HybridRetriever",
        "status": "SUCCESS",
        "payload": {
            "documentary_packet": {
                "sources": [{"source_id": "src_001"}],
                "norm_units": [{"norm_unit_id": "nu_001"}],
            }
        },
        "warnings": [],
        "errors": [],
        "blocks": [],
        "timestamp": "2026-03-18T09:00:01Z",
    }


def main():
    request_envelope = {
        "request_id": "req_001",
        "case_id": "case_001",
        "trace_id": "trace_001",
        "api_version": "1.0",
        "caller_module": "A1_OrchestratorePPAV",
        "target_module": "B10_HybridRetriever",
        "timestamp": "2026-03-18T09:00:00Z",
        "payload": {
            "runner_payload": {
                "query": "art. 191 TUEL",
                "domain": "tuel",
                "top_k": 5,
            }
        },
    }

    frontdoor = FinalABRunnerFrontDoor(
        adapter_bridge=dummy_adapter_bridge
    )

    response = frontdoor.execute(request_envelope)

    print("=== FRONTDOOR RESPONSE ===")
    print(response)


if __name__ == "__main__":
    main()