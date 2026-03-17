import json
from pathlib import Path

from src.config.normattiva_config import PRE_BASE_URL
from src.connectors.normattiva_client import NormattivaClient


class _FakeResponse:
    def __init__(self, body: str, *, status: int = 200, content_type: str = "application/json") -> None:
        self._body = body.encode("utf-8")
        self.status = status
        self.headers = {"Content-Type": content_type}

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_normattiva_client_builds_pre_url() -> None:
    client = NormattivaClient()
    assert client.build_url("search_simple") == f"{PRE_BASE_URL}/bff-opendata/v1/api/v1/ricerca/semplice"


def test_normattiva_client_loads_payload_from_file(tmp_path: Path) -> None:
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps({"ok": True, "count": 2}), encoding="utf-8")

    client = NormattivaClient()
    payload = client.load_payload_from_file(payload_path)

    assert payload == {"ok": True, "count": 2}


def test_normattiva_client_search_simple_posts_json(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout=0):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse('{"numeroAttiTrovati": 1, "atti": []}')

    monkeypatch.setattr("src.connectors.normattiva_client.urlopen", fake_urlopen)

    client = NormattivaClient()
    response = client.search_simple(
        parametri_ricerca={"numeroProvvedimento": 267, "annoProvvedimento": 2000},
        pagina_corrente=2,
        numero_elementi_per_pagina=15,
    )

    assert captured["url"].endswith("/bff-opendata/v1/api/v1/ricerca/semplice")
    assert captured["body"]["paginaCorrente"] == 2
    assert captured["body"]["numeroElementiPerPagina"] == 15
    assert response["numeroAttiTrovati"] == 1
