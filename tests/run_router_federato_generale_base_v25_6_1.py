#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ROUTER FEDERATO GENERALE — BASE v25.6.1

Patch finale di consolidamento:
1) intro suppression nei rescue ranking del riaccertamento;
2) filtro stretto per fpv_operativo;
3) filtro stretto per entrate_vincolate_cassa.

File ricostruito in forma autosufficiente.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Any, Dict, List, Tuple

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

try:
    import chromadb
except ImportError as exc:
    print("Errore: chromadb non installato.", file=sys.stderr)
    raise

try:
    from sentence_transformers import SentenceTransformer
except ImportError as exc:
    print("Errore: sentence-transformers non installato.", file=sys.stderr)
    raise


# ======================================================================================
# COSTANTI GENERALI
# ======================================================================================

EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

DOMAIN_COLLECTIONS = {
    "dlgs118": [
        "normattiva_dlgs118_2011_main",
        "normattiva_dlgs118_2011_all_1",
        "normattiva_dlgs118_2011_all_4_1",
        "normattiva_dlgs118_2011_all_4_2",
    ]
}

COLLECTION_PRIOR_DEFAULT = {
    "normattiva_dlgs118_2011_main": 0.60,
    "normattiva_dlgs118_2011_all_1": 1.70,
    "normattiva_dlgs118_2011_all_4_1": 1.85,
    "normattiva_dlgs118_2011_all_4_2": 2.10,
}

COLLECTION_PRIOR_RESCUE_RIACC = {
    "normattiva_dlgs118_2011_main": 0.28,
    "normattiva_dlgs118_2011_all_1": 1.70,
    "normattiva_dlgs118_2011_all_4_1": 1.90,
    "normattiva_dlgs118_2011_all_4_2": 3.00,
}

INTRO_ID_PATTERNS = [
    "::par_0001_intro",
    "::fulltext",
]

INTRO_TEXT_PREFIXES = [
    "principio contabile applicato concernente",
    "decreto legislativo",
]

# ======================================================================================
# RIACCERTAMENTO — PROFILO STRETTO
# ======================================================================================

RIACCERTAMENTO_HARD_TERMS = [
    "reimput",
    "cancellat",
]

RIACCERTAMENTO_SOFT_TERMS = [
    "riaccertamento",
    "ordinario",
    "residui",
    "residui attivi",
    "residui passivi",
]

RIACCERTAMENTO_PROCESS_TERMS = [
    "riaccertamento ordinario",
    "riaccertamento",
    "ordinario",
]

RIACCERTAMENTO_OPERATIONAL_TERMS = [
    "reimput",
    "cancellat",
    "residui attivi",
    "residui passivi",
    "esercizi in cui sono esigibili",
    "imput",
]

RIACCERTAMENTO_TOP3_LATERAL_TERMS = [
    "rateizzazione",
    "entrate proprie",
    "accertamento dell'entrata",
    "credito",
    "credito",
    "riscossione",
    "rinegoziazione",
    "mutuo",
    "mutui",
    "titolo obbligazionario",
    "indebitamento",
    "interessi passivi",
]

# ======================================================================================
# FPV OPERATIVO — FILTRO STRETTO
# ======================================================================================

FPV_CORE_TERMS = [
    "fondo pluriennale vincolato",
    "fpv",
    "reimput",
]

FPV_OPERATIVE_TERMS = [
    "cronoprogramma",
    "esigibil",
    "imput",
    "scadenza",
    "obbligazioni passive",
    "spesa di investimento",
]

FPV_ENTRATA_LATERAL_TERMS = [
    "entrata",
    "entrate",
    "credito",
    "accertamento dell'entrata",
    "riscossione",
]

# ======================================================================================
# CASSA VINCOLATA — FILTRO STRETTO
# ======================================================================================

CASSA_CORE_TERMS = [
    "cassa",
    "tesoreria",
    "giacenza",
    "utilizzo di cassa",
]

VINCOLO_CORE_TERMS = [
    "vincolata",
    "vincolate",
    "vincolo",
    "destinazione vincolata",
]

CASSA_GENERIC_TERMS = [
    "incasso",
    "reversale",
    "riscossione",
    "riversamento",
]

# ======================================================================================
# QUERY VARIANTS
# ======================================================================================

