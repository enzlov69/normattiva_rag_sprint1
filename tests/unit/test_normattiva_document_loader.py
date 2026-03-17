import json
from pathlib import Path

import pytest

from src.connectors.normattiva_errors import NormattivaInvalidPayloadError
from src.ingestion.normattiva_document_loader import NormattivaDocumentLoader


def test_normattiva_document_loader_loads_valid_json(tmp_path: Path) -> None:
    payload_path = tmp_path / "search_item.json"
    payload_path.write_text(json.dumps({"atto": "ok", "numero": 267}), encoding="utf-8")

    loader = NormattivaDocumentLoader()
    payload = loader.load_json_file(payload_path)

    assert payload["numero"] == 267


def test_normattiva_document_loader_rejects_empty_payload(tmp_path: Path) -> None:
    payload_path = tmp_path / "empty.json"
    payload_path.write_text("{}", encoding="utf-8")

    loader = NormattivaDocumentLoader()
    with pytest.raises(NormattivaInvalidPayloadError):
        loader.load_json_file(payload_path)
