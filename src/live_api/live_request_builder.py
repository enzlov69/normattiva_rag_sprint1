
from __future__ import annotations

from typing import Any, Dict, Optional

from src.config.live_api_settings import LiveApiSettings
from src.live_api.live_types import LivePreparedRequest


class LiveRequestBuilder:
    def __init__(self, settings: Optional[LiveApiSettings] = None) -> None:
        self.settings = settings or LiveApiSettings()

    def build_search_simple(
        self,
        *,
        query_text: str,
        order_type: str = "recente",
        page: int = 1,
        page_size: int = 10,
    ) -> LivePreparedRequest:
        body = {
            "testoRicerca": query_text,
            "orderType": order_type,
            "paginazione": {
                "paginaCorrente": page,
                "numeroElementiPerPagina": page_size,
            },
        }
        return self._build("POST", "search_simple", body, "Ricerca semplice live Normattiva")

    def build_search_advanced(
        self,
        *,
        testo_ricerca: str,
        denominazione_atto: Optional[str] = None,
        titolo_ricerca: Optional[str] = None,
        data_inizio_emanazione: Optional[str] = None,
        data_fine_emanazione: Optional[str] = None,
        data_vigenza: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> LivePreparedRequest:
        body: Dict[str, Any] = {
            "testoRicerca": testo_ricerca,
            "orderType": "recente",
            "paginazione": {
                "paginaCorrente": page,
                "numeroElementiPerPagina": page_size,
            },
        }
        if denominazione_atto:
            body["denominazioneAtto"] = denominazione_atto
        if titolo_ricerca:
            body["titoloRicerca"] = titolo_ricerca
        if data_inizio_emanazione:
            body["dataInizioEmanazione"] = data_inizio_emanazione
        if data_fine_emanazione:
            body["dataFineEmanazione"] = data_fine_emanazione
        if data_vigenza:
            body["vigenza"] = data_vigenza
        return self._build("POST", "search_advanced", body, "Ricerca avanzata live Normattiva")

    def build_detail_atto(self, *, detail_payload: Dict[str, Any]) -> LivePreparedRequest:
        return self._build("POST", "detail_atto", detail_payload, "Dettaglio atto live Normattiva")

    def build_async_new_search(
        self,
        *,
        query_text: str,
        formato: str = "JSON",
        tipo_ricerca: str = "A",
        modalita: str = "C",
        email: Optional[str] = None,
    ) -> LivePreparedRequest:
        body: Dict[str, Any] = {
            "formato": formato,
            "tipoRicerca": tipo_ricerca,
            "modalita": modalita,
            "parametriRicerca": {"testoRicerca": query_text},
        }
        if email:
            body["email"] = email
        return self._build("POST", "async_new_search", body, "Ricerca asincrona live Normattiva")

    def build_async_confirm_search(self, *, token: str) -> LivePreparedRequest:
        return self._build("PUT", "async_confirm_search", token.strip(), "Conferma ricerca asincrona live Normattiva",
                           headers={"Content-Type": "text/plain; charset=utf-8"})

    def build_async_check_status(self, *, token: str) -> LivePreparedRequest:
        path = self.settings.endpoints["async_check_status"].replace("{token}", token.strip())
        return LivePreparedRequest(
            method="GET",
            path=path,
            url=self.settings.build_url(path),
            headers=self._headers(None),
            body=None,
            description="Check status ricerca asincrona live Normattiva",
        )

    def _build(self, method: str, endpoint_key: str, body: Any, description: str, headers: Optional[Dict[str, str]] = None) -> LivePreparedRequest:
        path = self.settings.endpoints[endpoint_key]
        return LivePreparedRequest(
            method=method,
            path=path,
            url=self.settings.build_url(path),
            headers=self._headers(headers),
            body=body,
            description=description,
        )

    def _headers(self, extra: Optional[Dict[str, str]]) -> Dict[str, str]:
        headers = dict(self.settings.default_headers)
        headers["User-Agent"] = self.settings.user_agent
        if extra:
            headers.update(extra)
        return headers
