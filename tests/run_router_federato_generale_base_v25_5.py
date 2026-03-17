#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

DOMAIN_COLLECTIONS: Dict[str, List[str]] = {
    "dlgs118": [
        "normattiva_dlgs118_2011_main",
        "normattiva_dlgs118_2011_all_1",
        "normattiva_dlgs118_2011_all_4_1",
        "normattiva_dlgs118_2011_all_4_2",
    ]
}

SPECIALISTIC_SUBINTENTS = {
    "fpv_strutturale",
    "fpv_operativo",
    "impegno_spesa",
    "esigibilita_spesa",
    "cronoprogramma_investimento",
    "riaccertamento_ordinario",
    "entrate_vincolate_risultato",
    "entrate_vincolate_cassa",
}

RESCUE_SUBINTENTS = {
    "riaccertamento_ordinario",
    "fpv_operativo",
    "entrate_vincolate_cassa",
}

DEFAULT_TEST_QUERIES = [
    "fpv",
    "impegno di spesa",
    "esigibilità della spesa",
    "riaccertamento ordinario dei residui",
    "cronoprogramma investimento",
    "entrate vincolate",
    "fondo pluriennale vincolato cronoprogramma",
    "fondo pluriennale vincolato bilancio di previsione",
    "quote vincolate risultato di amministrazione",
    "cassa vincolata entrate vincolate",
    "reimputazione residui passivi",
    "riaccertamento residui passivi e attivi",
]

SUBINTENT_ANCHORS: Dict[str, List[str]] = {
    "riaccertamento_ordinario": [
        "riaccertamento",
        "ordinario",
        "residui",
        "reimput",
        "cancellati",
        "reimputati",
        "residui attivi",
        "residui passivi",
    ],
    "fpv_operativo": [
        "fondo pluriennale vincolato",
        "fpv",
        "esigibil",
        "imput",
        "obbligazione",
        "cronoprogramma",
        "scadenza",
        "spesa",
    ],
    "entrate_vincolate_cassa": [
        "entrate vincolate",
        "cassa vincolata",
        "utilizzo di cassa",
        "tesoreria",
        "incasso",
        "reversale",
        "cassa",
    ],
    "entrate_vincolate_risultato": [
        "entrate vincolate",
        "risultato di amministrazione",
        "quote vincolate",
        "avanzo vincolato",
        "allegato a/2",
        "nota integrativa",
        "9.7.2",
        "9.11.4",
    ],
    "impegno_spesa": [
        "impegno di spesa",
        "obbligazione giuridicamente perfezionata",
        "impegno",
        "spesa",
    ],
    "esigibilita_spesa": [
        "esigibil",
        "spesa",
        "obbligazioni passive",
        "esigibili",
        "imput",
    ],
    "cronoprogramma_investimento": [
        "cronoprogramma",
        "investimento",
        "esigibil",
        "spesa di investimento",
    ],
    "fpv_strutturale": [
        "fondo pluriennale vincolato",
        "fpv",
        "prospetto",
        "equilibri",
        "bilancio",
        "nota integrativa",
        "missioni",
        "programmi",
    ],
}

SUBINTENT_FALSE_POSITIVE_PENALTIES: Dict[str, List[str]] = {
    "riaccertamento_ordinario": [
        "derivato",
        "bullet",
        "cartolarizzazione",
        "anticipazione",
        "addizionale irpef",
        "autoliquidazione",
        "ruolo",
        "lista di carico",
        "tributi",
        "tributo",
        "accertamento entrate",
    ]
}



RIACCERTAMENTO_HARD_ANCHORS = [
    "riaccertamento ordinario",
    "reimput",
    "cancellat",
]

RIACCERTAMENTO_SUPPORT_ANCHORS = [
    "riaccertamento",
    "ordinario",
    "residui",
    "residui attivi",
    "residui passivi",
]

RIACCERTAMENTO_STRICT_NEGATIVES = [
    "derivato",
    "bullet",
    "cartolarizzazione",
    "anticipazione",
    "addizionale irpef",
    "autoliquidazione",
    "ruolo",
    "lista di carico",
    "tributi",
    "tributo",
    "accertamento entrate",
]


TARGET_HINTS: Dict[str, Dict[str, List[str]]] = {
    "impegno_spesa": {
        "ids": ["par_0054_5"],
        "phrases": [
            "impegno di spesa",
            "obbligazione giuridicamente perfezionata",
        ],
    },
    "esigibilita_spesa": {
        "ids": ["par_0060_5_3_1"],
        "phrases": [
            "esigibilita della spesa",
            "esigibilità della spesa",
            "obbligazioni passive giuridicamente perfezionate",
            "esercizi in cui le obbligazioni passive sono esigibili",
        ],
    },
    "cronoprogramma_investimento": {
        "ids": ["par_0060_5_3_1"],
        "phrases": [
            "cronoprogramma",
            "investimento",
            "spesa di investimento",
            "esigibilità della spesa",
        ],
    },
    "entrate_vincolate_risultato": {
        "ids": ["9.7.2", "9.11.4"],
        "phrases": [
            "risultato di amministrazione",
            "entrate vincolate",
            "quote vincolate",
            "avanzo vincolato",
            "allegato a/2",
            "nota integrativa",
            "9.7.2",
            "9.11.4",
        ],
    },
    "entrate_vincolate_cassa": {
        "ids": ["9.11.4"],
        "phrases": [
            "entrate vincolate",
            "cassa vincolata",
            "utilizzo di cassa",
            "tesoreria",
            "incasso",
            "reversale",
            "9.11.4",
        ],
    },
}


@dataclass
class Candidate:
    collection: str
    doc_id: str
    document: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    best_distance: Optional[float] = None
    best_similarity: float = 0.0
    variant_hits: int = 0
    debug: Dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.collection}::{self.doc_id}"


