from enum import Enum
from dataclasses import dataclass
from typing import Optional

class DetailKind(str, Enum):
    WRAPPER_ARTICLE = "WRAPPER_ARTICLE"
    INNER_TEXT_ARTICLE = "INNER_TEXT_ARTICLE"
    UNRESOLVED = "UNRESOLVED"

@dataclass
class DetailClassification:
    kind: DetailKind
    reason: str
    text_preview: Optional[str] = None

WRAPPER_MARKERS = [
    "È approvato l'unito testo unico",
    "È approvato il testo unico",
    "unito testo unico",
]

INNER_TEXT_MARKERS = [
    "Il presente testo unico",
    "principi e le disposizioni",
    "ordinamento degli enti locali",
]

def classify_detail_text(text: str) -> DetailClassification:

    if not text:
        return DetailClassification(
            kind=DetailKind.UNRESOLVED,
            reason="empty_text",
        )

    normalized = text.lower()

    for marker in WRAPPER_MARKERS:
        if marker.lower() in normalized:
            return DetailClassification(
                kind=DetailKind.WRAPPER_ARTICLE,
                reason="wrapper_marker_detected",
                text_preview=text[:120],
            )

    for marker in INNER_TEXT_MARKERS:
        if marker.lower() in normalized:
            return DetailClassification(
                kind=DetailKind.INNER_TEXT_ARTICLE,
                reason="inner_text_marker_detected",
                text_preview=text[:120],
            )

    return DetailClassification(
        kind=DetailKind.UNRESOLVED,
        reason="no_known_markers",
        text_preview=text[:120],
    )