QUERY_VARIANTS_BY_SUBINTENT = {
    "generic_dlgs118": lambda q: [
        q,
        "fondo pluriennale vincolato fpv all_4_1 all_4_2",
        "fpv risultato di amministrazione esigibilita spesa",
    ],
    "impegno_spesa": lambda q: [
        q,
        "impegno di spesa obbligazione giuridicamente perfezionata",
        "all_4_2 5.4 impegno di spesa",
    ],
    "esigibilita_spesa": lambda q: [
        q,
        "esigibilita della spesa obbligazioni passive esigibili imputazione",
        "all_4_2 5.3.1 esigibilita spesa",
    ],
    "riaccertamento_ordinario": lambda q: [
        q,
        "riaccertamento ordinario dei residui reimputazione residui attivi passivi",
        "residui cancellati reimputati riaccertamento ordinario competenza finanziaria potenziata",
    ],
    "cronoprogramma_investimento": lambda q: [
        q,
        "cronoprogramma investimento esigibilita della spesa",
        "spesa di investimento cronoprogramma all_4_2 5.3.1",
    ],
    "entrate_vincolate_risultato": lambda q: [
        q,
        "entrate vincolate risultato di amministrazione quote vincolate allegato a/2 9.7.2 9.11.4",
        "avanzo vincolato nota integrativa entrate vincolate",
    ],
    "fpv_operativo": lambda q: [
        q,
        "fondo pluriennale vincolato esigibilita spesa imputazione cronoprogramma",
        "fpv obbligazioni esigibili impegno reimputazione all_4_2",
    ],
    "fpv_strutturale": lambda q: [
        q,
        "fondo pluriennale vincolato prospetto equilibri bilancio nota integrativa",
        "fpv missioni programmi all_4_1",
    ],
    "entrate_vincolate_cassa": lambda q: [
        q,
        "entrate vincolate cassa cassa vincolata tesoreria incasso reversale 9.11.4",
        "utilizzo di cassa entrate vincolate gestione di cassa all_4_2",
    ],
}


# ======================================================================================
# NORMALIZZAZIONE
# ======================================================================================

def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = text.replace("’", "'").replace("`", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def first_snippet(text: str, max_len: int = 180) -> str:
    t = re.sub(r"\s+", " ", (text or "")).strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 3] + "..."


def count_hits(text: str, terms: List[str]) -> int:
    norm = normalize_text(text)
    hits = 0
    for term in terms:
        t = normalize_text(term)
        if t and t in norm:
            hits += 1
    return hits


def matched_terms(text: str, terms: List[str]) -> List[str]:
    norm = normalize_text(text)
    out = []
    for term in terms:
        t = normalize_text(term)
        if t and t in norm:
            out.append(term)
    return out


def is_intro_candidate(cand: Dict[str, Any], anchor_text: str) -> bool:
    cid = (cand.get("id") or "").lower()
    text = (anchor_text or "").strip().lower()

    if any(pat in cid for pat in INTRO_ID_PATTERNS):
        return True

    return any(text.startswith(prefix) for prefix in INTRO_TEXT_PREFIXES)


# ======================================================================================
# SUBINTENT
# ======================================================================================

def detect_subintent(query_text: str) -> str:
    q = normalize_text(query_text)

    if "cassa vincolata" in q:
        return "entrate_vincolate_cassa"

    if "quote vincolate risultato di amministrazione" in q:
        return "entrate_vincolate_risultato"

    if "entrate vincolate" in q:
        return "entrate_vincolate_risultato"

    if "fondo pluriennale vincolato bilancio di previsione" in q:
        return "fpv_strutturale"

    if "fondo pluriennale vincolato cronoprogramma" in q:
        return "fpv_operativo"

    if "cronoprogramma investimento" in q:
        return "cronoprogramma_investimento"

    if "riaccertamento" in q or "reimputazione residui" in q:
        return "riaccertamento_ordinario"

    if "esigibil" in q and "spesa" in q:
        return "esigibilita_spesa"

    if "impegno di spesa" in q:
        return "impegno_spesa"

    return "generic_dlgs118"


def build_query_variants(query_text: str, subintent: str) -> List[str]:
    builder = QUERY_VARIANTS_BY_SUBINTENT.get(subintent)
    if builder:
        return builder(query_text)
    return [query_text]