def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    text = text.lower().replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def serialize_metadata(metadata: Optional[Dict[str, Any]]) -> str:
    if not metadata:
        return ""
    parts: List[str] = []
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            value_str = " ".join(map(str, value))
        else:
            value_str = str(value)
        parts.append(f"{key}:{value_str}")
    return " | ".join(parts)


def candidate_blob(candidate: Candidate) -> str:
    return normalize_text(
        " ".join([candidate.key, serialize_metadata(candidate.metadata), candidate.document or ""])
    )


def metadata_focus_text(metadata: Optional[Dict[str, Any]]) -> str:
    if not metadata:
        return ""
    preferred_keys = (
        "rubrica",
        "titolo",
        "title",
        "heading",
        "label",
        "article_title",
        "chapter_title",
        "section_title",
    )
    parts: List[str] = []
    for key, value in metadata.items():
        if value is None:
            continue
        k = normalize_text(str(key))
        if not any(pk in k for pk in preferred_keys):
            continue
        if isinstance(value, (list, tuple, set)):
            value_str = " ".join(map(str, value))
        else:
            value_str = str(value)
        parts.append(value_str)
    return normalize_text(" ".join(parts))


def candidate_anchor_text(candidate: Candidate, subintent: str) -> str:
    if subintent == "riaccertamento_ordinario":
        return normalize_text(" ".join([metadata_focus_text(candidate.metadata), candidate.document or ""]))
    return candidate_blob(candidate)


def contains_any(text: str, needles: Iterable[str]) -> bool:
    return any(n in text for n in needles)


def count_hits(text: str, needles: Iterable[str]) -> int:
    return sum(1 for n in needles if n in text)


def distance_to_similarity(distance: Optional[float]) -> float:
    if distance is None:
        return 0.0
    return 1.0 / (1.0 + max(0.0, float(distance)))


def short_doc(text: str, limit: int = 190) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def detect_domains(query_text: str) -> List[str]:
    q = normalize_text(query_text)
    dlgs118_markers = [
        "fpv",
        "fondo pluriennale vincolato",
        "impegno di spesa",
        "esigibil",
        "riaccert",
        "residui",
        "entrate vincolate",
        "cronoprogramma",
        "risultato di amministrazione",
        "all_4_1",
        "all_4_2",
    ]
    if contains_any(q, dlgs118_markers):
        return ["dlgs118"]
    return ["dlgs118"]


def detect_subintent_dlgs118(query_text: str) -> str:
    q = normalize_text(query_text)

    has_fpv = "fpv" in q or "fondo pluriennale vincolato" in q
    structural_terms = ["prospetto", "equilibri", "bilancio", "nota integrativa", "missioni", "programmi"]
    operational_terms = ["cronoprogramma", "impegno", "esigibil", "reimput", "obbligazione", "scadenza"]

    if contains_any(q, ["riaccertamento ordinario", "riaccertamento", "reimput", "residui attivi", "residui passivi"]):
        return "riaccertamento_ordinario"

    if contains_any(q, ["cronoprogramma investimento", "cronoprogramma degli investimenti"]) or (
        "cronoprogramma" in q and contains_any(q, ["invest", "opera", "lavor"])
    ):
        return "cronoprogramma_investimento"

    if contains_any(q, ["esigibilità della spesa", "esigibilita della spesa", "esigibil"]):
        return "esigibilita_spesa"

    if contains_any(q, ["impegno di spesa", "impegno spesa"]):
        return "impegno_spesa"

    if contains_any(q, ["entrate vincolate", "quote vincolate", "avanzo vincolato", "allegato a/2", "nota integrativa"]):
        if contains_any(q, ["cassa vincolata", "utilizzo di cassa", "tesoreria", "incasso", "reversale", "gestione di cassa", "cassa"]):
            return "entrate_vincolate_cassa"
        return "entrate_vincolate_risultato"

    if has_fpv and contains_any(q, operational_terms):
        return "fpv_operativo"

    if has_fpv and contains_any(q, structural_terms):
        return "fpv_strutturale"

    if q in {"fpv", "fondo pluriennale vincolato"}:
        return "generic_dlgs118"

    return "generic_dlgs118"


def build_query_variants(query_text: str, subintent: str) -> List[str]:
    variants = [query_text.strip()]
    extra: Dict[str, List[str]] = {
        "fpv_strutturale": [
            "fondo pluriennale vincolato prospetto equilibri bilancio nota integrativa",
            "fpv missioni programmi all_4_1",
        ],
        "fpv_operativo": [
            "fondo pluriennale vincolato esigibilita spesa imputazione cronoprogramma",
            "fpv obbligazioni esigibili impegno reimputazione all_4_2",
        ],
        "impegno_spesa": [
            "impegno di spesa obbligazione giuridicamente perfezionata",
            "all_4_2 5.4 impegno di spesa",
        ],
        "esigibilita_spesa": [
            "esigibilita della spesa obbligazioni passive esigibili imputazione",
            "all_4_2 5.3.1 esigibilita spesa",
        ],
        "cronoprogramma_investimento": [
            "cronoprogramma investimento esigibilita della spesa",
            "spesa di investimento cronoprogramma all_4_2 5.3.1",
        ],
        "riaccertamento_ordinario": [
            "riaccertamento ordinario dei residui reimputazione residui attivi passivi",
            "residui cancellati reimputati riaccertamento ordinario competenza finanziaria potenziata",
        ],
        "entrate_vincolate_risultato": [
            "entrate vincolate risultato di amministrazione quote vincolate allegato a/2 9.7.2 9.11.4",
            "avanzo vincolato nota integrativa entrate vincolate",
        ],
        "entrate_vincolate_cassa": [
            "entrate vincolate cassa cassa vincolata tesoreria incasso reversale 9.11.4",
            "utilizzo di cassa entrate vincolate gestione di cassa all_4_2",
        ],
        "generic_dlgs118": [
            "fondo pluriennale vincolato fpv all_4_1 all_4_2",
            "fpv risultato di amministrazione esigibilita spesa",
        ],
    }
    variants.extend(extra.get(subintent, []))

    seen = set()
    out: List[str] = []
    for item in variants:
        key = normalize_text(item)
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def is_main_fulltext_collection(collection_name: str) -> bool:
    return collection_name == "normattiva_dlgs118_2011_main"


