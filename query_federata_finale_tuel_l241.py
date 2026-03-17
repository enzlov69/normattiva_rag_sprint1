#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import chromadb
from sentence_transformers import SentenceTransformer

DEFAULT_PERSIST_DIR = "data/chroma"
DEFAULT_COLLECTIONS = ["normattiva_tuel_267_2000", "normattiva_l241_1990"]
DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_SEMANTIC_K = 12
DEFAULT_LEXICAL_K = 8
DEFAULT_FINAL_K = 10

ARTICLE_REF_RE = re.compile(r"\bart\.?\s*(\d+[\-a-z]*)\b", re.IGNORECASE)
LEADING_ARTICLE_RE = re.compile(r"^(?:Art(?:icolo)?\.?)\s*(\d+[\-a-z]*)", re.IGNORECASE)
WS_RE = re.compile(r"\s+")


@dataclass
class Candidate:
    chunk_id: str
    collection: str
    domain_code: str
    citation_text: str
    rubrica: str
    uri: str
    testo: str
    distanza: Optional[float]
    semantic_score: float
    lexical_score: float
    overlap_score: float
    legal_boost: float
    article_boost: float
    concept_boost: float
    abrogation_penalty: float
    score_totale: float
    metadata: Dict[str, Any]


def normalize_text(text: str) -> str:
    text = (text or "").replace("’", "'").replace("`", "'")
    text = text.lower()
    text = re.sub(r"[^a-z0-9àèéìòù'\-\. ]+", " ", text)
    return WS_RE.sub(" ", text).strip()


def tokenize(text: str) -> List[str]:
    return [t for t in normalize_text(text).split() if t]


def extract_article_ref(text: str) -> Optional[str]:
    m = ARTICLE_REF_RE.search(text or "")
    if not m:
        return None
    return normalize_article_token(m.group(1))


def normalize_article_token(token: str) -> str:
    token = (token or "").lower().strip().replace(" ", "-")
    token = token.replace("–", "-")
    return token


def safe_float(v: Any) -> Optional[float]:
    try:
        return float(v)
    except Exception:
        return None


def semantic_to_score(distance: Optional[float]) -> float:
    if distance is None:
        return 0.0
    # Higher is better. Tuned to the user's current distance ranges.
    return max(0.0, 100.0 - (distance * 120.0))


def extract_rubrica(candidate: Dict[str, Any]) -> str:
    rubrica = (candidate.get("rubrica") or "").strip()
    if rubrica:
        return clean_rubrica(rubrica)
    text = candidate.get("testo") or ""
    m = re.search(r"^(?:Art(?:icolo)?\.?\s*\d+[\-a-z]*\s*)([^\n]{5,220})", text, re.IGNORECASE)
    if m:
        return clean_rubrica(m.group(1))
    return ""


def clean_rubrica(text: str) -> str:
    text = text.replace("((", "").replace("))", "")
    text = text.replace("( (", "(").replace(") )", ")")
    text = text.replace("..", ".")
    text = WS_RE.sub(" ", text).strip(" .-;:")
    return text


def abrogation_penalty(text: str, rubrica: str) -> float:
    hay = f"{rubrica} {text}".upper()
    penalty = 0.0
    if "ARTICOLO ABROGATO" in hay:
        penalty -= 260.0
    if "COMMA ABROGATO" in hay:
        penalty -= 75.0
    return penalty


def get_article_key_from_candidate(md: Dict[str, Any], chunk_id: str, citation_text: str, text: str) -> Optional[str]:
    for key in ("article_label_slug", "article_label_original", "articolo", "article"):
        if md.get(key):
            return normalize_article_token(str(md[key]))
    m = re.search(r"_art_([0-9]+(?:_[a-z]+)?)_", chunk_id)
    if m:
        return m.group(1).replace("_", "-")
    m = re.search(r"art\.\s*(\d+[\-a-z]*)", citation_text or "", re.IGNORECASE)
    if m:
        return normalize_article_token(m.group(1))
    m = LEADING_ARTICLE_RE.search(text or "")
    if m:
        return normalize_article_token(m.group(1))
    return None


