
import json
from pathlib import Path

from src.config.live_api_settings import LiveApiSettings
from src.live_api.live_normattiva_client import LiveNormattivaClient
from src.live_api.live_request_builder import LiveRequestBuilder


class _FakeResponse:
    def __init__(self, payload: str, *, status: int = 200, content_type: str = 'application/json') -> None:
        self._payload = payload.encode('utf-8')
        self.status = status
        self.headers = {'Content-Type': content_type}

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_settings_from_openapi_reads_server_and_required_paths(tmp_path: Path) -> None:
    spec = {
        'openapi': '3.0.1',
        'servers': [{'url': 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1'}],
        'paths': {
            '/api/v1/ricerca/semplice': {'post': {}},
            '/api/v1/ricerca/avanzata': {'post': {}},
            '/api/v1/ricerca/aggiornati': {'post': {}},
            '/api/v1/atto/dettaglio-atto': {'post': {}},
            '/api/v1/ricerca-asincrona/nuova-ricerca': {'post': {}},
            '/api/v1/ricerca-asincrona/conferma-ricerca': {'put': {}},
            '/api/v1/ricerca-asincrona/check-status/{token}': {'get': {}},
        },
    }
    spec_path = tmp_path / 'openapi.json'
    spec_path.write_text(json.dumps(spec), encoding='utf-8')

    settings = LiveApiSettings.from_openapi(spec_path)

    assert settings.base_url == 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1'
    assert settings.endpoints['detail_atto'] == '/api/v1/atto/dettaglio-atto'


def test_live_client_executes_prepared_request_with_fake_transport() -> None:
    settings = LiveApiSettings()
    builder = LiveRequestBuilder(settings)
    prepared = builder.build_search_simple(query_text='bilancio')

    def fake_opener(request, timeout=0, context=None):
        assert request.full_url == prepared.url
        return _FakeResponse('{"content": [{"codiceRedazionale": "011G0118"}]}')

    client = LiveNormattivaClient(settings, opener=fake_opener)
    envelope = client.execute(prepared)

    assert envelope.status_code == 200
    assert envelope.payload['content'][0]['codiceRedazionale'] == '011G0118'
