
from __future__ import annotations

import json
from dataclasses import dataclass, field
from os import getenv
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urljoin


DEFAULT_PROD_BASE_URL = "https://api.normattiva.it/t/normattiva.api/bff-opendata/v1"
DEFAULT_PRE_BASE_URL = "https://pre.api.normattiva.it/t/normattiva.api/bff-opendata/v1"


@dataclass(frozen=True)
class LiveApiSettings:
    base_url: str = getenv("NORMATTIVA_LIVE_BASE_URL", DEFAULT_PROD_BASE_URL)
    timeout_seconds: int = int(getenv("NORMATTIVA_LIVE_TIMEOUT_SECONDS", "30"))
    user_agent: str = getenv("NORMATTIVA_LIVE_USER_AGENT", "normattiva-rag-metodo-cerda/live-api")
    verify_ssl: bool = getenv("NORMATTIVA_LIVE_VERIFY_SSL", "true").lower() != "false"
    openapi_spec_path: Optional[str] = getenv("NORMATTIVA_OPENAPI_SPEC_PATH")
    postman_collection_path: Optional[str] = getenv("NORMATTIVA_POSTMAN_COLLECTION_PATH")
    default_headers: Dict[str, str] = field(default_factory=lambda: {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    })
    endpoints: Dict[str, str] = field(default_factory=lambda: {
        "search_simple": "/api/v1/ricerca/semplice",
        "search_advanced": "/api/v1/ricerca/avanzata",
        "search_updated": "/api/v1/ricerca/aggiornati",
        "detail_atto": "/api/v1/atto/dettaglio-atto",
        "async_new_search": "/api/v1/ricerca-asincrona/nuova-ricerca",
        "async_confirm_search": "/api/v1/ricerca-asincrona/conferma-ricerca",
        "async_check_status": "/api/v1/ricerca-asincrona/check-status/{token}",
    })

    def build_url(self, path: str) -> str:
        return urljoin(f"{self.base_url.rstrip('/')}/", path.lstrip('/'))

    @classmethod
    def from_openapi(cls, spec_path: str | Path, *, prefer_pre: bool = False) -> "LiveApiSettings":
        path = Path(spec_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        server_url = None
        servers = data.get("servers") or []
        if servers:
            server_url = servers[0].get("url")
        base_url = server_url or (DEFAULT_PRE_BASE_URL if prefer_pre else DEFAULT_PROD_BASE_URL)
        paths = data.get("paths") or {}
        endpoints = {
            "search_simple": "/api/v1/ricerca/semplice",
            "search_advanced": "/api/v1/ricerca/avanzata",
            "search_updated": "/api/v1/ricerca/aggiornati",
            "detail_atto": "/api/v1/atto/dettaglio-atto",
            "async_new_search": "/api/v1/ricerca-asincrona/nuova-ricerca",
            "async_confirm_search": "/api/v1/ricerca-asincrona/conferma-ricerca",
            "async_check_status": "/api/v1/ricerca-asincrona/check-status/{token}",
        }
        missing = [p for p in endpoints.values() if p not in paths]
        if missing:
            raise ValueError(f"Spec OpenAPI priva dei path attesi: {', '.join(missing)}")
        return cls(base_url=base_url, openapi_spec_path=str(path), endpoints=endpoints)