def lexical_score_for_query(q_norm: str, rubrica: str, text: str, citation_text: str) -> float:
    score = 0.0
    rub_n = normalize_text(rubrica)
    text_n = normalize_text(text)
    cit_n = normalize_text(citation_text)
    if q_norm and q_norm in rub_n:
        score += 275.0
    if q_norm and q_norm in cit_n:
        score += 180.0
    if q_norm and q_norm in text_n:
        score += 120.0
    # token overlap
    q_tokens = tokenize(q_norm)
    if q_tokens:
        rub_tokens = set(tokenize(rub_n))
        text_tokens = set(tokenize(text_n))
        matched_rub = sum(1 for t in q_tokens if t in rub_tokens)
        matched_text = sum(1 for t in q_tokens if t in text_tokens)
        score += matched_rub * 35.0
        score += min(matched_text, max(1, len(q_tokens))) * 15.0
    return score


def overlap_score(q_norm: str, rubrica: str, text: str) -> float:
    q_tokens = set(tokenize(q_norm))
    if not q_tokens:
        return 0.0
    cand_tokens = set(tokenize(rubrica)) | set(tokenize(text[:1200]))
    inter = q_tokens & cand_tokens
    return float(len(inter) * 20)


def build_concept_profile(query_text: str) -> Dict[str, Any]:
    q = normalize_text(query_text)
    article_ref = extract_article_ref(q)

    profile: Dict[str, Any] = {
        "query_norm": q,
        "article_ref": article_ref,
        "aliases": [],
        "preferred_articles": {},   # article_key -> boost
        "domain_boosts": {},        # domain -> boost
    }

    def add_pref(article: str, boost: float) -> None:
        profile["preferred_articles"][normalize_article_token(article)] = boost

    # L. 241/1990
    if "annullamento d'ufficio" in q:
        add_pref("21-novies", 320.0)
        profile["aliases"].extend(["annullamento d ufficio", "21 novies", "art 21 novies"])
        profile["domain_boosts"]["l241_1990"] = 45.0

    if "silenzio assenso" in q:
        add_pref("20", 320.0)
        add_pref("17-bis", 90.0)
        profile["aliases"].extend(["silenzio assenso", "art 20"])
        profile["domain_boosts"]["l241_1990"] = 45.0

    if "responsabile del procedimento" in q:
        add_pref("6", 300.0)
        add_pref("4", 270.0)
        add_pref("5", 240.0)
        add_pref("6-bis", 60.0)
        profile["aliases"].extend(["responsabile procedimento", "art 4", "art 5", "art 6"])
        profile["domain_boosts"]["l241_1990"] = 45.0

    if "preavviso di rigetto" in q or "motivi ostativi" in q:
        add_pref("10-bis", 460.0)
        profile["aliases"].extend([
            "preavviso rigetto",
            "motivi ostativi accoglimento istanza",
            "art 10 bis",
            "art 10-bis",
        ])
        profile["domain_boosts"]["l241_1990"] = 45.0

    if "accesso ai documenti amministrativi" in q or "diritto di accesso" in q or "accesso documentale" in q:
        add_pref("25", 520.0)
        add_pref("22", 550.0)
        add_pref("24", 450.0)
        add_pref("23", 420.0)
        add_pref("27", 10.0)
        add_pref("28", 0.0)
        profile["aliases"].extend([
            "documenti amministrativi",
            "diritto di accesso",
            "accesso documentale",
            "art 22",
            "art 25",
        ])
        profile["domain_boosts"]["l241_1990"] = 45.0

    # TUEL
    if "debiti fuori bilancio" in q:
        add_pref("194", 815.0)
        add_pref("193", 180.0)
        add_pref("191", 155.0)
        add_pref("202", -35.0)
        profile["aliases"].extend(["debiti fuori bilancio", "riconoscimento di legittimita di debiti fuori bilancio", "art 194"])
        profile["domain_boosts"]["tuel_267_2000"] = 60.0
        profile["domain_boosts"]["norme"] = 60.0

    if "fondo di riserva" in q:
        add_pref("176", 550.0)
        add_pref("166", 540.0)
        add_pref("167", 115.0)
        profile["aliases"].extend(["fondo di riserva", "prelevamenti dal fondo di riserva", "art 166", "art 176"])
        profile["domain_boosts"]["tuel_267_2000"] = 60.0
        profile["domain_boosts"]["norme"] = 60.0

    if any(x in q for x in ["pareri ex art. 49", "pareri ex art 49", "pareri art 49", "pareri ex articolo 49", "art. 49", "art 49", "articolo 49"]):
        add_pref("49", 2895.0)
        profile["aliases"].extend([
            "art 49",
            "articolo 49",
            "pareri dei responsabili dei servizi",
            "regolarita tecnica",
            "regolarita contabile",
            "pareri responsabili servizi",
        ])
        profile["domain_boosts"]["tuel_267_2000"] = 60.0
        profile["domain_boosts"]["norme"] = 60.0

    if article_ref:
        profile["preferred_articles"].setdefault(article_ref, 160.0)

    return profile


