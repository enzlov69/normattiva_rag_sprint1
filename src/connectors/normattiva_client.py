import json
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.config.normattiva_config import NormattivaConfig
from src.connectors.normattiva_errors import (
    NormattivaHttpError,
    NormattivaInvalidPayloadError,
    NormattivaTransportError,
)


class NormattivaClient:
    def __init__(self, config: Optional[NormattivaConfig] = None) -> None:
        self.config = config or NormattivaConfig()

    def build_url(self, endpoint_key_or_path: str) -> str:
        path = self.config.endpoints.get(endpoint_key_or_path, endpoint_key_or_path)
        return self.config.build_url(path)

    def search_simple(
        self,
        *,
        parametri_ricerca: Dict[str, Any],
        pagina_corrente: int = 1,
        numero_elementi_per_pagina: int = 20,
        filtri_map: Optional[Dict[str, Any]] = None,
    ) -> Any:
        payload: Dict[str, Any] = {
            "parametriRicerca": parametri_ricerca,
            "paginaCorrente": pagina_corrente,
            "numeroElementiPerPagina": numero_elementi_per_pagina,
        }
        if filtri_map:
            payload["filtriMap"] = filtri_map
        return self.post_json("search_simple", payload)

    def search_advanced(
        self,
        *,
        parametri_ricerca: Dict[str, Any],
        pagina_corrente: int = 1,
        numero_elementi_per_pagina: int = 20,
        filtri_map: Optional[Dict[str, Any]] = None,
    ) -> Any:
        payload: Dict[str, Any] = {
            "parametriRicerca": parametri_ricerca,
            "paginaCorrente": pagina_corrente,
            "numeroElementiPerPagina": numero_elementi_per_pagina,
        }
        if filtri_map:
            payload["filtriMap"] = filtri_map
        return self.post_json("search_advanced", payload)

    def start_async_search(
        self,
        *,
        parametri_ricerca: Dict[str, Any],
        formato: str = "JSON",
        tipo_ricerca: str = "A",
        modalita: str = "C",
        email: Optional[str] = None,
        data_vigenza: Optional[str] = None,
        filtri_map: Optional[Dict[str, Any]] = None,
    ) -> Any:
        payload: Dict[str, Any] = {
            "formato": formato,
            "tipoRicerca": tipo_ricerca,
            "modalita": modalita,
            "parametriRicerca": parametri_ricerca,
        }
        if email:
            payload["email"] = email
        if data_vigenza:
            payload["dataVigenza"] = data_vigenza
        if filtri_map:
            payload["filtriMap"] = filtri_map
        return self.post_json("async_new_search", payload)

    def confirm_async_search(self, collection_token: str) -> Any:
        if not collection_token or not collection_token.strip():
            raise NormattivaInvalidPayloadError("Token collezione assente o vuoto")
        return self.post_text("async_confirm_search", collection_token.strip())

    def load_payload_from_file(self, filepath: str | Path) -> Any:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(path)
        return json.loads(path.read_text(encoding="utf-8"))

    def post_json(self, endpoint_key_or_path: str, payload: Dict[str, Any]) -> Any:
        return self._send_request(
            endpoint_key_or_path,
            body=json.dumps(payload).encode("utf-8"),
            content_type="application/json",
        )

    def post_text(self, endpoint_key_or_path: str, body_text: str) -> Any:
        return self._send_request(
            endpoint_key_or_path,
            body=body_text.encode("utf-8"),
            content_type="text/plain; charset=utf-8",
        )

    def _send_request(self, endpoint_key_or_path: str, *, body: bytes, content_type: str) -> Any:
        url = self.build_url(endpoint_key_or_path)
        headers = dict(self.config.default_headers)
        headers["User-Agent"] = self.config.user_agent
        headers["Content-Type"] = content_type
        request = Request(url=url, data=body, headers=headers, method="POST")

        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                status = getattr(response, "status", 200)
                content_type_header = ""
                headers_obj = getattr(response, "headers", None)
                if headers_obj is not None:
                    try:
                        content_type_header = headers_obj.get("Content-Type", "")
                    except AttributeError:
                        content_type_header = headers_obj.get("Content-Type", "") if isinstance(headers_obj, dict) else ""
        except HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            raise NormattivaHttpError(status_code=exc.code, body=body_text) from exc
        except URLError as exc:
            raise NormattivaTransportError(str(exc.reason)) from exc

        if status >= 400:
            raise NormattivaHttpError(status_code=status, body=raw)

        return self._parse_response_body(raw=raw, content_type_header=content_type_header)

    @staticmethod
    def _parse_response_body(*, raw: str, content_type_header: str) -> Any:
        if not raw:
            return None
        if "json" in (content_type_header or "").lower():
            return json.loads(raw)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw.strip()
