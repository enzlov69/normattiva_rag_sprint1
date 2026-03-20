from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict
from urllib import request, error

JsonDict = Dict[str, Any]
TransportCallable = Callable[[JsonDict], JsonDict]


class FederatedRunnerLiveTransportError(RuntimeError):
    """Errore tecnico di trasporto verso il runner federato reale."""


def build_transport() -> TransportCallable:
    """
    Costruisce un transport reale minimale verso il runner federato.

    Regole:
    - il transport non interpreta;
    - il transport non valida in senso metodologico;
    - il transport non conclude;
    - il transport inoltra la request e restituisce la response JSON grezza come dict.

    Variabili ambiente supportate:
    - FEDERATED_RUNNER_LIVE_ENDPOINT
    - FEDERATED_RUNNER_LIVE_BEARER_TOKEN   (opzionale)
    - FEDERATED_RUNNER_LIVE_TIMEOUT_SECONDS (opzionale, default 30)
    """

    endpoint = os.getenv("FEDERATED_RUNNER_LIVE_ENDPOINT")
    if not endpoint:
        raise FederatedRunnerLiveTransportError(
            "Missing environment variable FEDERATED_RUNNER_LIVE_ENDPOINT."
        )

    timeout = int(os.getenv("FEDERATED_RUNNER_LIVE_TIMEOUT_SECONDS", "30"))
    bearer_token = os.getenv("FEDERATED_RUNNER_LIVE_BEARER_TOKEN")

    def _transport(envelope: JsonDict) -> JsonDict:
        if not isinstance(envelope, dict):
            raise FederatedRunnerLiveTransportError(
                "Transport input must be a dict request envelope."
            )

        body = json.dumps(envelope).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"

        http_request = request.Request(
            url=endpoint,
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8")
            except Exception:
                detail = str(exc)
            raise FederatedRunnerLiveTransportError(
                f"HTTP error from federated runner: {exc.code} {detail}"
            ) from exc
        except error.URLError as exc:
            raise FederatedRunnerLiveTransportError(
                f"Connection error to federated runner: {exc}"
            ) from exc
        except Exception as exc:
            raise FederatedRunnerLiveTransportError(
                f"Unexpected transport error: {exc}"
            ) from exc

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise FederatedRunnerLiveTransportError(
                "Federated runner response is not valid JSON."
            ) from exc

        if not isinstance(parsed, dict):
            raise FederatedRunnerLiveTransportError(
                "Federated runner response must be a JSON object."
            )

        return parsed

    return _transport