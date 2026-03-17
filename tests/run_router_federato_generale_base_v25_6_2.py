#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ROUTER FEDERATO GENERALE — BASE v25.6.2

Obiettivo della v25.6.2:
1) riaccertamento_top3_guard():
   - esclude dal top3 operativo il fulltext main e gli intro chunk quando esistono
     almeno 2 chunk realmente operativi sul riaccertamento.
2) fpv_operativo_structural_bonus():
   - riporta in testa i paragrafi 5.3 / 5.3.1 / 5.3.2 dell'All. 4/2
     per query FPV operative (cronoprogramma / esigibilità / imputazione).
3) cassa_vincolata_strict_pairing():
   - riconosce la vera "cassa vincolata" solo con co-occorrenze strette,
     evitando contaminazioni da "vincolata" usato in altri sensi.

Nota:
- file completo sostitutivo
- mantiene CLI semplice
- stampa log diagnostici leggibili
"""

from __future__ import annotations

import argparse
import math
import re
import sys
import traceback
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import chromadb
from sentence_transformers import SentenceTransformer


# ==================================================================================================
# CONFIG
# ==================================================================================================

EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

DOMAIN_COLLECTIONS: Dict[str, List[str]] = {
    "dlgs118": [
        "normattiva_dlgs118_2011_main",
        "normattiva_dlgs118_2011_all_1",
        "normattiva_dlgs118_2011_all_4_1",
        "normattiva_dlgs118_2011_all_4_2",
    ]
}

SUBINTENT_GENERIC = "generic_dlgs118"
SUBINTENT_IMPEGNO = "impegno_spesa"
SUBINTENT_ESIGIBILITA = "esigibilita_spesa"
SUBINTENT_RIACCERTAMENTO = "riaccertamento_ordinario"
SUBINTENT_CRONO = "cronoprogramma_investimento"
SUBINTENT_ENTRATE_VINCOLATE_RIS = "entrate_vincolate_risultato"
SUBINTENT_FPV_OPERATIVO = "fpv_operativo"
SUBINTENT_FPV_STRUTTURALE = "fpv_strutturale"
SUBINTENT_ENTRATE_VINCOLATE_CASSA = "entrate_vincolate_cassa"

RIACCERTAMENTO_SOFT_TERMS = [
    "riaccertamento",
    "ordinario",
    "residui",
    "residui attivi",
    "residui passivi",
]
RIACCERTAMENTO_HARD_TERMS = [
    "reimput",
    "cancellat",
]
RIACCERTAMENTO_TOP3_LATERAL_TERMS = [
    "rateizzazione",
    "rateizz",
    "rinegoziazione",
    "rinegozia",
    "accertamento dell entrata",
    "accertamento dell'entrata",
    "entrate proprie",
    "credito",
    "scadenza del credito",
    "societa veicolo",
    "società veicolo",
    "alienazioni",
    "proventi",
    "titoli obbligazionari",
]

FPV_OPERATIVO_ANCHORS = [
    "fondo pluriennale vincolato",
    "fpv",
    "cronoprogramma",
    "esigibil",
    "imput",
    "obbligazione",
    "obbligazioni passive",
    "scadenza",
    "spesa",
    "spesa di investimento",
]

CASSA_VINCOLATA_STRICT_PAIRS: List[Tuple[str, ...]] = [
    ("cassa vincolata",),
    ("entrate vincolate", "cassa"),
    ("tesorer", "vincolat"),
    ("utilizzo di cassa", "vincolat"),
    ("giacenze", "vincolat"),
    ("fondi vincolati", "cassa"),
    ("reversale", "vincolat"),
    ("incasso", "vincolat"),
]

TOP_N_PRINT = 8


# ==================================================================================================
# DATA
# ==================================================================================================

@dataclass
class Candidate:
    collection: str
    item_id: str
    document: str
    metadata: Dict[str, Any]
    distance: float
    query_hits: List[str] = field(default_factory=list)

    sim_score: float = 0.0
    collection_prior: float = 0.0
    anchor_hits: List[str] = field(default_factory=list)

    hint_score: float = 0.0
    query_bonus: float = 0.0
    penalty_score: float = 0.0
    score_final: float = 0.0

    main_demoted: bool = False
    rescue_mode: bool = False

    anchor_text: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def key(self) -> str:
        return f"{self.collection}::{self.item_id}"

    def short_ref(self) -> str:
        return f"{self.collection}::{self.item_id}"


# ==================================================================================================
# NORMALIZATION
# ==================================================================================================

def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    text = strip_accents(text).lower()
    text = re.sub(r"[“”\"'`´’]", " ", text)
    text = re.sub(r"[^a-z0-9/+\-\. ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def contains_term(text_norm: str, term_norm: str) -> bool:
    return term_norm in text_norm


def count_hits(text_norm: str, terms: Iterable[str]) -> List[str]:
    hits: List[str] = []
    for term in terms:
        term_norm = normalize_text(term)
        if not term_norm:
            continue
        if contains_term(text_norm, term_norm):
            hits.append(term)
    return hits


def truncate_snippet(text: str, max_len: int = 180) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if len(clean) <= max_len:
        return clean
    return clean[: max_len - 3].rstrip() + "..."


# ==================================================================================================
# SUBINTENT
# ==================================================================================================

def detect_domain(query_text: str) -> List[str]:
    # In questo cantiere il dominio operativo è DLgs 118.
    return ["dlgs118"]


def detect_subintent(query_text: str) -> str:
    q = normalize_text(query_text)

    if "cassa vincolata" in q or ("entrate vincolate" in q and "cassa" in q):
        return SUBINTENT_ENTRATE_VINCOLATE_CASSA

    if ("fondo pluriennale vincolato" in q or " fpv " in f" {q} " or q.startswith("fpv")) and (
        "cronoprogramma" in q
        or "esigibil" in q
        or "imput" in q
        or "obbligaz" in q
        or "reimput" in q
    ):
        return SUBINTENT_FPV_OPERATIVO

    if ("fondo pluriennale vincolato" in q or " fpv " in f" {q} " or q.startswith("fpv")) and (
        "bilancio" in q
        or "prospetto" in q
        or "equilibri" in q
        or "nota integrativa" in q
        or "missioni" in q
        or "programmi" in q
    ):
        return SUBINTENT_FPV_STRUTTURALE

    if "riaccertamento" in q or "reimputazione residui" in q:
        return SUBINTENT_RIACCERTAMENTO

    if "impegno di spesa" in q:
        return SUBINTENT_IMPEGNO

    if "esigibil" in q and "spesa" in q:
        return SUBINTENT_ESIGIBILITA

    if "cronoprogramma" in q and "invest" in q:
        return SUBINTENT_CRONO

    if "quote vincolate" in q and "risultato di amministrazione" in q:
        return SUBINTENT_ENTRATE_VINCOLATE_RIS

    if "entrate vincolate" in q:
        return SUBINTENT_ENTRATE_VINCOLATE_RIS

    return SUBINTENT_GENERIC


def build_query_variants(query_text: str, subintent: str) -> List[str]:
    base = query_text.strip()

    if subintent == SUBINTENT_IMPEGNO:
        return [
            "impegno di spesa",
            "impegno di spesa obbligazione giuridicamente perfezionata",
            "all_4_2 5.4 impegno di spesa",
        ]

    if subintent == SUBINTENT_ESIGIBILITA:
        return [
            "esigibilità della spesa",
            "esigibilita della spesa obbligazioni passive esigibili imputazione",
            "all_4_2 5.3.1 esigibilita spesa",
        ]

    if subintent == SUBINTENT_RIACCERTAMENTO:
        if "reimputazione residui passivi" in normalize_text(base):
            return [
                "reimputazione residui passivi",
                "riaccertamento ordinario dei residui reimputazione residui attivi passivi",
                "residui cancellati reimputati riaccertamento ordinario competenza finanziaria potenziata",
            ]
        if "riaccertamento residui passivi e attivi" in normalize_text(base):
            return [
                "riaccertamento residui passivi e attivi",
                "riaccertamento ordinario dei residui reimputazione residui attivi passivi",
                "residui cancellati reimputati riaccertamento ordinario competenza finanziaria potenziata",
            ]
        return [
            "riaccertamento ordinario dei residui",
            "riaccertamento ordinario dei residui reimputazione residui attivi passivi",
            "residui cancellati reimputati riaccertamento ordinario competenza finanziaria potenziata",
        ]

    if subintent == SUBINTENT_CRONO:
        return [
            "cronoprogramma investimento",
            "cronoprogramma investimento esigibilita della spesa",
            "spesa di investimento cronoprogramma all_4_2 5.3.1",
        ]

    if subintent == SUBINTENT_ENTRATE_VINCOLATE_RIS:
        if "quote vincolate risultato di amministrazione" in normalize_text(base):
            return [
                "quote vincolate risultato di amministrazione",
                "entrate vincolate risultato di amministrazione quote vincolate allegato a/2 9.7.2 9.11.4",
                "avanzo vincolato nota integrativa entrate vincolate",
            ]
        return [
            "entrate vincolate",
            "entrate vincolate risultato di amministrazione quote vincolate allegato a/2 9.7.2 9.11.4",
            "avanzo vincolato nota integrativa entrate vincolate",
        ]

    if subintent == SUBINTENT_FPV_OPERATIVO:
        return [
            "fondo pluriennale vincolato cronoprogramma",
            "fondo pluriennale vincolato esigibilita spesa imputazione cronoprogramma",
            "fpv obbligazioni esigibili impegno reimputazione all_4_2",
        ]

    if subintent == SUBINTENT_FPV_STRUTTURALE:
        return [
            "fondo pluriennale vincolato bilancio di previsione",
            "fondo pluriennale vincolato prospetto equilibri bilancio nota integrativa",
            "fpv missioni programmi all_4_1",
        ]

    if subintent == SUBINTENT_ENTRATE_VINCOLATE_CASSA:
        return [
            "cassa vincolata entrate vincolate",
            "entrate vincolate cassa cassa vincolata tesoreria incasso reversale 9.11.4",
            "utilizzo di cassa entrate vincolate gestione di cassa all_4_2",
        ]

    if normalize_text(base) == "fpv":
        return [
            "fpv",
            "fondo pluriennale vincolato fpv all_4_1 all_4_2",
            "fpv risultato di amministrazione esigibilita spesa",
        ]

    return [base]


# ==================================================================================================
# COLLECTION HELPERS
# ==================================================================================================

def get_collection_prior(collection_name: str, subintent: str) -> float:
    if collection_name.endswith("_main"):
        return 0.28 if subintent == SUBINTENT_RIACCERTAMENTO else 0.60

    if collection_name.endswith("_all_1"):
        return 1.70

    if collection_name.endswith("_all_4_1"):
        if subintent in {SUBINTENT_ENTRATE_VINCOLATE_RIS, SUBINTENT_FPV_STRUTTURALE}:
            return 1.85 if subintent == SUBINTENT_ENTRATE_VINCOLATE_RIS else 1.95
        return 1.55

    if collection_name.endswith("_all_4_2"):
        if subintent == SUBINTENT_RIACCERTAMENTO:
            return 3.00
        return 2.10

    return 1.0


def is_main_fulltext(cand: Candidate) -> bool:
    return cand.collection.endswith("_main") and ("fulltext" in cand.item_id)


def is_intro_chunk(cand: Candidate) -> bool:
    txt = cand.anchor_text
    return (
        cand.item_id.startswith("par_0001_intro")
        or "principio contabile applicato concernente la contabilita finanziaria" in txt
    )


def variant_match_bonus(text_norm: str, variants: Sequence[str]) -> float:
    bonus = 0.0
    for var in variants:
        var_norm = normalize_text(var)
        if not var_norm:
            continue
        if var_norm in text_norm:
            if len(var_norm) >= 55:
                bonus += 180.0
            elif len(var_norm) >= 35:
                bonus += 160.0
            elif len(var_norm) >= 20:
                bonus += 140.0
            else:
                bonus += 120.0
    return bonus


def build_anchor_text(document: str, metadata: Dict[str, Any]) -> str:
    pieces: List[str] = []
    if document:
        pieces.append(document)
    for key in ("rubrica", "titolo", "title", "path", "riferimento_normativo"):
        val = metadata.get(key)
        if isinstance(val, str) and val.strip():
            pieces.append(val)
    return normalize_text(" ".join(pieces))


# ==================================================================================================
# FETCH
# ==================================================================================================

def chroma_query_collection(
    collection: Any,
    embedder: SentenceTransformer,
    query_text: str,
    per_collection_k: int,
) -> Dict[str, Any]:
    embedding = embedder.encode(query_text, normalize_embeddings=True)
    return collection.query(
        query_embeddings=[embedding.tolist()],
        n_results=per_collection_k,
        include=["documents", "metadatas", "distances"],
    )


def fetch_candidates_for_collection(
    client: chromadb.PersistentClient,
    embedder: SentenceTransformer,
    collection_name: str,
    query_variants: Sequence[str],
    per_collection_k: int,
) -> List[Candidate]:
    try:
        collection = client.get_collection(collection_name)
    except Exception as exc:
        print(f"[COLLECTION OPEN ERROR] {collection_name} -> {exc}")
        return []

    merged: Dict[str, Candidate] = {}

    for qv in query_variants:
        print(f"[COLLECTION QUERY] {collection_name} -> {qv}")
        try:
            result = chroma_query_collection(collection, embedder, qv, per_collection_k)
        except Exception as exc:
            print(f"[COLLECTION QUERY ERROR] {collection_name} -> {exc}")
            continue

        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]

        for item_id, doc, meta, dist in zip(ids, docs, metas, dists):
            if meta is None:
                meta = {}
            key = f"{collection_name}::{item_id}"
            if key not in merged:
                merged[key] = Candidate(
                    collection=collection_name,
                    item_id=item_id,
                    document=doc or "",
                    metadata=meta or {},
                    distance=float(dist if dist is not None else 1.0),
                    query_hits=[qv],
                )
            else:
                cand = merged[key]
                cand.distance = min(cand.distance, float(dist if dist is not None else 1.0))
                if qv not in cand.query_hits:
                    cand.query_hits.append(qv)
                if len(doc or "") > len(cand.document or ""):
                    cand.document = doc or cand.document
                if not cand.metadata and meta:
                    cand.metadata = meta

    return list(merged.values())


# ==================================================================================================
# SPECIAL LOGIC
# ==================================================================================================

def riaccertamento_lateral_for_top3(anchor_text: str) -> bool:
    lateral_hits = count_hits(anchor_text, RIACCERTAMENTO_TOP3_LATERAL_TERMS)
    return bool(lateral_hits)


def riaccertamento_operational_nucleus(anchor_text: str) -> bool:
    has_residui = "residui" in anchor_text
    has_hard = bool(count_hits(anchor_text, RIACCERTAMENTO_HARD_TERMS))
    has_riacc = "riaccertamento" in anchor_text or "riaccertamento ordinario" in anchor_text
    if not has_residui:
        return False
    if not has_hard:
        return False
    if riaccertamento_lateral_for_top3(anchor_text):
        # Il laterale va escluso se non contiene davvero il nucleo riaccertamento-reimputazione-cancellazione residui
        # Qui il filtro resta severo: rateizzazione/rinegoziazione/entrata non sono nucleo.
        lateral_terms = count_hits(anchor_text, RIACCERTAMENTO_TOP3_LATERAL_TERMS)
        if lateral_terms and not has_riacc:
            return False
    return True


def fpv_operativo_nucleus(cand: Candidate) -> bool:
    t = cand.anchor_text
    code = cand.item_id
    is_all_4_2 = cand.collection.endswith("_all_4_2")

    if any(x in code for x in ("par_0059_5_3", "par_0060_5_3_1", "par_0061_5_3_2")):
        return True

    has_spesa_invest = ("spesa di investimento" in t) or ("spese di investimento" in t)
    has_obbl_passive = "obbligazioni passive" in t
    has_time_logic = any(x in t for x in ("esigibil", "imput", "scadenza", "scadono", "cronoprogramma"))
    return is_all_4_2 and (has_spesa_invest or has_obbl_passive) and has_time_logic


def fpv_operativo_lateral_entrata(cand: Candidate) -> bool:
    t = cand.anchor_text
    has_entrata = ("entrata" in t) or ("entrate" in t) or ("credito" in t) or ("accertamento" in t)
    has_spesa = "spesa" in t or "obbligazioni passive" in t or "spese di investimento" in t
    return has_entrata and not has_spesa


def cassa_vincolata_strict_pairing(anchor_text: str) -> bool:
    for pair in CASSA_VINCOLATA_STRICT_PAIRS:
        if all(term in anchor_text for term in map(normalize_text, pair)):
            return True
    return False


def cassa_vincolata_generic_lateral(anchor_text: str) -> bool:
    generic = any(term in anchor_text for term in ("cassa", "tesorer", "incasso", "reversale"))
    strict = cassa_vincolata_strict_pairing(anchor_text)
    return generic and not strict


# ==================================================================================================
# SCORING
# ==================================================================================================

def score_candidate(
    cand: Candidate,
    query_text: str,
    query_variants: Sequence[str],
    subintent: str,
    rescue_mode: bool,
) -> None:
    cand.rescue_mode = rescue_mode
    cand.anchor_text = build_anchor_text(cand.document, cand.metadata)
    cand.sim_score = max(0.0, 100.0 - (cand.distance * 100.0))
    cand.collection_prior = get_collection_prior(cand.collection, subintent)

    # Anchors di base per stampa diagnostica
    if subintent == SUBINTENT_RIACCERTAMENTO:
        anchor_terms = RIACCERTAMENTO_SOFT_TERMS + RIACCERTAMENTO_HARD_TERMS
    elif subintent == SUBINTENT_FPV_OPERATIVO:
        anchor_terms = FPV_OPERATIVO_ANCHORS
    elif subintent == SUBINTENT_IMPEGNO:
        anchor_terms = [
            "impegno di spesa",
            "obbligazione giuridicamente perfezionata",
            "impegno",
            "spesa",
        ]
    elif subintent == SUBINTENT_ESIGIBILITA:
        anchor_terms = [
            "esigibil",
            "spesa",
            "obbligazioni passive",
            "esigibili",
            "imput",
        ]
    elif subintent == SUBINTENT_CRONO:
        anchor_terms = [
            "cronoprogramma",
            "investimento",
            "esigibil",
            "spesa di investimento",
        ]
    elif subintent == SUBINTENT_ENTRATE_VINCOLATE_RIS:
        anchor_terms = [
            "entrate vincolate",
            "risultato di amministrazione",
            "quote vincolate",
            "allegato a/2",
            "nota integrativa",
            "9.7.2",
            "9.11.4",
        ]
    elif subintent == SUBINTENT_ENTRATE_VINCOLATE_CASSA:
        anchor_terms = [
            "cassa",
            "vincolata",
            "vincolate",
            "tesoreria",
            "incasso",
            "reversale",
        ]
    else:
        anchor_terms = []

    cand.anchor_hits = count_hits(cand.anchor_text, anchor_terms)

    base_score = (cand.sim_score * 1.1) + (cand.collection_prior * 10.0) + (len(cand.anchor_hits) * 12.0)
    cand.query_bonus = variant_match_bonus(cand.anchor_text, query_variants)
    cand.hint_score = 0.0
    cand.penalty_score = 0.0

    # ----------------------------------------------------------------------------------------------
    # SUBINTENT: RIACCERTAMENTO
    # ----------------------------------------------------------------------------------------------
    if subintent == SUBINTENT_RIACCERTAMENTO:
        hard_hits = count_hits(cand.anchor_text, RIACCERTAMENTO_HARD_TERMS)
        soft_hits = count_hits(cand.anchor_text, RIACCERTAMENTO_SOFT_TERMS)

        process_anchor = bool(hard_hits or soft_hits)
        strong_anchor = bool(hard_hits and len(soft_hits) >= 2)
        core_combo = (
            ("riaccertamento ordinario" in cand.anchor_text and "residui" in cand.anchor_text)
            or ("residui" in cand.anchor_text and bool(hard_hits))
        )
        operational_nucleus = riaccertamento_operational_nucleus(cand.anchor_text)
        lateral_top3 = riaccertamento_lateral_for_top3(cand.anchor_text) and not operational_nucleus

        cand.extra["riacc_hard_hits"] = hard_hits
        cand.extra["riacc_soft_hits"] = soft_hits
        cand.extra["process_anchor"] = process_anchor
        cand.extra["strong_anchor"] = strong_anchor
        cand.extra["core_combo"] = core_combo
        cand.extra["operational_nucleus"] = operational_nucleus
        cand.extra["lateral_top3"] = lateral_top3

        if operational_nucleus:
            base_score += 260.0
        if strong_anchor:
            base_score += 110.0
        if core_combo:
            base_score += 90.0

        if rescue_mode and cand.collection.endswith("_all_4_2"):
            base_score += 25.0

        if lateral_top3:
            cand.penalty_score += 440.0

        if is_intro_chunk(cand):
            cand.penalty_score += 320.0

        if is_main_fulltext(cand):
            cand.main_demoted = True
            cand.penalty_score += 140.0

        if rescue_mode and not process_anchor:
            cand.penalty_score += 320.0

    # ----------------------------------------------------------------------------------------------
    # SUBINTENT: FPV OPERATIVO
    # ----------------------------------------------------------------------------------------------
    elif subintent == SUBINTENT_FPV_OPERATIVO:
        nucleus = fpv_operativo_nucleus(cand)
        lateral_entrata = fpv_operativo_lateral_entrata(cand)

        cand.extra["fpv_operational_nucleus"] = nucleus
        cand.extra["fpv_lateral_entrata"] = lateral_entrata

        # bonus strutturale definitivo area 5.3.x
        if "par_0060_5_3_1" in cand.item_id:
            base_score += 260.0
        elif "par_0059_5_3" in cand.item_id:
            base_score += 220.0
        elif "par_0061_5_3_2" in cand.item_id:
            base_score += 210.0
        elif "par_0058_3" in cand.item_id:
            base_score += 90.0

        if nucleus:
            base_score += 140.0

        # penalizza chunk strutturali 9.x dell'All. 4/1 in query operative
        if cand.collection.endswith("_all_4_1") and re.search(r"par_00(6[0-9]|7[0-9])_", cand.item_id):
            cand.penalty_score += 90.0

        if lateral_entrata:
            cand.penalty_score += 160.0

        if is_main_fulltext(cand):
            cand.main_demoted = True
            cand.penalty_score += 60.0

    # ----------------------------------------------------------------------------------------------
    # SUBINTENT: FPV STRUTTURALE
    # ----------------------------------------------------------------------------------------------
    elif subintent == SUBINTENT_FPV_STRUTTURALE:
        if "par_0063_9_8" in cand.item_id:
            base_score += 210.0
        elif "par_0065_9_10" in cand.item_id:
            base_score += 170.0
        elif "par_0068_9_11_1" in cand.item_id:
            base_score += 150.0
        elif cand.collection.endswith("_all_4_1"):
            base_score += 80.0

        if is_main_fulltext(cand):
            cand.main_demoted = True
            cand.penalty_score += 50.0

    # ----------------------------------------------------------------------------------------------
    # SUBINTENT: CASSA VINCOLATA
    # ----------------------------------------------------------------------------------------------
    elif subintent == SUBINTENT_ENTRATE_VINCOLATE_CASSA:
        nucleus = cassa_vincolata_strict_pairing(cand.anchor_text)
        generic_lateral = cassa_vincolata_generic_lateral(cand.anchor_text)

        cand.extra["cassa_vincolata_nucleus"] = nucleus
        cand.extra["cassa_generic_lateral"] = generic_lateral

        if nucleus:
            base_score += 180.0
            if any(term in cand.anchor_text for term in ("tesorer", "incasso", "reversale")):
                base_score += 80.0

        # penalizza "quote vincolate risultato di amministrazione" se manca vera cassa/tesoreria vincolata
        if (
            ("risultato di amministrazione" in cand.anchor_text or "quote vincolate" in cand.anchor_text)
            and not nucleus
        ):
            cand.penalty_score += 140.0

        if generic_lateral:
            cand.penalty_score += 120.0

    # ----------------------------------------------------------------------------------------------
    # SUBINTENT: IMPEGNO
    # ----------------------------------------------------------------------------------------------
    elif subintent == SUBINTENT_IMPEGNO:
        if "par_0054_5" in cand.item_id:
            base_score += 340.0
        elif "par_0060_5_3_1" in cand.item_id:
            base_score += 110.0
        elif "par_0058_3" in cand.item_id:
            base_score += 90.0

        if is_main_fulltext(cand):
            cand.main_demoted = True
            cand.penalty_score += 80.0

    # ----------------------------------------------------------------------------------------------
    # SUBINTENT: ESIGIBILITA'
    # ----------------------------------------------------------------------------------------------
    elif subintent == SUBINTENT_ESIGIBILITA:
        if "par_0060_5_3_1" in cand.item_id:
            base_score += 360.0
        elif "par_0054_5" in cand.item_id:
            base_score += 100.0
        elif "par_0055_5_2" in cand.item_id:
            base_score += 80.0

        if is_main_fulltext(cand):
            cand.main_demoted = True
            cand.penalty_score += 80.0

    # ----------------------------------------------------------------------------------------------
    # SUBINTENT: CRONOPROGRAMMA INVESTIMENTO
    # ----------------------------------------------------------------------------------------------
    elif subintent == SUBINTENT_CRONO:
        if "par_0060_5_3_1" in cand.item_id:
            base_score += 360.0
        elif "par_0061_5_3_2" in cand.item_id:
            base_score += 130.0
        elif "par_0033_3_19" in cand.item_id:
            base_score += 70.0

        if is_main_fulltext(cand):
            cand.main_demoted = True
            cand.penalty_score += 80.0

    # ----------------------------------------------------------------------------------------------
    # SUBINTENT: ENTRATE VINCOLATE RISULTATO
    # ----------------------------------------------------------------------------------------------
    elif subintent == SUBINTENT_ENTRATE_VINCOLATE_RIS:
        if "par_0061_9_7_2" in cand.item_id:
            base_score += 330.0
        elif "par_0071_9_11_4" in cand.item_id:
            base_score += 300.0
        elif "par_0062_9_7_3" in cand.item_id:
            base_score += 80.0

        if is_main_fulltext(cand):
            cand.main_demoted = True
            cand.penalty_score += 70.0

    # ----------------------------------------------------------------------------------------------
    # GENERIC
    # ----------------------------------------------------------------------------------------------
    else:
        if is_main_fulltext(cand):
            cand.main_demoted = False

    cand.score_final = base_score + cand.query_bonus + cand.hint_score - cand.penalty_score


# ==================================================================================================
# POST-RANK GUARDS
# ==================================================================================================

def riaccertamento_top3_guard(ranked: List[Candidate]) -> List[Candidate]:
    operational = [
        c for c in ranked
        if c.extra.get("operational_nucleus") is True and not is_main_fulltext(c)
    ]

    if len(operational) < 2:
        return ranked

    changed = False
    for cand in ranked:
        if is_main_fulltext(cand):
            cand.penalty_score += 900.0
            cand.score_final -= 900.0
            cand.main_demoted = True
            changed = True
        elif is_intro_chunk(cand):
            cand.penalty_score += 800.0
            cand.score_final -= 800.0
            changed = True
        elif cand.extra.get("lateral_top3") is True:
            cand.penalty_score += 500.0
            cand.score_final -= 500.0
            changed = True
        elif cand.extra.get("operational_nucleus") is not True and cand.extra.get("strong_anchor") is not True:
            cand.penalty_score += 220.0
            cand.score_final -= 220.0
            changed = True

    if changed:
        ranked.sort(key=lambda c: (c.score_final, c.sim_score), reverse=True)
    return ranked


def apply_post_rank_guards(subintent: str, ranked: List[Candidate]) -> List[Candidate]:
    if subintent == SUBINTENT_RIACCERTAMENTO:
        return riaccertamento_top3_guard(ranked)
    return ranked


# ==================================================================================================
# RANK
# ==================================================================================================

def rank_candidates(
    candidates: List[Candidate],
    query_text: str,
    query_variants: Sequence[str],
    subintent: str,
    rescue_mode: bool,
) -> List[Candidate]:
    for cand in candidates:
        score_candidate(cand, query_text, query_variants, subintent, rescue_mode=rescue_mode)

    ranked = sorted(candidates, key=lambda c: (c.score_final, c.sim_score), reverse=True)
    ranked = apply_post_rank_guards(subintent, ranked)
    return ranked


# ==================================================================================================
# PRINT
# ==================================================================================================

def print_header(title: str) -> None:
    print("=" * 110)
    print(title)


def print_candidate(cand: Candidate, idx: int, subintent: str) -> None:
    print(f"[{idx}] {cand.short_ref()}")
    print(f"  score_final: {cand.score_final:.4f}")
    print(f"  sim_score: {cand.sim_score:.4f}")
    print(f"  collection_prior: {cand.collection_prior}")
    print(f"  anchor_hits: {len(cand.anchor_hits)} -> {cand.anchor_hits}")

    if subintent == SUBINTENT_RIACCERTAMENTO:
        print(
            "  riacc_hard_hits: "
            f"{cand.extra.get('riacc_hard_hits', [])} | "
            f"riacc_soft_hits: {cand.extra.get('riacc_soft_hits', [])} | "
            f"process_anchor: {cand.extra.get('process_anchor', False)} | "
            f"strong_anchor: {cand.extra.get('strong_anchor', False)} | "
            f"core_combo: {cand.extra.get('core_combo', False)} | "
            f"operational_nucleus: {cand.extra.get('operational_nucleus', False)} | "
            f"lateral_top3: {cand.extra.get('lateral_top3', False)}"
        )

    if subintent == SUBINTENT_FPV_OPERATIVO:
        print(
            "  fpv_operational_nucleus: "
            f"{cand.extra.get('fpv_operational_nucleus', False)} | "
            f"fpv_lateral_entrata: {cand.extra.get('fpv_lateral_entrata', False)}"
        )

    if subintent == SUBINTENT_ENTRATE_VINCOLATE_CASSA:
        print(
            "  cassa_vincolata_nucleus: "
            f"{cand.extra.get('cassa_vincolata_nucleus', False)} | "
            f"cassa_generic_lateral: {cand.extra.get('cassa_generic_lateral', False)}"
        )

    print(
        f"  hint_score: {cand.hint_score:.1f} | "
        f"query_bonus: {cand.query_bonus:.1f} | "
        f"penalty_score: {cand.penalty_score:.1f}"
    )
    print(f"  main_demoted: {cand.main_demoted} | rescue_mode: {cand.rescue_mode}")
    print(f"  snippet: {truncate_snippet(cand.document)}")
    print("-" * 110)


def print_top_results(ranked: List[Candidate], subintent: str, top_n: int = TOP_N_PRINT) -> None:
    print("\n=== TOP RESULTS ===")
    for idx, cand in enumerate(ranked[:top_n], start=1):
        print_candidate(cand, idx, subintent)


def print_common_flags(ranked: List[Candidate]) -> None:
    top3 = ranked[:3]
    anchor_hit_top3 = any(len(c.anchor_hits) > 0 for c in top3)
    main_fulltext_demoted = any(is_main_fulltext(c) and c.main_demoted for c in ranked)
    rescue_ranking = any(c.rescue_mode for c in ranked)

    print(f"ANCHOR_HIT_TOP3: {'YES' if anchor_hit_top3 else 'NO'}")
    print(f"MAIN_FULLTEXT_DEMOTED: {'YES' if main_fulltext_demoted else 'NO'}")
    print(f"RESCUE RANKING: {'ON' if rescue_ranking else 'OFF'}")


def print_check(query_text: str, ranked: List[Candidate], subintent: str) -> None:
    qn = normalize_text(query_text)
    top3 = ranked[:3]

    if subintent == SUBINTENT_RIACCERTAMENTO:
        clean_top3 = [c for c in top3 if not is_intro_chunk(c) and not is_main_fulltext(c)]
        ok = len(clean_top3) >= 2 and all(c.extra.get("operational_nucleus") for c in clean_top3[:2])

        label = "riaccertamento"
        if "reimputazione residui passivi" in qn:
            label = "reimputazione residui passivi"
        elif "riaccertamento residui passivi e attivi" in qn:
            label = "riaccertamento residui passivi e attivi"

        print(f"\nCHECK {label} -> top3 senza intro/fulltext: {'OK' if ok else 'NO'}")
        return

    if subintent == SUBINTENT_IMPEGNO:
        ok = bool(top3) and "par_0054_5" in top3[0].item_id
        print(f"\nCHECK impegno di spesa -> target par_0054_5: {'OK' if ok else 'NO'}")
        return

    if subintent == SUBINTENT_ESIGIBILITA:
        ok = any("par_0060_5_3_1" in c.item_id for c in top3)
        print(f"\nCHECK esigibilità della spesa -> target par_0060_5_3_1: {'OK' if ok else 'NO'}")
        return

    if subintent == SUBINTENT_CRONO:
        ok = bool(top3) and "par_0060_5_3_1" in top3[0].item_id
        print(f"\nCHECK cronoprogramma investimento -> target par_0060_5_3_1 top1: {'OK' if ok else 'NO'}")
        return

    if subintent == SUBINTENT_ENTRATE_VINCOLATE_RIS:
        ok_972 = any("par_0061_9_7_2" in c.item_id for c in top3)
        ok_9114 = any("par_0071_9_11_4" in c.item_id for c in top3)
        print(f"\nCHECK entrate vincolate -> 9.7.2 / 9.11.4 nei top3: {'OK' if (ok_972 and ok_9114) else 'NO'}")
        return

    if subintent == SUBINTENT_FPV_OPERATIVO:
        ok = bool(top3) and any(
            code in top3[0].item_id for code in ("par_0060_5_3_1", "par_0059_5_3", "par_0061_5_3_2")
        )
        print(f"\nCHECK fpv operativo -> area 5.3.x in top1: {'OK' if ok else 'NO'}")
        return

    if subintent == SUBINTENT_FPV_STRUTTURALE:
        ok = any("par_0063_9_8" in c.item_id for c in top3)
        print(f"\nCHECK fpv strutturale -> 9.8 nei top3: {'OK' if ok else 'NO'}")
        return

    if subintent == SUBINTENT_ENTRATE_VINCOLATE_CASSA:
        ok = any(c.extra.get("cassa_vincolata_nucleus") for c in top3)
        print(f"\nCHECK cassa vincolata -> pairing stretto nei top3: {'OK' if ok else 'NO'}")
        return


# ==================================================================================================
# MAIN
# ==================================================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Router federato generale base v25.6.2")
    parser.add_argument("--persist-dir", required=True, help="Percorso Chroma persist directory")
    parser.add_argument(
        "--query-text",
        action="append",
        required=True,
        help="Query da eseguire. Opzione ripetibile.",
    )
    parser.add_argument(
        "--per-collection-k",
        type=int,
        default=12,
        help="Numero risultati per collection e per variante query.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("=== ROUTER FEDERATO GENERALE — BASE v25.6.2 ===")
    print(f"CHROMA_PATH: {args.persist_dir}")
    print(f"EMBED_MODEL: {EMBED_MODEL}")

    client = chromadb.PersistentClient(path=args.persist_dir)
    embedder = SentenceTransformer(EMBED_MODEL)

    for query_text in args.query_text:
        print_header(f"QUERY: {query_text}")

        domains = detect_domain(query_text)
        print(f"DOMAINS: {domains}")

        subintent = detect_subintent(query_text)
        print(f"SUBINTENT DETECTED: {subintent}")

        query_variants = build_query_variants(query_text, subintent)
        print(f"QUERY_VARIANTS: {query_variants}")

        all_candidates: Dict[str, Candidate] = {}

        for domain in domains:
            collections = DOMAIN_COLLECTIONS.get(domain, [])
            print(f"[DOMAIN] {domain} -> {collections}")

            for collection_name in collections:
                fetched = fetch_candidates_for_collection(
                    client=client,
                    embedder=embedder,
                    collection_name=collection_name,
                    query_variants=query_variants,
                    per_collection_k=args.per_collection_k,
                )
                for cand in fetched:
                    key = cand.key()
                    if key not in all_candidates:
                        all_candidates[key] = cand
                    else:
                        old = all_candidates[key]
                        old.distance = min(old.distance, cand.distance)
                        for qh in cand.query_hits:
                            if qh not in old.query_hits:
                                old.query_hits.append(qh)
                        if len(cand.document or "") > len(old.document or ""):
                            old.document = cand.document
                        if not old.metadata and cand.metadata:
                            old.metadata = cand.metadata

        rescue_mode = subintent == SUBINTENT_RIACCERTAMENTO
        print(f"RESCUE RANKING: {'ON' if rescue_mode else 'OFF'}")

        ranked = rank_candidates(
            candidates=list(all_candidates.values()),
            query_text=query_text,
            query_variants=query_variants,
            subintent=subintent,
            rescue_mode=rescue_mode,
        )

        top3 = ranked[:3]
        main_fulltext_in_top3 = any(is_main_fulltext(c) for c in top3)
        anchor_hit_top3 = any(len(c.anchor_hits) > 0 for c in top3)
        print(f"MAIN_FULLTEXT_DEMOTED: {'YES' if any(c.main_demoted for c in ranked) else 'NO'}")
        print(f"ANCHOR_HIT_TOP3: {'YES' if anchor_hit_top3 else 'NO'}")

        print_top_results(ranked, subintent)
        print_common_flags(ranked)
        print_check(query_text, ranked, subintent)
        print()

    cmd = (
        "py tests/run_router_federato_generale_base_v25_6_2.py "
        f'--persist-dir {args.persist_dir}'
    )
    for q in args.query_text:
        cmd += f' --query-text "{q}"'

    print("Comando PowerShell consigliato:")
    print(cmd)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrotto dall'utente.")
        raise SystemExit(130)
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)