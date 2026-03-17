# Patch da integrare in src/live_api/live_inner_text_resolver.py

from dataclasses import dataclass
from typing import Optional, List

from .live_probe_matrix import build_probe_matrix
from .live_detail_classifier import DetailKind

WRAPPER_MARKERS = [
    "IL PRESIDENTE DELLA REPUBBLICA",
    "Emana",
    "È approvato l'unito testo unico",
    "il seguente decreto legislativo",
]

INNER_MARKERS = [
    "Il presente testo unico contiene",
]

def classify_html(html: str) -> DetailKind:
    if not html:
        return DetailKind.UNRESOLVED

    for marker in WRAPPER_MARKERS:
        if marker in html:
            return DetailKind.WRAPPER_ARTICLE

    for marker in INNER_MARKERS:
        if marker in html:
            return DetailKind.INNER_TEXT_ARTICLE

    return DetailKind.UNRESOLVED


@dataclass
class LiveResolutionResult:
    resolved_kind: DetailKind
    text: Optional[str]
    attempts: List[str]
    warnings: List[str]


class LiveInnerTextResolver:

    def __init__(self, detail_service):
        self.detail_service = detail_service

    def resolve_article(self, base_params: dict) -> LiveResolutionResult:
        attempts_log = []
        warnings = []

        probe_matrix = build_probe_matrix(base_params)

        for attempt in probe_matrix:
            params = attempt.params
            attempts_log.append(attempt.description)

            response = self.detail_service.get_article_detail(params)

            if not response:
                warnings.append("empty_response")
                continue

            html = response.get("articoloHtml", "") or response.get("testo", "")
            classification = classify_html(html)

            if classification == DetailKind.INNER_TEXT_ARTICLE:
                return LiveResolutionResult(
                    resolved_kind=DetailKind.INNER_TEXT_ARTICLE,
                    text=html,
                    attempts=attempts_log,
                    warnings=warnings,
                )

            if classification == DetailKind.WRAPPER_ARTICLE:
                warnings.append("wrapper_detected")

        return LiveResolutionResult(
            resolved_kind=DetailKind.UNRESOLVED,
            text=None,
            attempts=attempts_log,
            warnings=warnings,
        )