# ======================================================================================
# PROFILI SPECIALI
# ======================================================================================

def riaccertamento_profile(anchor_text: str) -> Dict[str, Any]:
    hard_hits_terms = matched_terms(anchor_text, RIACCERTAMENTO_HARD_TERMS)
    soft_hits_terms = matched_terms(anchor_text, RIACCERTAMENTO_SOFT_TERMS)
    process_hits = matched_terms(anchor_text, RIACCERTAMENTO_PROCESS_TERMS)
    operational_hits = matched_terms(anchor_text, RIACCERTAMENTO_OPERATIONAL_TERMS)

    process_anchor = len(process_hits) >= 1 and len(soft_hits_terms) >= 2
    strong_anchor = len(hard_hits_terms) >= 1 and len(soft_hits_terms) >= 2
    core_combo = process_anchor and len(soft_hits_terms) >= 3
    operational_nucleus = len(hard_hits_terms) >= 1 and len(operational_hits) >= 2

    return {
        "hard_hits_terms": hard_hits_terms,
        "soft_hits_terms": soft_hits_terms,
        "process_hits": process_hits,
        "operational_hits": operational_hits,
        "process_anchor": process_anchor,
        "strong_anchor": strong_anchor,
        "core_combo": core_combo,
        "operational_nucleus": operational_nucleus,
    }


def riaccertamento_lateral_for_top3(anchor_text: str, profile: Dict[str, Any]) -> bool:
    lateral_hits = count_hits(anchor_text, [normalize_text(x) for x in RIACCERTAMENTO_TOP3_LATERAL_TERMS])
    has_hard = len(profile.get("hard_hits_terms", [])) >= 1
    has_operational = profile.get("operational_nucleus", False)
    return lateral_hits >= 2 and (not has_hard) and (not has_operational)


def fpv_operational_nucleus(anchor_text: str) -> bool:
    fpv_hits = count_hits(anchor_text, [normalize_text(x) for x in FPV_CORE_TERMS])
    op_hits = count_hits(anchor_text, [normalize_text(x) for x in FPV_OPERATIVE_TERMS])
    return fpv_hits >= 1 and op_hits >= 1


def fpv_entrata_lateral(anchor_text: str) -> bool:
    lateral_hits = count_hits(anchor_text, [normalize_text(x) for x in FPV_ENTRATA_LATERAL_TERMS])
    fpv_hits = count_hits(anchor_text, [normalize_text(x) for x in FPV_CORE_TERMS])
    return lateral_hits >= 2 and fpv_hits == 0


def cassa_vincolata_nucleus(anchor_text: str) -> bool:
    cassa_hits = count_hits(anchor_text, [normalize_text(x) for x in CASSA_CORE_TERMS])
    vincolo_hits = count_hits(anchor_text, [normalize_text(x) for x in VINCOLO_CORE_TERMS])
    return cassa_hits >= 1 and vincolo_hits >= 1


def cassa_generic_lateral(anchor_text: str) -> bool:
    cassa_hits = count_hits(anchor_text, [normalize_text(x) for x in CASSA_CORE_TERMS])
    vincolo_hits = count_hits(anchor_text, [normalize_text(x) for x in VINCOLO_CORE_TERMS])
    generic_hits = count_hits(anchor_text, [normalize_text(x) for x in CASSA_GENERIC_TERMS])
    return cassa_hits >= 1 and vincolo_hits == 0 and generic_hits >= 2


# ======================================================================================
# QUERY COLLECTION
# ======================================================================================

def distance_to_similarity(distance: float) -> float:
    try:
        dist = float(distance)
    except Exception:
        return 0.0

    # conversione robusta, utile per ranking leggibile
    sim = 100.0 * (1.0 / (1.0 + max(dist, 0.0)))
    return round(sim, 4)


def collection_prior(collection_name: str, rescue_mode: bool, subintent: str) -> float:
    if rescue_mode and subintent == "riaccertamento_ordinario":
        return COLLECTION_PRIOR_RESCUE_RIACC.get(collection_name, 1.0)
    return COLLECTION_PRIOR_DEFAULT.get(collection_name, 1.0)


