from dataclasses import dataclass, field
from os import getenv
from typing import Dict
from urllib.parse import urljoin


PRE_BASE_URL = "https://pre.api.normattiva.it/t/normattiva.api"

SIMPLE_SEARCH_PATH = "/bff-opendata/v1/api/v1/ricerca/semplice"
ADVANCED_SEARCH_PATH = "/bff-opendata/v1/api/v1/ricerca/avanzata"
ASYNC_NEW_SEARCH_PATH = "/bff-opendata/v1/api/v1/ricerca-asincrona/nuova-ricerca"
ASYNC_CONFIRM_PATH = "/bff-opendata/v1/api/v1/ricerca-asincrona/conferma-ricerca"


@dataclass(frozen=True)
class NormattivaConfig:
    base_url: str = getenv("NORMATTIVA_BASE_URL", PRE_BASE_URL)
    timeout_seconds: int = int(getenv("NORMATTIVA_TIMEOUT_SECONDS", "30"))
    user_agent: str = getenv("NORMATTIVA_USER_AGENT", "normattiva-rag-metodo-cerda/2.0")
    default_headers: Dict[str, str] = field(
        default_factory=lambda: {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
        }
    )

    @property
    def endpoints(self) -> Dict[str, str]:
        return {
            "search_simple": SIMPLE_SEARCH_PATH,
            "search_advanced": ADVANCED_SEARCH_PATH,
            "async_new_search": ASYNC_NEW_SEARCH_PATH,
            "async_confirm_search": ASYNC_CONFIRM_PATH,
        }

    def build_url(self, path: str) -> str:
        return urljoin(f"{self.base_url.rstrip('/')}/", path.lstrip('/'))
