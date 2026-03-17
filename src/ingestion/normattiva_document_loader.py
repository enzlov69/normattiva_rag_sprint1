import json
from pathlib import Path
from typing import Any

from src.connectors.normattiva_errors import NormattivaInvalidPayloadError


class NormattivaDocumentLoader:
    """Loads previously saved Normattiva payloads from disk and validates basic usability."""

    def load_json_file(self, filepath: str | Path) -> Any:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(path)

        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            raise NormattivaInvalidPayloadError("File payload Normattiva vuoto")

        payload = json.loads(raw)
        if payload in ({}, [], None, ""):
            raise NormattivaInvalidPayloadError("Payload Normattiva vuoto o non utilizzabile")
        return payload