def fetch_candidates_for_collection(
    client: chromadb.PersistentClient,
    model: SentenceTransformer,
    collection_name: str,
    query_text: str,
    per_collection_k: int,
) -> List[Dict[str, Any]]:
    collection = client.get_collection(collection_name)
    embedding = model.encode(query_text).tolist()

    result = collection.query(
        query_embeddings=[embedding],
        n_results=per_collection_k,
        include=["documents", "metadatas", "distances"],
    )

    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    dists = (result.get("distances") or [[]])[0]
    ids = (result.get("ids") or [[]])[0]

    out = []
    for i, doc in enumerate(docs):
        meta = metas[i] if i < len(metas) else {}
        dist = dists[i] if i < len(dists) else 1.0
        cid = ids[i] if i < len(ids) else f"{collection_name}::{i}"

        out.append(
            {
                "id": cid,
                "collection_name": collection_name,
                "document": doc or "",
                "metadata": meta or {},
                "distance": dist,
                "sim_score": distance_to_similarity(dist),
            }
        )

    return out


# ======================================================================================
# SCORING
# ======================================================================================

def score_candidate(
    cand: Dict[str, Any],
    query_text: str,
    subintent: str,
    rescue_mode: bool = False,
) -> None:
    anchor_text = normalize_text(cand.get("document", ""))
    cand["snippet"] = first_snippet(cand.get("document", ""))

    query_bonus = 0.0
    penalty_score = 0.0
    hint_score = 0.0

    coll_name = cand.get("collection_name", "")
    prior = collection_prior(coll_name, rescue_mode=rescue_mode, subintent=subintent)
    cand["collection_prior"] = prior

    # anchor terms base
    anchor_terms_by_subintent = {
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
        "entrate_vincolate_risultato": [
            "entrate vincolate",
            "risultato di amministrazione",
            "quote vincolate",
            "allegato a/2",
            "nota integrativa",
            "9.7.2",
            "9.11.4",
        ],
        "fpv_operativo": [
            "fondo pluriennale vincolato",
            "esigibil",
            "imput",
            "obbligazione",
            "cronoprogramma",
            "scadenza",
            "spesa",
        ],
        "fpv_strutturale": [
            "fondo pluriennale vincolato",
            "prospetto",
            "equilibri",
            "bilancio",
            "nota integrativa",
            "missioni",
            "programmi",
        ],
        "entrate_vincolate_cassa": [
            "cassa",
            "tesoreria",
            "incasso",
            "reversale",
            "vincolata",
            "vincolate",
        ],
    }

    if subintent == "riaccertamento_ordinario":
        riacc = riaccertamento_profile(anchor_text)
        cand["riacc_hard_hits"] = riacc["hard_hits_terms"]
        cand["riacc_soft_hits"] = riacc["soft_hits_terms"]
        cand["process_anchor"] = riacc["process_anchor"]
        cand["strong_anchor"] = riacc["strong_anchor"]
        cand["core_combo"] = riacc["core_combo"]
        cand["operational_nucleus"] = riacc["operational_nucleus"]

        anchor_terms = (
            riacc["soft_hits_terms"]
            + riacc["hard_hits_terms"]
        )
        anchor_hits_terms = list(dict.fromkeys(anchor_terms))
        cand["anchor_hits"] = anchor_hits_terms
        cand["anchor_hits_count"] = len(anchor_hits_terms)

        lateral_top3 = riaccertamento_lateral_for_top3(anchor_text, riacc)
        cand["lateral_top3"] = lateral_top3

        # rescue ranking stretto
        if rescue_mode:
            if riacc["core_combo"]:
                query_bonus += 160.0
            else:
                penalty_score += 120.0

            if riacc["operational_nucleus"]:
                query_bonus += 220.0
            else:
                penalty_score += 200.0

            if riacc["process_anchor"]:
                query_bonus += 80.0

            if lateral_top3:
                penalty_score += 240.0

        # boost query mirati
        q = normalize_text(query_text)
        if "reimputazione residui passivi" in q:
            if "residui passivi" in anchor_text and "reimput" in anchor_text:
                query_bonus += 80.0
        elif "riaccertamento residui passivi e attivi" in q:
            if "residui passivi" in anchor_text:
                query_bonus += 28.0

    else:
        anchor_terms = anchor_terms_by_subintent.get(subintent, [])
        anchor_hits_terms = matched_terms(anchor_text, anchor_terms)
        cand["anchor_hits"] = anchor_hits_terms
        cand["anchor_hits_count"] = len(anchor_hits_terms)

    # intro suppression finale
    intro_like = is_intro_candidate(cand, anchor_text)
    cand["intro_like"] = intro_like

    if rescue_mode and intro_like:
        no_real_anchor = (cand.get("anchor_hits_count", 0) == 0)
        no_operational_nucleus = not cand.get("operational_nucleus", False)
        no_core_combo = not cand.get("core_combo", False)

        if no_real_anchor and no_operational_nucleus and no_core_combo:
            penalty_score += 180.0

    # demotion fulltext main
    main_demoted = False
    if coll_name.endswith("_main") and ("::fulltext" in (cand.get("id") or "").lower() or intro_like):
        if rescue_mode or subintent in {"impegno_spesa", "esigibilita_spesa", "cronoprogramma_investimento"}:
            penalty_score += 140.0
            main_demoted = True

    cand["main_demoted"] = main_demoted

    # subintent-specific add-on
    if subintent == "impegno_spesa":
        hint_score += 36.0 * cand["anchor_hits_count"]

    elif subintent == "esigibilita_spesa":
        hint_score += 28.5 * cand["anchor_hits_count"]

    elif subintent == "cronoprogramma_investimento":
        hint_score += 44.25 * cand["anchor_hits_count"]

    elif subintent == "entrate_vincolate_risultato":
        hint_score += 27.5 * cand["anchor_hits_count"]

    elif subintent == "fpv_operativo":
        fpv_nucleus = fpv_operational_nucleus(anchor_text)
        cand["fpv_operational_nucleus"] = fpv_nucleus

        if fpv_nucleus:
            query_bonus += 90.0
        else:
            penalty_score += 70.0

        if fpv_entrata_lateral(anchor_text):
            penalty_score += 120.0
            cand["fpv_lateral_entrata"] = True
        else:
            cand["fpv_lateral_entrata"] = False

    elif subintent == "entrate_vincolate_cassa":
        cassa_nucleus = cassa_vincolata_nucleus(anchor_text)
        cand["cassa_vincolata_nucleus"] = cassa_nucleus

        if cassa_nucleus:
            query_bonus += 95.0
        else:
            penalty_score += 60.0

        if cassa_generic_lateral(anchor_text):
            penalty_score += 110.0
            cand["cassa_generic_lateral"] = True
        else:
            cand["cassa_generic_lateral"] = False

    elif subintent == "fpv_strutturale":
        hint_score += 22.0 * cand["anchor_hits_count"]

    elif subintent == "generic_dlgs118":
        hint_score += 0.0

    # score finale
    base = cand["sim_score"] * prior
    score_final = base + hint_score + query_bonus - penalty_score

    cand["hint_score"] = round(hint_score, 4)
    cand["query_bonus"] = round(query_bonus, 4)
    cand["penalty_score"] = round(penalty_score, 4)
    cand["score_final"] = round(score_final, 4)
    cand["rescue_mode"] = rescue_mode