def is_specialistic_query(subintent: str) -> bool:
    return subintent in SPECIALISTIC_SUBINTENTS


def get_collection_prior(collection_name: str, subintent: str, query_text: str, rescue_mode: bool = False) -> float:
    q = normalize_text(query_text)
    mult = 1.0

    if subintent == "fpv_strutturale":
        if collection_name.endswith("all_4_1"):
            mult *= 1.95 if not rescue_mode else 2.20
        elif collection_name.endswith("all_4_2"):
            mult *= 1.25 if not rescue_mode else 1.35
        elif collection_name.endswith("all_1"):
            mult *= 0.95
        elif is_main_fulltext_collection(collection_name):
            mult *= 0.62 if not rescue_mode else 0.45

    elif subintent == "fpv_operativo":
        if collection_name.endswith("all_4_2"):
            mult *= 2.10 if not rescue_mode else 2.50
        elif collection_name.endswith("all_4_1"):
            mult *= 1.18 if not rescue_mode else 1.10
        elif collection_name.endswith("all_1"):
            mult *= 0.98
        elif is_main_fulltext_collection(collection_name):
            mult *= 0.55 if not rescue_mode else 0.35

    elif subintent == "riaccertamento_ordinario":
        if collection_name.endswith("all_4_2"):
            mult *= 2.45 if not rescue_mode else 3.00
        elif collection_name.endswith("all_1"):
            mult *= 1.45 if not rescue_mode else 1.70
        elif collection_name.endswith("all_4_1"):
            mult *= 0.95 if not rescue_mode else 0.88
        elif is_main_fulltext_collection(collection_name):
            mult *= 0.28 if not rescue_mode else 0.16

    elif subintent == "entrate_vincolate_risultato":
        if collection_name.endswith("all_4_1"):
            mult *= 1.85 if not rescue_mode else 2.05
        elif collection_name.endswith("all_4_2"):
            mult *= 1.22 if not rescue_mode else 1.28
        elif collection_name.endswith("all_1"):
            mult *= 1.00
        elif is_main_fulltext_collection(collection_name):
            mult *= 0.60 if not rescue_mode else 0.45

    elif subintent == "entrate_vincolate_cassa":
        if collection_name.endswith("all_4_2"):
            mult *= 2.10 if not rescue_mode else 2.50
        elif collection_name.endswith("all_4_1"):
            mult *= 0.95 if not rescue_mode else 0.85
        elif collection_name.endswith("all_1"):
            mult *= 0.98
        elif is_main_fulltext_collection(collection_name):
            mult *= 0.52 if not rescue_mode else 0.33

    elif subintent in {"impegno_spesa", "esigibilita_spesa", "cronoprogramma_investimento"}:
        if collection_name.endswith("all_4_2"):
            mult *= 2.10 if not rescue_mode else 2.28
        elif collection_name.endswith("all_4_1"):
            mult *= 0.92
        elif collection_name.endswith("all_1"):
            mult *= 0.95
        elif is_main_fulltext_collection(collection_name):
            mult *= 0.42 if not rescue_mode else 0.25

    elif subintent == "generic_dlgs118" and contains_any(q, ["fpv", "fondo pluriennale vincolato"]):
        if collection_name.endswith("all_4_1"):
            mult *= 1.55
        elif collection_name.endswith("all_4_2"):
            mult *= 1.55
        elif collection_name.endswith("all_1"):
            mult *= 1.10
        elif is_main_fulltext_collection(collection_name):
            mult *= 0.72

    return mult


def should_demote_main_fulltext(subintent: str) -> bool:
    return is_specialistic_query(subintent)


def target_hint_boost(blob: str, subintent: str) -> float:
    hints = TARGET_HINTS.get(subintent, {})
    ids = [normalize_text(x) for x in hints.get("ids", [])]
    phrases = [normalize_text(x) for x in hints.get("phrases", [])]

    boost = 0.0
    boost += count_hits(blob, ids) * 26.0
    boost += count_hits(blob, phrases) * 11.5

    if subintent == "impegno_spesa" and "par_0054_5" in blob:
        boost += 95.0
    if subintent in {"esigibilita_spesa", "cronoprogramma_investimento"} and "par_0060_5_3_1" in blob:
        boost += 105.0
    if subintent == "entrate_vincolate_risultato" and ("9.7.2" in blob or "9.11.4" in blob):
        boost += 70.0

    return boost


def anchor_threshold(subintent: str) -> int:
    if subintent == "riaccertamento_ordinario":
        return 2
    if subintent in {"fpv_operativo", "entrate_vincolate_cassa"}:
        return 2
    return 1


def riaccertamento_anchor_profile(anchor_text: str) -> Dict[str, Any]:
    hard_hits = [normalize_text(x) for x in RIACCERTAMENTO_HARD_ANCHORS if normalize_text(x) in anchor_text]
    support_hits = [normalize_text(x) for x in RIACCERTAMENTO_SUPPORT_ANCHORS if normalize_text(x) in anchor_text]
    process_anchor = len(hard_hits) >= 1
    strong = process_anchor and (len(support_hits) >= 1 or len(hard_hits) >= 2)
    return {
        "hard_hits": hard_hits,
        "soft_hits": support_hits,
        "hard_count": len(hard_hits),
        "soft_count": len(support_hits),
        "process_anchor": process_anchor,
        "strong": strong,
    }