def candidate_from_chroma(doc: str, md: Dict[str, Any], distance: Optional[float], collection_name: str) -> Dict[str, Any]:
    chunk_id = str(md.get("chunk_id") or md.get("id") or "")
    citation_text = str(md.get("citation_text") or md.get("citazione") or "")
    domain_code = str(md.get("domain_code") or md.get("dominio") or "")
    uri = str(md.get("uri_ufficiale") or md.get("uri") or "")
    return {
        "chunk_id": chunk_id,
        "collection": collection_name,
        "domain_code": domain_code,
        "citation_text": citation_text,
        "rubrica": extract_rubrica({"rubrica": md.get("rubrica"), "testo": doc}),
        "uri": uri,
        "testo": doc or "",
        "distanza": distance,
        "metadata": dict(md or {}),
    }


def semantic_retrieve(client: chromadb.PersistentClient, collection_name: str, query_text: str, model: SentenceTransformer, k: int) -> List[Dict[str, Any]]:
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        return []
    emb = model.encode(query_text).tolist()
    res = collection.query(query_embeddings=[emb], n_results=k, include=["documents", "metadatas", "distances"])
    docs = (res.get("documents") or [[]])[0]
    mds = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    out: List[Dict[str, Any]] = []
    for doc, md, dist in zip(docs, mds, dists):
        out.append(candidate_from_chroma(doc, md or {}, safe_float(dist), collection_name))
    return out


def lexical_retrieve(client: chromadb.PersistentClient, collection_name: str, query_text: str, profile: Dict[str, Any], k: int) -> List[Dict[str, Any]]:
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        return []
    # Pull a manageable superset. 500 is fine for the user's current collection sizes.
    items = collection.get(include=["documents", "metadatas"], limit=500)
    docs = items.get("documents") or []
    mds = items.get("metadatas") or []
    q_norm = profile["query_norm"]
    aliases = [normalize_text(a) for a in profile.get("aliases", []) if a]
    article_ref = profile.get("article_ref")
    preferred_articles = {normalize_article_token(a) for a in profile.get("preferred_articles", {}).keys()}

    scored: List[Tuple[float, Dict[str, Any]]] = []
    for doc, md in zip(docs, mds):
        cand = candidate_from_chroma(doc, md or {}, None, collection_name)
        rub = cand["rubrica"]
        text = cand["testo"]
        citation = cand["citation_text"]
        article_key = get_article_key_from_candidate(cand["metadata"], cand["chunk_id"], citation, text)

        lex = lexical_score_for_query(q_norm, rub, text, citation)
        ov = overlap_score(q_norm, rub, text)
        extra = 0.0
        joined = normalize_text(f"{rub} {citation} {text[:1800]}")
        for alias in aliases:
            if alias and alias in joined:
                extra += 110.0
        if article_ref and article_key == article_ref:
            extra += 180.0
        if article_key in preferred_articles:
            extra += 140.0

        total = lex + ov + extra
        if total > 0:
            scored.append((total, cand))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [cand for _, cand in scored[:k]]


def score_candidate(query_text: str, cand: Dict[str, Any]) -> Candidate:
    q_norm = normalize_text(query_text)
    profile = build_concept_profile(query_text)
    rub = cand["rubrica"]
    text = cand["testo"]
    citation_text = cand["citation_text"]
    article_key = get_article_key_from_candidate(cand["metadata"], cand["chunk_id"], citation_text, text)

    sem = semantic_to_score(cand["distanza"])
    lex = lexical_score_for_query(q_norm, rub, text, citation_text)
    ov = overlap_score(q_norm, rub, text)
    legal = profile.get("domain_boosts", {}).get(cand["domain_code"], 0.0)
    article = 0.0
    concept = 0.0

    if article_key and article_key == profile.get("article_ref"):
        article += 160.0
    if article_key and article_key in profile.get("preferred_articles", {}):
        concept += float(profile["preferred_articles"][article_key])
    # stronger art.49 recognition across fields
    if profile.get("article_ref") == "49":
        cid = cand["chunk_id"].lower()
        cit = (citation_text or "").lower()
        leading = (text[:120] or "").lower()
        if "_art_49_" in cid or "art. 49" in cit or "articolo 49" in leading or "art. 49" in leading:
            article += 810.0

    # extra alias-based concept support
    joined = normalize_text(f"{rub} {citation_text} {text[:2200]}")
    for alias in profile.get("aliases", []):
        alias_n = normalize_text(alias)
        if alias_n and alias_n in joined:
            concept += 55.0

    abr = abrogation_penalty(text, rub)
    total = sem + lex + ov + legal + article + concept + abr

    return Candidate(
        chunk_id=cand["chunk_id"],
        collection=cand["collection"],
        domain_code=cand["domain_code"],
        citation_text=citation_text,
        rubrica=rub,
        uri=cand["uri"],
        testo=text,
        distanza=cand["distanza"],
        semantic_score=round(sem, 4),
        lexical_score=round(lex, 4),
        overlap_score=round(ov, 4),
        legal_boost=round(legal, 4),
        article_boost=round(article, 4),
        concept_boost=round(concept, 4),
        abrogation_penalty=round(abr, 4),
        score_totale=round(total, 4),
        metadata=cand["metadata"],
    )


