
from __future__ import annotations

from typing import Dict, List, Optional

from src.config.live_api_settings import LiveApiSettings
from src.live_api.live_normattiva_client import LiveNormattivaClient
from src.live_api.live_request_builder import LiveRequestBuilder
from src.live_api.live_response_mapper import LiveResponseMapper


class LiveSearchService:
    def __init__(
        self,
        *,
        settings: Optional[LiveApiSettings] = None,
        client: Optional[LiveNormattivaClient] = None,
        request_builder: Optional[LiveRequestBuilder] = None,
        response_mapper: Optional[LiveResponseMapper] = None,
    ) -> None:
        self.settings = settings or LiveApiSettings()
        self.client = client or LiveNormattivaClient(self.settings)
        self.request_builder = request_builder or LiveRequestBuilder(self.settings)
        self.response_mapper = response_mapper or LiveResponseMapper()

    def search_simple(self, *, query_text: str, page: int = 1, page_size: int = 10) -> List[Dict]:
        request = self.request_builder.build_search_simple(
            query_text=query_text,
            page=page,
            page_size=page_size,
        )
        response = self.client.execute(request)
        return self.response_mapper.extract_search_items(response.payload)

    def search_advanced(self, *, testo_ricerca: str, **kwargs) -> List[Dict]:
        request = self.request_builder.build_search_advanced(testo_ricerca=testo_ricerca, **kwargs)
        response = self.client.execute(request)
        return self.response_mapper.extract_search_items(response.payload)
