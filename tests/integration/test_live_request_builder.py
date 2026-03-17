
from src.config.live_api_settings import LiveApiSettings
from src.live_api.live_request_builder import LiveRequestBuilder


def test_build_search_simple_uses_official_path() -> None:
    settings = LiveApiSettings()
    builder = LiveRequestBuilder(settings)

    request = builder.build_search_simple(query_text='tuel', page=2, page_size=5)

    assert request.method == 'POST'
    assert request.path == '/api/v1/ricerca/semplice'
    assert request.body['testoRicerca'] == 'tuel'
    assert request.body['paginazione']['paginaCorrente'] == 2
    assert request.body['paginazione']['numeroElementiPerPagina'] == 5
    assert request.url.startswith(settings.base_url)


def test_build_detail_atto_payload_is_passed_verbatim() -> None:
    settings = LiveApiSettings()
    builder = LiveRequestBuilder(settings)
    payload = {'codiceRedazionale': '000X0001', 'idArticolo': 1, 'versione': 0}

    request = builder.build_detail_atto(detail_payload=payload)

    assert request.method == 'POST'
    assert request.path == '/api/v1/atto/dettaglio-atto'
    assert request.body == payload