def run_query(client: chromadb.PersistentClient, collections: List[str], model: SentenceTransformer, query_text: str,
              semantic_k: int, lexical_k: int, final_k: int) -> List[Candidate]:
    merged: Dict[str, Dict[str, Any]] = {}
    profile = build_concept_profile(query_text)

    for cname in collections:
        sem_candidates = semantic_retrieve(client, cname, query_text, model, semantic_k)
        lex_candidates = lexical_retrieve(client, cname, query_text, profile, lexical_k)
        for cand in [*sem_candidates, *lex_candidates]:
            key = f"{cname}::{cand['chunk_id']}"
            if key not in merged:
                merged[key] = cand
            else:
                # keep semantic distance if available, merge metadata conservatively
                if merged[key].get("distanza") is None and cand.get("distanza") is not None:
                    merged[key]["distanza"] = cand["distanza"]

    scored = [score_candidate(query_text, cand) for cand in merged.values()]
    scored.sort(key=lambda c: c.score_totale, reverse=True)
    return scored[:final_k]


def print_results(label: str, results: List[Candidate]) -> None:
    print(f"\nQuery federata finale: {label}")
    for idx, c in enumerate(results, start=1):
        print(f"  [{idx}] chunk_id={c.chunk_id}")
        print(f"      collection={c.collection}")
        print(f"      dominio={c.domain_code}")
        print(f"      citazione={c.citation_text}")
        print(f"      rubrica={c.rubrica}")
        print(f"      score_totale={c.score_totale}")
        print(f"      semantic_score={c.semantic_score}")
        print(f"      lexical_score={c.lexical_score}")
        print(f"      overlap_score={c.overlap_score}")
        print(f"      legal_boost={c.legal_boost}")
        print(f"      article_boost={c.article_boost}")
        print(f"      concept_boost={c.concept_boost}")
        print(f"      abrogation_penalty={c.abrogation_penalty}")
        print(f"      distanza={c.distanza}")
        print(f"      uri={c.uri}")
        testo = c.testo.replace("\n", " ")
        if len(testo) > 520:
            testo = testo[:520] + "..."
        print(f"      testo={testo}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Query federata finale armonizzata TUEL + L. 241/1990")
    p.add_argument("--persist-dir", default=DEFAULT_PERSIST_DIR)
    p.add_argument("--collection", action="append", default=None,
                   help="Collection da interrogare. Default: normattiva_tuel_267_2000 + normattiva_l241_1990")
    p.add_argument("--query-text", action="append", required=True)
    p.add_argument("--embedding-model", default=DEFAULT_MODEL)
    p.add_argument("--semantic-k", type=int, default=DEFAULT_SEMANTIC_K)
    p.add_argument("--lexical-k", type=int, default=DEFAULT_LEXICAL_K)
    p.add_argument("--final-k", type=int, default=DEFAULT_FINAL_K)
    p.add_argument("--output-json", default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    collections = args.collection or DEFAULT_COLLECTIONS
    client = chromadb.PersistentClient(path=args.persist_dir)
    model = SentenceTransformer(args.embedding_model)

    all_results: Dict[str, List[Dict[str, Any]]] = {}
    for q in args.query_text:
        results = run_query(client, collections, model, q, args.semantic_k, args.lexical_k, args.final_k)
        print_results(q, results)
        all_results[q] = [
            {
                **{k: v for k, v in asdict(c).items() if k != "metadata"},
                "metadata": c.metadata,
            }
            for c in results
        ]

    if args.output_json:
        out_path = Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "collections": collections,
            "persist_dir": args.persist_dir,
            "embedding_model": args.embedding_model,
            "results": all_results,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nOutput JSON scritto in: {out_path}")


if __name__ == "__main__":
    main()