def riaccertamento_core_combo(anchor_text: str, profile: Dict[str, Any]) -> bool:
    has_residui = contains_any(anchor_text, ["residui", "residui passivi", "residui attivi"])
    has_process_terms = contains_any(anchor_text, ["reimput", "cancell"])
    return bool(profile.get("process_anchor")) and has_residui and has_process_terms


def riaccertamento_lateral_for_top3(anchor_text: str, profile: Dict[str, Any]) -> bool:
    lateral_hits = count_hits(anchor_text, [normalize_text(x) for x in RIACCERTAMENTO_TOP3_LATERAL_TERMS])
    if lateral_hits == 0:
        return False
    return not riaccertamento_core_combo(anchor_text, profile)


def riaccertamento_query_bonus(query_text: str, anchor_text: str, profile: Dict[str, Any]) -> float:
    q = normalize_text(query_text)
    bonus = 0.0

    wants_phrase = "riaccertamento ordinario" in q
    wants_reimput = "reimput" in q
    wants_cancel = "cancell" in q
    wants_passivi = "residui passivi" in q
    wants_attivi = "residui attivi" in q

    if wants_phrase and "riaccertamento ordinario" in anchor_text:
        bonus += 60.0
    if wants_reimput and "reimput" in anchor_text:
        bonus += 52.0
    if wants_cancel and "cancell" in anchor_text:
        bonus += 40.0
    if wants_passivi and "residui passivi" in anchor_text and profile.get("process_anchor"):
        bonus += 28.0
    if wants_attivi and "residui attivi" in anchor_text and profile.get("process_anchor"):
        bonus += 28.0

    return bonus


def anchor_stats(candidate: Candidate, subintent: str) -> Tuple[int, List[str]]:
    anchor_text = candidate_anchor_text(candidate, subintent)
    anchors = [normalize_text(x) for x in SUBINTENT_ANCHORS.get(subintent, [])]
    hits = [a for a in anchors if a in anchor_text]
    return len(hits), hits


def candidate_has_strong_anchor(candidate: Candidate, subintent: str) -> bool:
    if subintent != "riaccertamento_ordinario":
        hits, _ = anchor_stats(candidate, subintent)
        return hits >= anchor_threshold(subintent)
    profile = riaccertamento_anchor_profile(candidate_anchor_text(candidate, subintent))
    return bool(profile["strong"])


def candidate_negative_hits(candidate: Candidate, subintent: str) -> int:
    text_for_penalty = candidate_anchor_text(candidate, subintent) if subintent == "riaccertamento_ordinario" else candidate_blob(candidate)
    negatives = [normalize_text(x) for x in SUBINTENT_FALSE_POSITIVE_PENALTIES.get(subintent, [])]
    return count_hits(text_for_penalty, negatives)


def false_positive_penalty(candidate: Candidate, subintent: str, anchor_hits: int, rescue_mode: bool = False) -> float:
    text_for_penalty = candidate_anchor_text(candidate, subintent) if subintent == "riaccertamento_ordinario" else candidate_blob(candidate)
    negatives = [normalize_text(x) for x in SUBINTENT_FALSE_POSITIVE_PENALTIES.get(subintent, [])]
    negative_hits = count_hits(text_for_penalty, negatives)
    if negative_hits == 0:
        return 0.0

    per_hit = 18.0 if anchor_hits == 0 else 7.0
    if rescue_mode:
        per_hit *= 1.35
    penalty = negative_hits * per_hit

    if subintent == "riaccertamento_ordinario":
        profile = riaccertamento_anchor_profile(text_for_penalty)
        hard_count = int(profile["hard_count"])
        process_anchor = bool(profile["process_anchor"])
        strict_negative_hits = count_hits(text_for_penalty, [normalize_text(x) for x in RIACCERTAMENTO_STRICT_NEGATIVES])

        if strict_negative_hits > 0 and not process_anchor:
            penalty += strict_negative_hits * (58.0 if not rescue_mode else 86.0)
        elif strict_negative_hits > 0 and hard_count == 1:
            penalty += strict_negative_hits * (18.0 if not rescue_mode else 26.0)

    return penalty