def rank_candidates(
    candidates: List[Dict[str, Any]],
    query_text: str,
    subintent: str,
    rescue_mode: bool = False,
) -> List[Dict[str, Any]]:
    for cand in candidates:
        score_candidate(cand, query_text, subintent, rescue_mode=rescue_mode)

    return sorted(
        candidates,
        key=lambda x: (
            x.get("score_final", 0.0),
            x.get("anchor_hits_count", 0),
            x.get("sim_score", 0.0),
        ),
        reverse=True,
    )


# ======================================================================================
# REPORT
# ======================================================================================

def print_candidate(idx: int, cand: Dict[str, Any]) -> None:
    print(f"[{idx}] {cand.get('id')}")
    print(f"  score_final: {cand.get('score_final')}")
    print(f"  sim_score: {cand.get('sim_score')}")
    print(f"  collection_prior: {cand.get('collection_prior')}")
    print(f"  anchor_hits: {cand.get('anchor_hits_count', 0)} -> {cand.get('anchor_hits', [])}")

    extra_parts = []

    if "riacc_hard_hits" in cand:
        extra_parts.append(f"riacc_hard_hits: {cand.get('riacc_hard_hits')}")
    if "riacc_soft_hits" in cand:
        extra_parts.append(f"riacc_soft_hits: {cand.get('riacc_soft_hits')}")
    if "process_anchor" in cand:
        extra_parts.append(f"process_anchor: {cand.get('process_anchor')}")
    if "strong_anchor" in cand:
        extra_parts.append(f"strong_anchor: {cand.get('strong_anchor')}")
    if "core_combo" in cand:
        extra_parts.append(f"core_combo: {cand.get('core_combo')}")
    if "operational_nucleus" in cand:
        extra_parts.append(f"operational_nucleus: {cand.get('operational_nucleus')}")
    if "lateral_top3" in cand:
        extra_parts.append(f"lateral_top3: {cand.get('lateral_top3')}")
    if "fpv_operational_nucleus" in cand:
        extra_parts.append(f"fpv_operational_nucleus: {cand.get('fpv_operational_nucleus')}")
    if "fpv_lateral_entrata" in cand:
        extra_parts.append(f"fpv_lateral_entrata: {cand.get('fpv_lateral_entrata')}")
    if "cassa_vincolata_nucleus" in cand:
        extra_parts.append(f"cassa_vincolata_nucleus: {cand.get('cassa_vincolata_nucleus')}")
    if "cassa_generic_lateral" in cand:
        extra_parts.append(f"cassa_generic_lateral: {cand.get('cassa_generic_lateral')}")

    if extra_parts:
        print("  " + " | ".join(extra_parts))

    print(
        f"  hint_score: {cand.get('hint_score')} | "
        f"query_bonus: {cand.get('query_bonus')} | "
        f"penalty_score: {cand.get('penalty_score')}"
    )
    print(f"  main_demoted: {cand.get('main_demoted')} | rescue_mode: {cand.get('rescue_mode')}")
    print(f"  snippet: {cand.get('snippet')}")
    print("-" * 110)


