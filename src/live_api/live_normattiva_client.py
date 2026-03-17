
from __future__ import annotations

import json
import ssl
from typing import Any, Callable, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.connectors.normattiva_errors import NormattivaHttpError, NormattivaTransportError
from src.config.live_api_settings import LiveApiSettings
from src.live_api.live_types import LivePreparedRequest, LiveResponseEnvelope


class LiveNormattivaClient:
    def __init__(
        self,
        settings: Optional[LiveApiSettings] = None,
        *,
        opener: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.settings = settings or LiveApiSettings()
        self._opener = opener or urlopen

    def execute(self, prepared_request: LivePreparedRequest) -> LiveResponseEnvelope:
        body_bytes = self._encode_body(prepared_request.body, prepared_request.headers.get("Content-Type", ""))
        request = Request(
            url=prepared_request.url,
            data=body_bytes,
            headers=prepared_request.headers,
            method=prepared_request.method,
        )
        context = None if self.settings.verify_ssl else ssl._create_unverified_context()
        try:
            with self._opener(request, timeout=self.settings.timeout_seconds, context=context) as response:
                raw = response.read().decode("utf-8")
                status = getattr(response, "status", 200)
                headers = dict(getattr(response, "headers", {}) or {})
        except HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            raise NormattivaHttpError(status_code=exc.code, body=body_text) from exc
        except URLError as exc:
            raise NormattivaTransportError(str(exc.reason)) from exc

        content_type = headers.get("Content-Type", "")
        payload = self._parse_body(raw, content_type)
        return LiveResponseEnvelope(
            status_code=status,
            content_type=content_type,
            payload=payload,
            raw_text=raw,
            headers=headers,
        )

    @staticmethod
    def _encode_body(body: Any, content_type: str) -> Optional[bytes]:
        if body is None:
            return None
        if isinstance(body, bytes):
            return body
        if isinstance(body, str):
            return body.encode("utf-8")
        if "json" in content_type.lower():
            return json.dumps(body).encode("utf-8")
        return str(body).encode("utf-8")

    @staticmethod
    def _parse_body(raw: str, content_type: str) -> Any:
        if not raw:
            return None
        if "json" in content_type.lower():
            return json.loads(raw)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