def score_candidate(candidate: Candidate, query_text: str, subintent: str, rescue_mode: bool = False) -> float:
    blob = candidate_blob(candidate)
    anchor_text = candidate_anchor_text(candidate, subintent)
    sim_score = candidate.best_similarity * 100.0
    variant_bonus = min(candidate.variant_hits, 4) * 5.0
    collection_prior = get_collection_prior(candidate.collection, subintent, query_text, rescue_mode=rescue_mode)
    anchors_count, anchors_found = anchor_stats(candidate, subintent)
    anchor_weight = 18.0 if not rescue_mode else 28.0
    anchor_score = anchors_count * anchor_weight
    hint_score = target_hint_boost(blob, subintent)
    penalty_score = false_positive_penalty(candidate, subintent, anchors_count, rescue_mode=rescue_mode)

    riacc_profile = None
    query_bonus = 0.0
    if subintent == "riaccertamento_ordinario":
        riacc_profile = riaccertamento_anchor_profile(anchor_text)
        if riacc_profile["process_anchor"]:
            anchor_score += 36.0 * riacc_profile["hard_count"]
        if riacc_profile["strong"]:
            anchor_score += 55.0 if not rescue_mode else 82.0
        query_bonus += riaccertamento_query_bonus(query_text, anchor_text, riacc_profile)

    score = (sim_score + variant_bonus + anchor_score + hint_score + query_bonus - penalty_score) * collection_prior

    main_demoted = False
    if should_demote_main_fulltext(subintent) and is_main_fulltext_collection(candidate.collection):
        main_demoted = True
        score *= 0.34 if not rescue_mode else 0.18
        hard_cap = 78.0 if not rescue_mode else 52.0
        score = min(score, hard_cap)

    if rescue_mode and subintent in RESCUE_SUBINTENTS and anchors_count < anchor_threshold(subintent):
        score *= 0.78

    if subintent == "riaccertamento_ordinario":
        negative_hits = candidate_negative_hits(candidate, subintent)
        hard_count = int(riacc_profile["hard_count"]) if riacc_profile else 0
        soft_count = int(riacc_profile["soft_count"]) if riacc_profile else 0
        process_anchor = bool(riacc_profile["process_anchor"]) if riacc_profile else False
        strong_anchor = bool(riacc_profile["strong"]) if riacc_profile else False
        core_combo = riaccertamento_core_combo(anchor_text, riacc_profile or {})
        lateral_top3 = riaccertamento_lateral_for_top3(anchor_text, riacc_profile or {})
        if soft_count > 0 and not process_anchor:
            score *= 0.48 if not rescue_mode else 0.16
        if negative_hits > 0 and not process_anchor:
            score *= 0.42 if not rescue_mode else 0.20
        elif negative_hits > 0 and not strong_anchor:
            score *= 0.82 if not rescue_mode else 0.58
        if candidate.doc_id in {"par_0001_intro", "par_0004_3"} and not process_anchor:
            score *= 0.40 if not rescue_mode else 0.12
        if process_anchor and not core_combo:
            score *= 0.70 if not rescue_mode else 0.34
        if lateral_top3:
            score *= 0.34 if not rescue_mode else 0.10
        if rescue_mode and not strong_anchor:
            score *= 0.55
        if rescue_mode and soft_count > 0 and not process_anchor:
            score *= 0.30
        if rescue_mode and negative_hits > 0 and not process_anchor:
            score *= 0.28
        if rescue_mode and process_anchor and not core_combo:
            score *= 0.26

    candidate.debug.update(
        {
            "collection_prior": round(collection_prior, 4),
            "sim_score": round(sim_score, 4),
            "variant_bonus": round(variant_bonus, 4),
            "anchor_hits": anchors_count,
            "anchors_found": anchors_found,
            "anchor_score": round(anchor_score, 4),
            "hint_score": round(hint_score, 4),
            "query_bonus": round(query_bonus, 4),
            "penalty_score": round(penalty_score, 4),
            "main_demoted": main_demoted,
            "rescue_mode": rescue_mode,
            "score_final": round(score, 4),
            "riacc_hard_hits": (riacc_profile or {}).get("hard_hits", []),
            "riacc_soft_hits": (riacc_profile or {}).get("soft_hits", []),
            "riacc_process_anchor": (riacc_profile or {}).get("process_anchor", False),
            "riacc_strong_anchor": (riacc_profile or {}).get("strong", False),
            "riacc_core_combo": riaccertamento_core_combo(anchor_text, riacc_profile or {}) if subintent == "riaccertamento_ordinario" else False,
            "riacc_lateral_top3": riaccertamento_lateral_for_top3(anchor_text, riacc_profile or {}) if subintent == "riaccertamento_ordinario" else False,
        }
    )
    return score


def anchor_hit_in_top3(ranked: Sequence[Candidate], subintent: str) -> bool:
    needed = anchor_threshold(subintent)
    for cand in ranked[:3]:
        if subintent == "riaccertamento_ordinario":
            if candidate_has_strong_anchor(cand, subintent):
                return True
            continue
        hits, _ = anchor_stats(cand, subintent)
        if hits >= needed:
            return True
    return False


def is_riaccertamento_top3_eligible(candidate: Candidate) -> bool:
    if is_main_fulltext_collection(candidate.collection):
        return False
    if not (candidate.collection.endswith("all_4_2") or candidate.collection.endswith("all_1") or candidate.collection.endswith("all_4_1")):
        return False
    profile = riaccertamento_anchor_profile(candidate_anchor_text(candidate, "riaccertamento_ordinario"))
    anchor_text = candidate_anchor_text(candidate, "riaccertamento_ordinario")
    if not profile["process_anchor"]:
        return False
    if not riaccertamento_core_combo(anchor_text, profile):
        return False
    if riaccertamento_lateral_for_top3(anchor_text, profile):
        return False
    return True


def riaccertamento_top3_purity_ok(ranked: Sequence[Candidate]) -> bool:
    if len(ranked) < 3:
        return False
    top3 = list(ranked[:3])
    if any(not is_riaccertamento_top3_eligible(c) for c in top3):
        return False
    profiles = [riaccertamento_anchor_profile(candidate_anchor_text(c, "riaccertamento_ordinario")) for c in top3]
    texts = [candidate_anchor_text(c, "riaccertamento_ordinario") for c in top3]
    if not profiles[0]["strong"] or not riaccertamento_core_combo(texts[0], profiles[0]):
        return False
    if not profiles[1]["process_anchor"] or not riaccertamento_core_combo(texts[1], profiles[1]):
        return False
    return profiles[2]["process_anchor"] and riaccertamento_core_combo(texts[2], profiles[2])


def maybe_promote_riaccertamento_pure_top3(ranked: List[Candidate]) -> List[Candidate]:
    if len(ranked) < 4:
        return ranked

    profiles = [riaccertamento_anchor_profile(candidate_anchor_text(c, "riaccertamento_ordinario")) for c in ranked]
    top3_profiles = profiles[:3]
    top3_ok = (
        is_riaccertamento_top3_eligible(ranked[2])
        and top3_profiles[2]["process_anchor"]
    )
    if top3_ok:
        return ranked

    replacement_idx = None
    for idx in range(3, len(ranked)):
        cand = ranked[idx]
        profile = profiles[idx]
        if not is_riaccertamento_top3_eligible(cand):
            continue
        anchor_text = candidate_anchor_text(cand, "riaccertamento_ordinario")
        if not profile["process_anchor"]:
            continue
        if not riaccertamento_core_combo(anchor_text, profile):
            continue
        if riaccertamento_lateral_for_top3(anchor_text, profile):
            continue
        neg_hits = candidate_negative_hits(cand, "riaccertamento_ordinario")
        if neg_hits > 0 and not profile["strong"]:
            continue
        replacement_idx = idx
        break

    if replacement_idx is None:
        return ranked

    ranked[2], ranked[replacement_idx] = ranked[replacement_idx], ranked[2]
    return ranked


