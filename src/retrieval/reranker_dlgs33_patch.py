from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Iterable


STOPWORDS_IT = {
    "a", "ad", "al", "allo", "ai", "agli", "all", "alla", "alle",
    "con", "col", "coi", "da", "dal", "dallo", "dai", "dagli", "dall",
    "dalla", "dalle", "di", "del", "dello", "dei", "degli", "dell",
    "della", "delle", "e", "ed", "in", "il", "lo", "la", "i", "gli",
    "le", "nel", "nello", "nei", "negli", "nell", "nella", "nelle",
    "o", "od", "per", "su", "sul", "sullo", "sui", "sugli", "sull",
    "sulla", "sulle", "tra", "fra", "un", "uno", "una",
}


@dataclass
class RetrievalCandidate:
    """
    Candidato documentale minimale per il reranking.
    Adatta i nomi campo del tuo progetto se il payload reale usa chiavi diverse.
    """

    retrieval_result_id: str
    atto_tipo: str = ""
    atto_numero: str = ""
    atto_anno: str = ""
    articolo: str = ""
    comma: str = ""
    rubrica: str = ""
    testo_unita: str = ""
    source_collection: str = ""
    score_lexical: float = 0.0
    score_vector: float = 0.0
    score_reranked: float = 0.0
    retrieval_reason: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class RerankerDLGS33Patch:
    """
    Reranker minimale con patch corpus-scoped per il D.Lgs. 33/2013.

    Obiettivi:
    - aumentare il peso lessicale della rubrica;
    - premiare i sintagmi normativi esatti;
    - impedire che l'art. 1 domini query specialistiche;
    - riconoscere alias normativi/istituzionali controllati (es. "amministrazione trasparente" -> art. 9);
    - non introdurre logiche decisorie o conclusive.
    """

    EXACT_RUBRICA_BOOST = 90.0
    RUBRICA_OVERLAP_MAX = 35.0
    EXACT_TEXT_BOOST = 20.0
    GENERIC_ART1_PENALTY = 70.0

    # Alias controllati: query nota -> articolo target -> boost
    # Patch minima e dichiarata, confinata al corpus D.Lgs. 33/2013.
    CONTROLLED_ALIAS_BOOSTS: dict[str, dict[str, float]] = {
        "amministrazione trasparente": {
            "9": 160.0,
        },
        "sezione amministrazione trasparente": {
            "9": 160.0,
        },
        "responsabile per la trasparenza": {
            "43": 120.0,
        },
    }

    WEIGHT_LEXICAL = 1.00
    WEIGHT_VECTOR = 1.00

    def rerank(self, query: str, candidates: Iterable[RetrievalCandidate]) -> list[RetrievalCandidate]:
        reranked: list[RetrievalCandidate] = []

        for item in candidates:
            base_score = self._base_hybrid_score(item)
            patch_components = self._dlgs33_patch_components(query=query, item=item)
            patch_delta = sum(patch_components.values())
            final_score = base_score + patch_delta

            cloned = RetrievalCandidate(**item.__dict__)
            cloned.score_reranked = final_score
            cloned.retrieval_reason = list(item.retrieval_reason or [])
            cloned.retrieval_reason.append(f"base_hybrid={base_score:.4f}")

            for key, value in patch_components.items():
                if value != 0:
                    cloned.retrieval_reason.append(f"{key}={value:.4f}")

            reranked.append(cloned)

        reranked.sort(key=lambda x: x.score_reranked, reverse=True)
        return reranked

    def _base_hybrid_score(self, item: RetrievalCandidate) -> float:
        return (
            (item.score_lexical or 0.0) * self.WEIGHT_LEXICAL
            + (item.score_vector or 0.0) * self.WEIGHT_VECTOR
        )

    def _dlgs33_patch_components(self, query: str, item: RetrievalCandidate) -> dict[str, float]:
        """
        Patch confinata al corpus D.Lgs. 33/2013.
        Nessun effetto sugli altri corpus.
        """
        if not self._is_dlgs33(item):
            return {
                "controlled_alias_boost": 0.0,
                "exact_rubrica_boost": 0.0,
                "rubrica_overlap_boost": 0.0,
                "exact_text_boost": 0.0,
                "generic_art1_penalty": 0.0,
            }

        rubrica = item.rubrica or ""
        testo = item.testo_unita or ""

        controlled_alias_boost = self._controlled_alias_boost(query, item)
        exact_rubrica_boost = self._exact_phrase_rubrica_boost(query, rubrica)
        rubrica_overlap_boost = self._rubrica_overlap_boost(query, rubrica)
        exact_text_boost = self._exact_phrase_text_boost(query, testo)
        generic_art1_penalty = -self._generic_art1_penalty(query, item)

        return {
            "controlled_alias_boost": controlled_alias_boost,
            "exact_rubrica_boost": exact_rubrica_boost,
            "rubrica_overlap_boost": rubrica_overlap_boost,
            "exact_text_boost": exact_text_boost,
            "generic_art1_penalty": generic_art1_penalty,
        }

    def _controlled_alias_boost(self, query: str, item: RetrievalCandidate) -> float:
        """
        Gestisce le query che non coincidono con la rubrica, ma rinviano in modo
        stabile e controllato a uno specifico articolo del D.Lgs. 33/2013.
        """
        q = self._norm(query)
        article = str(item.articolo or "").strip()

        if not q or not article:
            return 0.0

        article_boosts = self.CONTROLLED_ALIAS_BOOSTS.get(q)
        if not article_boosts:
            return 0.0

        return float(article_boosts.get(article, 0.0))

    def _is_dlgs33(self, item: RetrievalCandidate) -> bool:
        num = str(item.atto_numero or "").strip()
        anno = str(item.atto_anno or "").strip()
        coll = self._norm(item.source_collection or "")
        return (
            (num == "33" and anno == "2013")
            or ("dlgs33" in coll)
            or ("33 2013" in coll)
            or ("33_2013" in coll)
        )

    def _exact_phrase_rubrica_boost(self, query: str, rubrica: str) -> float:
        q = self._norm(query)
        r = self._norm(rubrica)
        if not q or not r:
            return 0.0

        # match esatto o sottostringa normativa piena
        if q == r or q in r:
            return self.EXACT_RUBRICA_BOOST

        # fallback prudente: tutti i token informativi della query presenti in rubrica
        q_tokens = self._content_tokens(q)
        if len(q_tokens) >= 2 and all(token in r for token in q_tokens):
            return self.EXACT_RUBRICA_BOOST / 2.0

        return 0.0

    def _rubrica_overlap_boost(self, query: str, rubrica: str) -> float:
        q = set(self._content_tokens(query))
        r = set(self._content_tokens(rubrica))
        if not q:
            return 0.0
        overlap_ratio = len(q & r) / len(q)
        return self.RUBRICA_OVERLAP_MAX * overlap_ratio

    def _exact_phrase_text_boost(self, query: str, text: str) -> float:
        q = self._norm(query)
        t = self._norm(text)
        if q and t and q in t:
            return self.EXACT_TEXT_BOOST
        return 0.0

    def _generic_art1_penalty(self, query: str, item: RetrievalCandidate) -> float:
        """
        Penalizzazione mirata all'art. 1 quando la query è specialistica e la rubrica
        dell'art. 1 non la intercetta realmente.
        """
        if str(item.articolo or "") != "1":
            return 0.0

        q_tokens = self._content_tokens(query)
        if len(q_tokens) < 2:
            return 0.0

        q = self._norm(query)
        r = self._norm(item.rubrica or "")

        # se la rubrica dell'art. 1 intercetta davvero la query, nessuna penalità
        if q and (q == r or q in r):
            return 0.0
        if q_tokens and all(token in r for token in q_tokens):
            return 0.0

        return self.GENERIC_ART1_PENALTY

    @staticmethod
    def _norm(s: str) -> str:
        s = (s or "").lower().strip()
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = re.sub(r"[^a-z0-9]+", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @classmethod
    def _content_tokens(cls, s: str) -> list[str]:
        return [tok for tok in cls._norm(s).split() if tok not in STOPWORDS_IT]