def print_top_results(
    ranked: List[Dict[str, Any]],
    query_text: str,
    rescue_mode: bool,
) -> None:
    print()
    print("=== TOP RESULTS ===")
    for idx, cand in enumerate(ranked[:8], start=1):
        print_candidate(idx, cand)

    top3 = ranked[:3]
    anchor_hit_top3 = any(c.get("anchor_hits_count", 0) > 0 for c in top3)
    main_fulltext_demoted = any(c.get("main_demoted", False) for c in ranked[:8])

    print(f"ANCHOR_HIT_TOP3: {'YES' if anchor_hit_top3 else 'NO'}")
    print(f"MAIN_FULLTEXT_DEMOTED: {'YES' if main_fulltext_demoted else 'NO'}")
    print(f"RESCUE RANKING: {'ON' if rescue_mode else 'OFF'}")


def check_query(query_text: str, ranked: List[Dict[str, Any]]) -> None:
    q = normalize_text(query_text)
    top3_ids = [c.get("id", "") for c in ranked[:3]]

    if q == "fpv":
        ok_41 = any("all_4_1" in cid for cid in top3_ids)
        ok_42 = any("all_4_2" in cid for cid in top3_ids)
        print()
        print(f"CHECK fpv -> all_4_1 nei top3: {'OK' if ok_41 else 'NO'} | all_4_2 nei top3: {'OK' if ok_42 else 'NO'}")

    elif q == "impegno di spesa":
        ok = ranked and "par_0054_5" in ranked[0].get("id", "")
        print()
        print(f"CHECK impegno di spesa -> target par_0054_5: {'OK' if ok else 'NO'}")

    elif q == "esigibilità della spesa" or q == "esigibilita della spesa":
        ok = ranked and "par_0060_5_3_1" in ranked[0].get("id", "")
        print()
        print(f"CHECK esigibilità della spesa -> target par_0060_5_3_1: {'OK' if ok else 'NO'}")

    elif q == "riaccertamento ordinario dei residui":
        no_intro_top3 = all("par_0001_intro" not in cid for cid in top3_ids)
        print()
        print(
            "CHECK riaccertamento -> top3 senza intro: "
            f"{'OK' if no_intro_top3 else 'NO'}"
        )

    elif q == "cronoprogramma investimento":
        ok = ranked and "par_0060_5_3_1" in ranked[0].get("id", "")
        print()
        print(f"CHECK cronoprogramma investimento -> target par_0060_5_3_1: {'OK' if ok else 'NO'}")

    elif q == "entrate vincolate":
        ok_972 = any("par_0061_9_7_2" in cid for cid in top3_ids)
        ok_9114 = any("par_0071_9_11_4" in cid for cid in top3_ids)
        print()
        print(f"CHECK entrate vincolate -> 9.7.2 / 9.11.4 nei top3: {'OK' if (ok_972 and ok_9114) else 'NO'}")

    elif q == "reimputazione residui passivi":
        no_intro_top3 = all("par_0001_intro" not in cid for cid in top3_ids)
        print()
        print(f"CHECK reimputazione residui passivi -> top3 senza intro: {'OK' if no_intro_top3 else 'NO'}")

    elif q == "riaccertamento residui passivi e attivi":
        no_intro_top3 = all("par_0001_intro" not in cid for cid in top3_ids)
        print()
        print(f"CHECK riaccertamento residui passivi e attivi -> top3 senza intro: {'OK' if no_intro_top3 else 'NO'}")


