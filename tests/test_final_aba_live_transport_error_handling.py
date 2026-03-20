from __future__ import annotations

from urllib import error

import pytest

from runtime.federated_runner_live_transport import (
    FederatedRunnerLiveTransportContractError,
    FederatedRunnerLiveTransportError,
    build_transport,
)


class _FakeResponse:
    def __init__(self, body: str):
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _request_envelope() -> dict:
    return {
        "request_id": "REQ-001",
        "case_id": "CASE-001",
        "trace_id": "TRACE-001",
        "status": "READY",
        "warnings": [],
        "errors": [],
        "blocks": [],
    }


def test_live_transport_raises_on_non_json_response(monkeypatch):
    monkeypatch.setenv("FEDERATED_RUNNER_LIVE_ENDPOINT", "https://runner.test/live")
    monkeypatch.setenv("FEDERATED_RUNNER_LIVE_TIMEOUT_SECONDS", "30")

    def _opener(_request, timeout):
        assert timeout == 30
        return _FakeResponse("not-json")

    transport = build_transport(opener=_opener, sleep_fn=lambda _: None)

    with pytest.raises(FederatedRunnerLiveTransportContractError):
        transport(_request_envelope())


def test_live_transport_retries_http_503_then_raises(monkeypatch):
    monkeypatch.setenv("FEDERATED_RUNNER_LIVE_ENDPOINT", "https://runner.test/live")
    monkeypatch.setenv("FEDERATED_RUNNER_LIVE_MAX_ATTEMPTS", "2")

    calls = {"count": 0}

    def _opener(_request, timeout):
        calls["count"] += 1
        raise error.HTTPError(
            url="https://runner.test/live",
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=None,
        )

    transport = build_transport(opener=_opener, sleep_fn=lambda _: None)

    with pytest.raises(FederatedRunnerLiveTransportError):
        transport(_request_envelope())

    assert calls["count"] == 2