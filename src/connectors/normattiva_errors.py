from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse


ALLOWED_SOURCE_DOMAINS = (
    "normattiva.it",
    "www.normattiva.it",
    "dati.normattiva.it",
    "www.dati.normattiva.it",
    "gazzettaufficiale.it",
    "www.gazzettaufficiale.it",
)


class NormattivaError(Exception):
    """Base error for the Normattiva connector layer."""


class NormattivaTransportError(NormattivaError):
    """Raised when the HTTP transport fails before a valid response is received."""


@dataclass
class NormattivaHttpError(NormattivaError):
    status_code: int
    body: str = ""

    def __str__(self) -> str:
        return f"Normattiva HTTP error {self.status_code}: {self.body}".strip()


class NormattivaInvalidPayloadError(NormattivaError):
    """Raised when the payload shape is not usable by the internal mapper."""


class NormattivaMetadataError(NormattivaError):
    """Raised when required metadata are missing from a Normattiva payload."""


class NormattivaSourceUnverifiedError(NormattivaError):
    """Raised when the official URI is missing or not traceable to an official domain."""


def ensure_required_fields(payload: dict, fields: Iterable[str], *, context: str = "payload") -> None:
    missing = [field for field in fields if not payload.get(field)]
    if missing:
        raise NormattivaMetadataError(
            f"{context}: metadati mancanti o vuoti -> {', '.join(missing)}"
        )


def ensure_official_uri(uri: str) -> None:
    if not uri:
        raise NormattivaSourceUnverifiedError("URI ufficiale assente")

    parsed = urlparse(uri)
    domain = parsed.netloc.lower()
    if domain not in ALLOWED_SOURCE_DOMAINS:
        raise NormattivaSourceUnverifiedError(
            f"Dominio non ufficiale o non riconosciuto: {domain or '<vuoto>'}"
        )
