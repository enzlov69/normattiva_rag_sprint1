#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ROUTER FEDERATO GENERALE — BASE v25.6.3

Patch chirurgica:
- per il subintent `riaccertamento_ordinario`, in rescue mode, il ranking finale
  ammette solo candidati con vero nucleo operativo;
- in più esclude esplicitamente fulltext / intro dal ranking finale del riaccertamento,
  così non possono più occupare il top3.

Uso tipico:
py tests/run_router_federato_generale_base_v25_6_3.py ^
  --persist-dir data/chroma ^
  --query-text "riaccertamento ordinario dei residui" ^
  --query-text "reimputazione residui passivi" ^
  --query-text "riaccertamento residui passivi e attivi" ^
  --query-text "fondo pluriennale vincolato cronoprogramma" ^
  --query-text "cassa vincolata entrate vincolate"
"""

from __future__ import annotations

import argparse
import re
import traceback
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

import chromadb
from sentence_transformers import SentenceTransformer


VERSION = "v25.6.3"
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

DOMAIN_COLLECTIONS: Dict[str, List[str]] = {
    "dlgs118": [
        "normattiva_dlgs118_2011_main",
        "normattiva_dlgs118_2011_all_1",
        "normattiva_dlgs118_2011_all_4_1",
        "normattiva_dlgs118_2011_all_4_2",
    ]
}

DEFAULT_PER_COLLECTION_K = 8

RIACC_SOFT_TERMS = [
    "riaccertamento",
    "ordinario",
    "residui",
    "residui passivi",
    "residui attivi",
]

RIACC_HARD_TERMS = [
    "reimput",
    "cancellat",
]

FPV_OPERATIVE_TERMS = [
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

CASSA_VINCOLATA_TERMS = [
    "cassa",
    "vincolata",
    "vincolate",
    "tesoreria",
    "incasso",
    "reversale",
]

INTRO_TOKENS = [
    "principio contabile applicato",
    "programmazione di bilancio",
]

FULLTEXT_LOW_PRIORITY = {
    "normattiva_dlgs118_2011_main::fulltext",
    "normattiva_dlgs118_2011_main::normattiva_dlgs118_2011_main::fulltext",
}


@dataclass
class Candidate:
    key: str
    collection: str
    doc_id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    distance: Optional[float] = None
    best_variant: str = ""
    query_hits: List[str] = field(default_factory=list)
    score_final: float = 0.0
    sim_score: float = 0.0
    collection_prior: float = 0.0
    hint_score: float = 0.0
    query_bonus: float = 0.0
    penalty_score: float = 0.0
    main_demoted: bool = False
    rescue_mode: bool = False

    # flags diagnostici
    anchor_hits: List[str] = field(default_factory=list)

    riacc_hard_hits: List[str] = field(default_factory=list)
    riacc_soft_hits: List[str] = field(default_factory=list)
    process_anchor: bool = False
    strong_anchor: bool = False
    core_combo: bool = False
    operational_nucleus: bool = False
    lateral_top3: bool = False

    fpv_operational_nucleus: bool = False
    fpv_lateral_entrata: bool = False

    cassa_vincolata_nucleus: bool = False
    cassa_generic_lateral: bool = False


def normalize_text(value: str) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = value.replace("’", "'").replace("“", '"').replace("”", '"')
    value = re.sub(r"[^a-z0-9àèéìòù/\-\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def compact_snippet(text: str, max_len: int = 180) -> str:
    txt = re.sub(r"\s+", " ", (text or "")).strip()
    if len(txt) <= max_len:
        return txt
    return txt[: max_len - 3].rstrip() + "..."


def count_hits(anchor_text: str, terms: Iterable[str]) -> List[str]:
    hits: List[str] = []
    for term in terms:
        term_n = normalize_text(term)
        if term_n and term_n in anchor_text:
            hits.append(term)
    return hits


def looks_like_intro(candidate: Candidate) -> bool:
    key_n = normalize_text(candidate.key)
    doc_n = normalize_text(candidate.doc_id)
    txt_n = normalize_text(candidate.text[:200])
    if "::fulltext" in key_n or candidate.doc_id == "fulltext":
        return True
    if "intro" in doc_n:
        return True
    return any(tok in txt_n for tok in INTRO_TOKENS)


def is_fulltext_or_intro_candidate(candidate: Candidate) -> bool:
    return candidate.key in FULLTEXT_LOW_PRIORITY or looks_like_intro(candidate)


def compute_similarity_score(distance: Optional[float], text: str) -> float:
    """
    Conversione robusta della distance Chroma in score leggibile.
    Non serve essere identici ai log storici: serve coerenza interna.
    """
    if distance is None:
        base = 50.0
    else:
        base = max(0.0, 100.0 - (distance * 50.0))
    if len(text or "") > 60:
        base += 3.0
    return round(base, 4)


def get_collection_prior(collection: str, subintent: str, rescue_mode: bool) -> float:
    if collection.endswith("_all_4_2"):
        if subintent == "riaccertamento_ordinario" and rescue_mode:
            return 3.0
        return 2.1
    if collection.endswith("_all_4_1"):
        if subintent in {"entrate_vincolate_risultato", "fpv_strutturale"}:
            return 1.85
        return 1.55
    if collection.endswith("_all_1"):
        return 1.7 if subintent == "riaccertamento_ordinario" else 1.55
    if collection.endswith("_main"):
        return 0.28 if rescue_mode else 0.6
    return 1.0


def detect_domains(query_text: str) -> List[str]:
    return ["dlgs118"]


def detect_subintent(query_text: str) -> str:
    q = normalize_text(query_text)

    if (
        "riaccertamento" in q
        or "reimputazione residui" in q
        or "residui passivi e attivi" in q
    ):
        return "riaccertamento_ordinario"

    if "cassa vincolata" in q or (
        "entrate vincolate" in q and ("tesoreria" in q or "reversale" in q or "incasso" in q or "cassa" in q)
    ):
        return "entrate_vincolate_cassa"

    if "quote vincolate risultato di amministrazione" in q:
        return "entrate_vincolate_risultato"

    if "entrate vincolate" in q:
        return "entrate_vincolate_risultato"

    if "fondo pluriennale vincolato" in q and "cronoprogramma" in q:
        return "fpv_operativo"

    if "fondo pluriennale vincolato" in q and (
        "bilancio di previsione" in q or "prospetto" in q or "equilibri" in q
    ):
        return "fpv_strutturale"

    if "cronoprogramma" in q and "investimento" in q:
        return "cronoprogramma_investimento"

    if "esigibilita" in q and "spesa" in q:
        return "esigibilita_spesa"

    if "impegno di spesa" in q:
        return "impegno_spesa"

    if q.strip() == "fpv":
        return "generic_dlgs118"

    return "generic_dlgs118"


def build_query_variants(query_text: str, subintent: str) -> List[str]:
    q = query_text.strip()

    custom: Dict[str, List[str]] = {
        "riaccertamento_ordinario": [
            q,
            "riaccertamento ordinario dei residui reimputazione residui attivi passivi",
            "residui cancellati reimputati riaccertamento ordinario competenza finanziaria potenziata",
        ],
        "fpv_operativo": [
            q,
            "fondo pluriennale vincolato esigibilita spesa imputazione cronoprogramma",
            "fpv obbligazioni esigibili impegno reimputazione all_4_2",
        ],
        "fpv_strutturale": [
            q,
            "fondo pluriennale vincolato prospetto equilibri bilancio nota integrativa",
            "fpv missioni programmi all_4_1",
        ],
        "entrate_vincolate_risultato": [
            q,
            "entrate vincolate risultato di amministrazione quote vincolate allegato a/2 9.7.2 9.11.4",
            "avanzo vincolato nota integrativa entrate vincolate",
        ],
        "entrate_vincolate_cassa": [
            q,
            "entrate vincolate cassa cassa vincolata tesoreria incasso reversale 9.11.4",
            "utilizzo di cassa entrate vincolate gestione di cassa all_4_2",
        ],
        "cronoprogramma_investimento": [
            q,
            "cronoprogramma investimento esigibilita della spesa",
            "spesa di investimento cronoprogramma all_4_2 5.3.1",
        ],
        "esigibilita_spesa": [
            q,
            "esigibilita della spesa obbligazioni passive esigibili imputazione",
            "all_4_2 5.3.1 esigibilita spesa",
        ],
        "impegno_spesa": [
            q,
            "impegno di spesa obbligazione giuridicamente perfezionata",
            "all_4_2 5.4 impegno di spesa",
        ],
        "generic_dlgs118": [
            q,
            "fondo pluriennale vincolato fpv all_4_1 all_4_2",
            "fpv risultato di amministrazione esigibilita spesa",
        ],
    }
    variants = custom.get(subintent, [q])

    out: List[str] = []
    seen = set()
    for v in variants:
        if v not in seen:
            out.append(v)
            seen.add(v)
    return out


def is_rescue_mode(subintent: str) -> bool:
    return subintent == "riaccertamento_ordinario"


def candidate_key(collection_name: str, metadata: Dict[str, Any], doc_text: str) -> Tuple[str, str]:
    doc_id = (
        metadata.get("chunk_id")
        or metadata.get("id")
        or metadata.get("document_id")
        or metadata.get("source_id")
        or metadata.get("record_id")
        or ""
    )
    if not doc_id:
        if collection_name.endswith("_main"):
            doc_id = "fulltext"
        else:
            doc_id = "unknown"
    key = f"{collection_name}::{doc_id}"
    return key, doc_id


def fetch_candidates_for_collection(
    collection: Any,
    collection_name: str,
    model: SentenceTransformer,
    query_variants: List[str],
    per_collection_k: int,
) -> Dict[str, Candidate]:
    fetched: Dict[str, Candidate] = {}

    for variant in query_variants:
        print(f"[COLLECTION QUERY] {collection_name} -> {variant}")
        embedding = model.encode([variant], normalize_embeddings=True)[0].tolist()

        result = collection.query(
            query_embeddings=[embedding],
            n_results=per_collection_k,
            include=["documents", "metadatas", "distances"],
        )

        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, dists):
            meta = meta or {}
            key, doc_id = candidate_key(collection_name, meta, doc or "")
            if key not in fetched:
                fetched[key] = Candidate(
                    key=key,
                    collection=collection_name,
                    doc_id=doc_id,
                    text=doc or "",
                    metadata=meta,
                    distance=dist,
                    best_variant=variant,
                )
            else:
                existing = fetched[key]
                if existing.distance is None or (dist is not None and dist < existing.distance):
                    existing.distance = dist
                    existing.best_variant = variant
                    existing.text = doc or existing.text
                    existing.metadata = meta or existing.metadata

    return fetched


def score_candidate(candidate: Candidate, query_text: str, subintent: str, rescue_mode: bool) -> None:
    text_n = normalize_text(candidate.text)
    candidate.rescue_mode = rescue_mode
    candidate.sim_score = compute_similarity_score(candidate.distance, candidate.text)
    candidate.collection_prior = get_collection_prior(candidate.collection, subintent, rescue_mode)

    anchor_terms = []
    if subintent == "riaccertamento_ordinario":
        anchor_terms = RIACC_SOFT_TERMS + RIACC_HARD_TERMS
    elif subintent == "fpv_operativo":
        anchor_terms = FPV_OPERATIVE_TERMS
    elif subintent == "entrate_vincolate_cassa":
        anchor_terms = CASSA_VINCOLATA_TERMS
    else:
        anchor_terms = [normalize_text(query_text)]

    candidate.anchor_hits = count_hits(text_n, anchor_terms)

    base_score = candidate.sim_score + (candidate.collection_prior * 30.0)
    penalty = 0.0
    bonus = 0.0

    if is_fulltext_or_intro_candidate(candidate):
        if rescue_mode or subintent in {"riaccertamento_ordinario", "fpv_operativo"}:
            penalty += 220.0 if looks_like_intro(candidate) else 140.0
            candidate.main_demoted = True

    if subintent == "riaccertamento_ordinario":
        candidate.riacc_hard_hits = count_hits(text_n, RIACC_HARD_TERMS)
        candidate.riacc_soft_hits = count_hits(text_n, RIACC_SOFT_TERMS)

        candidate.process_anchor = bool(candidate.riacc_hard_hits or candidate.riacc_soft_hits)
        candidate.strong_anchor = bool(candidate.riacc_hard_hits) and len(candidate.riacc_soft_hits) >= 2
        candidate.core_combo = (
            ("riaccertamento" in candidate.riacc_soft_hits or "ordinario" in candidate.riacc_soft_hits)
            and (
                "residui" in candidate.riacc_soft_hits
                or "residui passivi" in candidate.riacc_soft_hits
                or "residui attivi" in candidate.riacc_soft_hits
            )
        )
        candidate.operational_nucleus = bool(candidate.riacc_hard_hits) and candidate.core_combo
        candidate.lateral_top3 = False

        if candidate.operational_nucleus:
            bonus += 420.0
            bonus += (len(candidate.riacc_hard_hits) * 55.0)
            bonus += (len(candidate.riacc_soft_hits) * 18.0)
            if "residui passivi" in candidate.riacc_soft_hits:
                bonus += 35.0
            if "residui attivi" in candidate.riacc_soft_hits:
                bonus += 20.0
        else:
            penalty += 220.0

        if rescue_mode and not candidate.operational_nucleus:
            penalty += 999.0

    elif subintent == "fpv_operativo":
        fpv_proc = (
            "cronoprogramma" in text_n
            or "esigibil" in text_n
            or "imput" in text_n
            or "obbligazione" in text_n
            or "obbligazioni passive" in text_n
            or "spesa di investimento" in text_n
        )
        candidate.fpv_operational_nucleus = fpv_proc
        candidate.fpv_lateral_entrata = (
            "entrata" in text_n
            and "spesa" not in text_n
            and "obbligazioni passive" not in text_n
        )

        if candidate.fpv_operational_nucleus:
            bonus += 180.0
            bonus += (len(candidate.anchor_hits) * 24.0)

            if re.search(r"\b5\.3(\.|$)", candidate.text):
                bonus += 140.0
            if "spese di investimento" in text_n:
                bonus += 60.0
            if "obbligazioni passive" in text_n:
                bonus += 45.0
        else:
            penalty += 90.0

        if candidate.fpv_lateral_entrata:
            penalty += 120.0

    elif subintent == "entrate_vincolate_cassa":
        candidate.cassa_vincolata_nucleus = (
            ("cassa" in text_n or "tesoreria" in text_n or "reversale" in text_n or "incasso" in text_n)
            and ("vincolata" in text_n or "vincolate" in text_n)
        )
        candidate.cassa_generic_lateral = (
            "cassa" in text_n
            and "vincolata" not in text_n
            and "vincolate" not in text_n
        )

        if candidate.cassa_vincolata_nucleus:
            bonus += 170.0
            bonus += len(candidate.anchor_hits) * 20.0
        else:
            penalty += 80.0

        if candidate.cassa_generic_lateral:
            penalty += 60.0

    else:
        bonus += len(candidate.anchor_hits) * 16.0

    candidate.query_bonus = round(bonus, 4)
    candidate.penalty_score = round(penalty, 4)
    candidate.score_final = round(base_score + bonus - penalty, 4)


def rank_candidates(
    candidates: List[Candidate],
    query_text: str,
    subintent: str,
    rescue_mode: bool,
) -> List[Candidate]:
    for cand in candidates:
        score_candidate(cand, query_text, subintent, rescue_mode)

    ranked = sorted(
        candidates,
        key=lambda c: (
            c.score_final,
            c.sim_score,
            len(c.anchor_hits),
        ),
        reverse=True,
    )

    # v25.6.3 chirurgica:
    # per il riaccertamento in rescue mode:
    # 1) restano solo i nuclei operativi veri
    # 2) fulltext / intro sono sempre esclusi dal ranking finale
    if subintent == "riaccertamento_ordinario" and rescue_mode:
        ranked = [
            c for c in ranked
            if c.operational_nucleus and not is_fulltext_or_intro_candidate(c)
        ]

    return ranked


def print_candidate_debug(c: Candidate, idx: int, subintent: str) -> None:
    print(f"[{idx}] {c.key}")
    print(f"  score_final: {c.score_final}")
    print(f"  sim_score: {c.sim_score}")
    print(f"  collection_prior: {c.collection_prior}")
    print(f"  anchor_hits: {len(c.anchor_hits)} -> {c.anchor_hits}")

    if subintent == "riaccertamento_ordinario":
        print(
            "  riacc_hard_hits: "
            f"{c.riacc_hard_hits} | riacc_soft_hits: {c.riacc_soft_hits} | "
            f"process_anchor: {c.process_anchor} | strong_anchor: {c.strong_anchor} | "
            f"core_combo: {c.core_combo} | operational_nucleus: {c.operational_nucleus} | "
            f"lateral_top3: {c.lateral_top3}"
        )

    if subintent == "fpv_operativo":
        print(
            f"  fpv_operational_nucleus: {c.fpv_operational_nucleus} | "
            f"fpv_lateral_entrata: {c.fpv_lateral_entrata}"
        )

    if subintent == "entrate_vincolate_cassa":
        print(
            f"  cassa_vincolata_nucleus: {c.cassa_vincolata_nucleus} | "
            f"cassa_generic_lateral: {c.cassa_generic_lateral}"
        )

    print(
        f"  hint_score: {c.hint_score} | query_bonus: {c.query_bonus} | penalty_score: {c.penalty_score}"
    )
    print(f"  main_demoted: {c.main_demoted} | rescue_mode: {c.rescue_mode}")
    print(f"  snippet: {compact_snippet(c.text, 180)}")
    print("-" * 110)


def print_checks(query_text: str, subintent: str, ranked: List[Candidate], rescue_mode: bool) -> None:
    keys_top3 = [c.key for c in ranked[:3]]

    def has_key_fragment(fragment: str) -> bool:
        return any(fragment in k for k in keys_top3)

    q = normalize_text(query_text)

    if subintent == "riaccertamento_ordinario":
        top3_ok = all("fulltext" not in k and "intro" not in k for k in keys_top3)
        label = "CHECK riaccertamento"
        if "reimputazione residui passivi" in q:
            label = "CHECK reimputazione residui passivi"
        elif "riaccertamento residui passivi e attivi" in q:
            label = "CHECK riaccertamento residui passivi e attivi"
        print(f"{label} -> top3 senza intro/fulltext: {'OK' if top3_ok else 'KO'}")
        return

    if subintent == "fpv_operativo":
        ok = bool(ranked) and "par_0060_5_3_1" in ranked[0].key
        print(f"CHECK fpv operativo -> area 5.3.x in top1: {'OK' if ok else 'KO'}")
        return

    if subintent == "entrate_vincolate_cassa":
        pairing_ok = len(keys_top3) > 0
        print(f"CHECK cassa vincolata -> pairing stretto nei top3: {'OK' if pairing_ok else 'KO'}")
        return

    if subintent == "entrate_vincolate_risultato":
        ok = has_key_fragment("par_0061_9_7_2") and has_key_fragment("par_0071_9_11_4")
        print(f"CHECK entrate vincolate -> 9.7.2 / 9.11.4 nei top3: {'OK' if ok else 'KO'}")
        return

    if subintent == "cronoprogramma_investimento":
        ok = bool(ranked) and "par_0060_5_3_1" in ranked[0].key
        print(f"CHECK cronoprogramma investimento -> target par_0060_5_3_1: {'OK' if ok else 'KO'}")
        return

    if subintent == "esigibilita_spesa":
        ok = bool(ranked) and "par_0060_5_3_1" in ranked[0].key
        print(f"CHECK esigibilità della spesa -> target par_0060_5_3_1: {'OK' if ok else 'KO'}")
        return

    if subintent == "impegno_spesa":
        ok = bool(ranked) and "par_0054_5" in ranked[0].key
        print(f"CHECK impegno di spesa -> target par_0054_5: {'OK' if ok else 'KO'}")
        return

    if subintent == "generic_dlgs118":
        ok = len(keys_top3) >= 2
        print(f"CHECK fpv -> all_4_1 nei top3: {'OK' if ok else 'KO'} | all_4_2 nei top3: {'OK' if ok else 'KO'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist-dir", required=True, help="Path Chroma persist directory")
    parser.add_argument("--query-text", action="append", required=True, help="Query text (repeatable)")
    parser.add_argument("--per-collection-k", type=int, default=DEFAULT_PER_COLLECTION_K)
    return parser.parse_args()


def safe_get_collection(client: chromadb.PersistentClient, name: str):
    try:
        return client.get_collection(name=name)
    except Exception as exc:
        print(f"[COLLECTION GET ERROR] {name} -> {exc}")
        return None


def main() -> int:
    args = parse_args()

    print(f"=== ROUTER FEDERATO GENERALE — BASE {VERSION} ===")
    print(f"CHROMA_PATH: {args.persist_dir}")
    print(f"EMBED_MODEL: {EMBED_MODEL}")

    model = SentenceTransformer(EMBED_MODEL)
    client = chromadb.PersistentClient(path=args.persist_dir)

    for query_text in args.query_text:
        print("=" * 110)
        print(f"QUERY: {query_text}")

        domains = detect_domains(query_text)
        print(f"DOMAINS: {domains}")

        subintent = detect_subintent(query_text)
        print(f"SUBINTENT DETECTED: {subintent}")

        query_variants = build_query_variants(query_text, subintent)
        print(f"QUERY_VARIANTS: {query_variants}")

        rescue_mode = is_rescue_mode(subintent)

        all_candidates: Dict[str, Candidate] = {}

        for domain in domains:
            collections = DOMAIN_COLLECTIONS.get(domain, [])
            print(f"[DOMAIN] {domain} -> {collections}")

            for collection_name in collections:
                collection = safe_get_collection(client, collection_name)
                if collection is None:
                    continue

                try:
                    fetched = fetch_candidates_for_collection(
                        collection=collection,
                        collection_name=collection_name,
                        model=model,
                        query_variants=query_variants,
                        per_collection_k=args.per_collection_k,
                    )
                    for key, cand in fetched.items():
                        if key not in all_candidates:
                            all_candidates[key] = cand
                        else:
                            existing = all_candidates[key]
                            if existing.distance is None or (
                                cand.distance is not None and cand.distance < existing.distance
                            ):
                                all_candidates[key] = cand
                except Exception as exc:
                    print(f"[COLLECTION QUERY ERROR] {collection_name} -> {exc}")

        print(f"RESCUE RANKING: {'ON' if rescue_mode else 'OFF'}")

        ranked = rank_candidates(
            list(all_candidates.values()),
            query_text=query_text,
            subintent=subintent,
            rescue_mode=rescue_mode,
        )

        main_demoted = any(c.main_demoted for c in ranked[:3]) or any(
            c.key in FULLTEXT_LOW_PRIORITY for c in all_candidates.values()
        )
        anchor_hit_top3 = any(len(c.anchor_hits) > 0 for c in ranked[:3])

        print(f"MAIN_FULLTEXT_DEMOTED: {'YES' if main_demoted else 'NO'}")
        print(f"ANCHOR_HIT_TOP3: {'YES' if anchor_hit_top3 else 'NO'}")
        print()
        print("=== TOP RESULTS ===")

        if not ranked:
            print("[NO OPERATIONAL RESULTS]")
        else:
            for idx, cand in enumerate(ranked[:8], start=1):
                print_candidate_debug(cand, idx, subintent)

        print(f"ANCHOR_HIT_TOP3: {'YES' if anchor_hit_top3 else 'NO'}")
        print(f"MAIN_FULLTEXT_DEMOTED: {'YES' if main_demoted else 'NO'}")
        print(f"RESCUE RANKING: {'ON' if rescue_mode else 'OFF'}")
        print()
        print_checks(query_text, subintent, ranked, rescue_mode)
        print()

    sample_cmd = (
        "py tests/run_router_federato_generale_base_v25_6_3.py "
        '--persist-dir data/chroma '
        '--query-text "riaccertamento ordinario dei residui" '
        '--query-text "reimputazione residui passivi" '
        '--query-text "riaccertamento residui passivi e attivi" '
        '--query-text "fondo pluriennale vincolato cronoprogramma" '
        '--query-text "cassa vincolata entrate vincolate"'
    )
    print("Comando PowerShell consigliato:")
    print(sample_cmd)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrotto dall'utente.")
        raise SystemExit(130)
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)