
from typing import Tuple, List


WRAPPER_MARKERS = [
    "Il Presidente della Repubblica",
    "emana il seguente decreto legislativo",
    "Visti gli articoli",
]


def classify_live_content(text: str) -> str:
    """
    Classifica il contenuto restituito dall'API live Normattiva.
    """

    if not text:
        return "EMPTY"

    for marker in WRAPPER_MARKERS:
        if marker in text:
            return "WRAPPER_ARTICLE"

    if len(text) < 80:
        return "TOO_SHORT"

    return "INNER_TEXT_ARTICLE"


class LiveInnerTextResolver:
    """Resolver che determina se il testo live è un wrapper o un vero articolo."""

    def resolve(self, text: str) -> Tuple[str, List[str]]:
        warnings = []

        content_kind = classify_live_content(text)

        if content_kind == "WRAPPER_ARTICLE":
            warnings.append("LIVE_WRAPPER_ONLY")

        if content_kind in ("EMPTY", "TOO_SHORT"):
            warnings.append("LIVE_INNER_TEXT_NOT_RESOLVED")

        return content_kind, warnings