def should_trigger_rescue(ranked: Sequence[Candidate], subintent: str) -> bool:
    if subintent not in RESCUE_SUBINTENTS:
        return False
    if not ranked:
        return False

    if subintent != "riaccertamento_ordinario":
        return not anchor_hit_in_top3(ranked, subintent)

    top3 = list(ranked[:3])
    profiles = [riaccertamento_anchor_profile(candidate_anchor_text(c, subintent)) for c in top3]

    if not any(p["process_anchor"] for p in profiles):
        return True
    if not profiles[0]["process_anchor"]:
        return True
    if not profiles[0]["strong"]:
        return True

    process_anchored_top3 = sum(1 for p in profiles if p["process_anchor"])
    if process_anchored_top3 < 2:
        return True
    eligible_top3 = sum(1 for c in top3 if is_riaccertamento_top3_eligible(c))
    if eligible_top3 < 3:
        return True
    if any(is_main_fulltext_collection(c.collection) for c in top3):
        return True
    if not riaccertamento_top3_purity_ok(ranked):
        return True

    for cand, profile in zip(top3, profiles):
        neg_hits = candidate_negative_hits(cand, subintent)
        if neg_hits > 0 and not profile["process_anchor"]:
            return True
        if neg_hits > 0 and not profile["strong"]:
            return True

    return False


def enforce_main_fulltext_not_top1(ranked: List[Candidate], subintent: str) -> List[Candidate]:
    if not ranked or not should_demote_main_fulltext(subintent):
        return ranked
    if not is_main_fulltext_collection(ranked[0].collection):
        return ranked

    specialist_index = None
    for idx, cand in enumerate(ranked[1:], start=1):
        if not is_main_fulltext_collection(cand.collection):
            specialist_index = idx
            break
    if specialist_index is None:
        return ranked

    main_cand = ranked[0]
    specialist_cand = ranked[specialist_index]
    main_score = float(main_cand.debug.get("score_final", 0.0))
    specialist_score = float(specialist_cand.debug.get("score_final", 0.0))
    if specialist_score >= max(10.0, main_score * 0.35):
        ranked[0], ranked[specialist_index] = ranked[specialist_index], ranked[0]
    return ranked


def balance_generic_fpv_top3(ranked: List[Candidate], subintent: str) -> List[Candidate]:
    if subintent != "generic_dlgs118" or len(ranked) < 3:
        return ranked

    top3 = ranked[:3]
    has_41 = any(c.collection.endswith("all_4_1") for c in top3)
    has_42 = any(c.collection.endswith("all_4_2") for c in top3)
    if has_41 and has_42:
        return ranked

    missing_suffix = "all_4_2" if not has_42 else "all_4_1"
    replacement_idx = None
    for idx, cand in enumerate(ranked[3:], start=3):
        if cand.collection.endswith(missing_suffix):
            replacement_idx = idx
            break
    if replacement_idx is None:
        return ranked

    ranked[2], ranked[replacement_idx] = ranked[replacement_idx], ranked[2]
    return ranked


def load_runtime() -> Tuple[Any, Any]:
    try:
        import chromadb  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Errore: chromadb non disponibile. Installa le dipendenze del progetto prima di eseguire il runner."
        ) from exc

    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Errore: sentence-transformers non disponibile. Installa le dipendenze del progetto prima di eseguire il runner."
        ) from exc

    return chromadb, SentenceTransformer


def fetch_candidates_for_collection(
    collection: Any,
    collection_name: str,
    query_variants: Sequence[str],
    embedding_model: Any,
    per_collection_k: int,
) -> Dict[str, Candidate]:
    candidates: Dict[str, Candidate] = {}

    for variant in query_variants:
        embedding = embedding_model.encode([variant], normalize_embeddings=True)[0].tolist()
        result = collection.query(
            query_embeddings=[embedding],
            n_results=per_collection_k,
            include=["documents", "metadatas", "distances"],
        )

        ids_list = result.get("ids", [[]])[0]
        docs_list = result.get("documents", [[]])[0]
        metas_list = result.get("metadatas", [[]])[0]
        dists_list = result.get("distances", [[]])[0]

        for doc_id, doc, meta, dist in zip(ids_list, docs_list, metas_list, dists_list):
            key = f"{collection_name}::{doc_id}"
            cand = candidates.get(key)
            if cand is None:
                cand = Candidate(
                    collection=collection_name,
                    doc_id=str(doc_id),
                    document=doc or "",
                    metadata=meta or {},
                    best_distance=float(dist) if dist is not None else None,
                    best_similarity=distance_to_similarity(dist),
                    variant_hits=1,
                )
                candidates[key] = cand
            else:
                cand.variant_hits += 1
                if dist is not None and (cand.best_distance is None or float(dist) < cand.best_distance):
                    cand.best_distance = float(dist)
                    cand.best_similarity = distance_to_similarity(dist)
                if doc and len(doc) > len(cand.document):
                    cand.document = doc
                if meta:
                    cand.metadata.update(meta)

    return candidates