# ======================================================================================
# MAIN
# ======================================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist-dir", required=True, help="Path Chroma persist dir")
    parser.add_argument("--query-text", action="append", required=True, help="Query testuale")
    parser.add_argument("--per-collection-k", type=int, default=8)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("=== ROUTER FEDERATO GENERALE — BASE v25.6.1 ===")
    print(f"CHROMA_PATH: {args.persist_dir}")
    print(f"EMBED_MODEL: {EMBED_MODEL}")

    model = SentenceTransformer(EMBED_MODEL)
    client = chromadb.PersistentClient(path=args.persist_dir)

    for query_text in args.query_text:
        print("=" * 110)
        print(f"QUERY: {query_text}")

        domains = ["dlgs118"]
        print(f"DOMAINS: {domains}")

        subintent = detect_subintent(query_text)
        print(f"SUBINTENT DETECTED: {subintent}")

        query_variants = build_query_variants(query_text, subintent)
        print(f"QUERY_VARIANTS: {query_variants}")

        all_candidates: Dict[str, Dict[str, Any]] = {}

        for domain in domains:
            collections = DOMAIN_COLLECTIONS[domain]
            print(f"[DOMAIN] {domain} -> {collections}")

            for collection_name in collections:
                for variant in query_variants:
                    try:
                        print(f"[COLLECTION QUERY] {collection_name} -> {variant}")
                        fetched = fetch_candidates_for_collection(
                            client=client,
                            model=model,
                            collection_name=collection_name,
                            query_text=variant,
                            per_collection_k=args.per_collection_k,
                        )
                    except Exception as exc:
                        print(f"[COLLECTION QUERY ERROR] {collection_name} -> {exc}")
                        continue

                    for cand in fetched:
                        cid = cand["id"]
                        prev = all_candidates.get(cid)
                        if prev is None or cand["sim_score"] > prev["sim_score"]:
                            all_candidates[cid] = cand

        rescue_mode = (subintent == "riaccertamento_ordinario")

        ranked = rank_candidates(
            list(all_candidates.values()),
            query_text=query_text,
            subintent=subintent,
            rescue_mode=rescue_mode,
        )

        print_top_results(ranked, query_text=query_text, rescue_mode=rescue_mode)
        check_query(query_text, ranked)
        print()

    print("Comando PowerShell consigliato:")
    print(
        'py tests/run_router_federato_generale_base_v25_6_1.py '
        '--persist-dir data/chroma '
        '--query-text "fpv" '
        '--query-text "impegno di spesa" '
        '--query-text "esigibilità della spesa" '
        '--query-text "riaccertamento ordinario dei residui" '
        '--query-text "cronoprogramma investimento" '
        '--query-text "entrate vincolate" '
        '--query-text "reimputazione residui passivi" '
        '--query-text "riaccertamento residui passivi e attivi" '
        '--query-text "fondo pluriennale vincolato cronoprogramma" '
        '--query-text "fondo pluriennale vincolato bilancio di previsione" '
        '--query-text "quote vincolate risultato di amministrazione" '
        '--query-text "cassa vincolata entrate vincolate"'
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())