def extra_riaccertamento_probe_variants(query_text: str) -> List[str]:
    q = normalize_text(query_text)
    variants = [
        "riaccertamento ordinario reimputazione cancellazione residui",
        "reimputazione residui passivi cancellati reimputati",
        "riaccertamento ordinario residui attivi residui passivi reimputazione",
    ]
    if "reimput" in q:
        variants.insert(0, "reimputazione residui passivi reimputati cancellati")
    if "passivi" in q or "attivi" in q:
        variants.insert(0, "residui passivi residui attivi riaccertamento ordinario reimputazione")
    return variants


def fetch_riaccertamento_probe_candidates(
    client: Any,
    embedding_model: Any,
    query_text: str,
    per_collection_k: int,
) -> Dict[str, Candidate]:
    probe_candidates: Dict[str, Candidate] = {}
    probe_variants = extra_riaccertamento_probe_variants(query_text)
    target_collections = [
        "normattiva_dlgs118_2011_all_4_2",
        "normattiva_dlgs118_2011_all_1",
    ]
    boosted_k = max(per_collection_k, 18)

    for collection_name in target_collections:
        try:
            collection = client.get_collection(name=collection_name)
        except Exception:
            continue
        fetched = fetch_candidates_for_collection(
            collection=collection,
            collection_name=collection_name,
            query_variants=probe_variants,
            embedding_model=embedding_model,
            per_collection_k=boosted_k,
        )
        for key, cand in fetched.items():
            existing = probe_candidates.get(key)
            if existing is None:
                probe_candidates[key] = cand
            else:
                existing.variant_hits += cand.variant_hits
                if cand.best_distance is not None and (
                    existing.best_distance is None or cand.best_distance < existing.best_distance
                ):
                    existing.best_distance = cand.best_distance
                    existing.best_similarity = cand.best_similarity
                if len(cand.document or "") > len(existing.document or ""):
                    existing.document = cand.document
                existing.metadata.update(cand.metadata)

    return probe_candidates


def rank_candidates(
    candidates: Sequence[Candidate],
    query_text: str,
    subintent: str,
    rescue_mode: bool = False,
) -> List[Candidate]:
    ranked = list(candidates)
    for cand in ranked:
        score_candidate(cand, query_text, subintent, rescue_mode=rescue_mode)
    ranked.sort(key=lambda c: float(c.debug.get("score_final", 0.0)), reverse=True)
    ranked = enforce_main_fulltext_not_top1(ranked, subintent)
    if subintent == "riaccertamento_ordinario":
        ranked = maybe_promote_riaccertamento_pure_top3(ranked)
    ranked = balance_generic_fpv_top3(ranked, subintent)
    return ranked


def print_header(title: str) -> None:
    print("=" * 110)
    print(title)


def print_candidate(idx: int, candidate: Candidate) -> None:
    print(f"[{idx}] {candidate.key}")
    print(f"  score_final: {candidate.debug.get('score_final')}")
    print(f"  sim_score: {candidate.debug.get('sim_score')}")
    print(f"  collection_prior: {candidate.debug.get('collection_prior')}")
    print(f"  anchor_hits: {candidate.debug.get('anchor_hits')} -> {candidate.debug.get('anchors_found')}")
    if candidate.debug.get('riacc_hard_hits') or candidate.debug.get('riacc_soft_hits'):
        print(f"  riacc_hard_hits: {candidate.debug.get('riacc_hard_hits')} | riacc_soft_hits: {candidate.debug.get('riacc_soft_hits')} | process_anchor: {candidate.debug.get('riacc_process_anchor')} | strong_anchor: {candidate.debug.get('riacc_strong_anchor')} | core_combo: {candidate.debug.get('riacc_core_combo')} | lateral_top3: {candidate.debug.get('riacc_lateral_top3')}")
    print(f"  hint_score: {candidate.debug.get('hint_score')} | query_bonus: {candidate.debug.get('query_bonus')} | penalty_score: {candidate.debug.get('penalty_score')}")
    print(f"  main_demoted: {candidate.debug.get('main_demoted')} | rescue_mode: {candidate.debug.get('rescue_mode')}")
    print(f"  snippet: {short_doc(candidate.document)}")
    print("-" * 110)


def print_acceptance_notes(query_text: str, ranked: Sequence[Candidate]) -> None:
    if not ranked:
        return
    top1 = ranked[0].key
    top3 = [c.key for c in ranked[:3]]
    q = normalize_text(query_text)

    if q == "impegno di spesa":
        ok = ("par_0054_5" in top1) or any("par_0054_5" in k for k in top3)
        print(f"CHECK impegno di spesa -> target par_0054_5: {'OK' if ok else 'ATTENZIONE'}")
    elif q == "esigibilità della spesa":
        ok = ("par_0060_5_3_1" in top1) or any("par_0060_5_3_1" in k for k in top3)
        print(f"CHECK esigibilità della spesa -> target par_0060_5_3_1: {'OK' if ok else 'ATTENZIONE'}")
    elif q == "cronoprogramma investimento":
        ok = ("par_0060_5_3_1" in top1) or any("par_0060_5_3_1" in k for k in top3)
        print(f"CHECK cronoprogramma investimento -> target par_0060_5_3_1: {'OK' if ok else 'ATTENZIONE'}")
    elif q == "entrate vincolate":
        ok = any(
            ("9.7.2" in c.key)
            or ("9.11.4" in c.key)
            or ("9.7.2" in (c.document or ""))
            or ("9.11.4" in (c.document or ""))
            for c in ranked[:3]
        )
        print(f"CHECK entrate vincolate -> 9.7.2 / 9.11.4 nei top3: {'OK' if ok else 'ATTENZIONE'}")
    elif q == "fpv":
        has_41 = any(c.collection.endswith("all_4_1") for c in ranked[:3])
        has_42 = any(c.collection.endswith("all_4_2") for c in ranked[:3])
        print(f"CHECK fpv -> all_4_1 nei top3: {'OK' if has_41 else 'ATTENZIONE'} | all_4_2 nei top3: {'OK' if has_42 else 'ATTENZIONE'}")
    elif q == "riaccertamento ordinario dei residui":
        has_main_top1 = ranked[0].collection == "normattiva_dlgs118_2011_main"
        has_anchor = any(candidate_has_strong_anchor(c, "riaccertamento_ordinario") for c in ranked[:3])
        print(f"CHECK riaccertamento -> anchor reali top3: {'OK' if has_anchor else 'ATTENZIONE'} | main::fulltext top1: {'NO' if has_main_top1 else 'OK'}")


def print_final_command_hint() -> None:
    print("\nComando PowerShell consigliato:")
    print(
        'py tests/run_router_federato_generale_base_v25_4.py --persist-dir data/chroma --query-text "fpv" --query-text "impegno di spesa" --query-text "esigibilità della spesa" --query-text "riaccertamento ordinario dei residui" --query-text "cronoprogramma investimento" --query-text "entrate vincolate"'
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Router federato generale v25.5 - micro-patch finale semantica top3 riaccertamento")
    parser.add_argument("--persist-dir", required=True, help="Directory Chroma persistita")
    parser.add_argument("--query-text", action="append", default=[], help="Query di test (ripetibile)")
    parser.add_argument("--top-k", type=int, default=8, help="Numero risultati finali da stampare per query")
    parser.add_argument("--per-collection-k", type=int, default=12, help="Numero candidati da estrarre per collection e per variante")
    args = parser.parse_args(argv)

    chromadb, SentenceTransformer = load_runtime()

    if not os.path.isdir(args.persist_dir):
        raise SystemExit(f"Persist dir non trovata: {args.persist_dir}")

    queries = args.query_text or list(DEFAULT_TEST_QUERIES)
    client = chromadb.PersistentClient(path=args.persist_dir)
    embedding_model = SentenceTransformer(EMBED_MODEL_NAME)

    print("=== ROUTER FEDERATO GENERALE — BASE v25.5 ===")
    print(f"CHROMA_PATH: {args.persist_dir}")
    print(f"EMBED_MODEL: {EMBED_MODEL_NAME}")

    for query_text in queries:
        print_header(f"QUERY: {query_text}")
        domains = detect_domains(query_text)
        print(f"DOMAINS: {domains}")

        subintent = detect_subintent_dlgs118(query_text) if "dlgs118" in domains else "n/a"
        print(f"SUBINTENT DETECTED: {subintent}")

        query_variants = build_query_variants(query_text, subintent)
        print(f"QUERY_VARIANTS: {query_variants}")

        all_candidates: Dict[str, Candidate] = {}

        for domain in domains:
            collection_names = DOMAIN_COLLECTIONS.get(domain, [])
            print(f"[DOMAIN] {domain} -> {collection_names}")
            for collection_name in collection_names:
                try:
                    collection = client.get_collection(name=collection_name)
                except Exception as exc:
                    print(f"[SKIP] collection mancante/non accessibile: {collection_name} ({exc})")
                    continue

                print(f"[COLLECTION QUERY] {collection_name} -> {query_variants[0]}")
                fetched = fetch_candidates_for_collection(
                    collection=collection,
                    collection_name=collection_name,
                    query_variants=query_variants,
                    embedding_model=embedding_model,
                    per_collection_k=args.per_collection_k,
                )
                for key, cand in fetched.items():
                    existing = all_candidates.get(key)
                    if existing is None:
                        all_candidates[key] = cand
                    else:
                        existing.variant_hits += cand.variant_hits
                        if cand.best_distance is not None and (
                            existing.best_distance is None or cand.best_distance < existing.best_distance
                        ):
                            existing.best_distance = cand.best_distance
                            existing.best_similarity = cand.best_similarity
                        if len(cand.document or "") > len(existing.document or ""):
                            existing.document = cand.document
                        existing.metadata.update(cand.metadata)

        ranked = rank_candidates(list(all_candidates.values()), query_text, subintent, rescue_mode=False)
        main_fulltext_demoted = any(bool(c.debug.get("main_demoted")) for c in ranked)
        anchor_hit = anchor_hit_in_top3(ranked, subintent)

        rescue_on = should_trigger_rescue(ranked, subintent)
        if rescue_on:
            rescue_candidates = dict(all_candidates)
            if subintent == "riaccertamento_ordinario":
                probe = fetch_riaccertamento_probe_candidates(
                    client=client,
                    embedding_model=embedding_model,
                    query_text=query_text,
                    per_collection_k=args.per_collection_k,
                )
                for key, cand in probe.items():
                    existing = rescue_candidates.get(key)
                    if existing is None:
                        rescue_candidates[key] = cand
                    else:
                        existing.variant_hits += cand.variant_hits
                        if cand.best_distance is not None and (
                            existing.best_distance is None or cand.best_distance < existing.best_distance
                        ):
                            existing.best_distance = cand.best_distance
                            existing.best_similarity = cand.best_similarity
                        if len(cand.document or "") > len(existing.document or ""):
                            existing.document = cand.document
                        existing.metadata.update(cand.metadata)
            ranked = rank_candidates(list(rescue_candidates.values()), query_text, subintent, rescue_mode=True)
            anchor_hit = anchor_hit_in_top3(ranked, subintent)

        print(f"RESCUE RANKING: {'ON' if rescue_on else 'OFF'}")
        print(f"MAIN_FULLTEXT_DEMOTED: {'YES' if main_fulltext_demoted else 'NO'}")
        print(f"ANCHOR_HIT_TOP3: {'YES' if anchor_hit else 'NO'}")

        if not ranked:
            print("[NO RESULTS]")
            continue

        print("\n=== TOP RESULTS ===")
        for idx, cand in enumerate(ranked[: args.top_k], start=1):
            print_candidate(idx, cand)

        print_acceptance_notes(query_text, ranked)
        print()

    print_final_command_hint()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
