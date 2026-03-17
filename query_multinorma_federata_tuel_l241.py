#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import chromadb
except Exception as e:  # pragma: no cover
    print("Errore: chromadb non installato. Esegui: pip install chromadb", file=sys.stderr)
    raise

try:
    from sentence_transformers import SentenceTransformer
except Exception as e:  # pragma: no cover
    print(
        "Errore: sentence-transformers non installato. Esegui: pip install sentence-transformers",
        file=sys.stderr,
    )
    raise


DEFAULT_COLLECTIONS = ["normattiva_tuel", "normattiva_l241_1990"]
DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
STOPWORDS = {
    "a", "ad", "ai", "agli", "al", "all", "alla", "alle", "allo", "con", "da", "dal", "dalla",
    "dalle", "dei", "del", "della", "delle", "di", "e", "ed", "gli", "i", "il", "in", "la", "le",
    "lo", "nei", "nel", "nella", "nelle", "o", "per", "su", "tra", "un", "una", "uno", "dei",
    "degli", "dello", "dell", "dell'", "sull", "sull'", "sui", "sulle", "suo", "sua", "sue", "l",
    "l'", "d", "d'", "ex", "art", "art.", "comma", "commi",
}

ARTICLE_IN_TEXT_RE = re.compile(
    r"^Art\.\s*(\d+(?:[-\s](?:bis|ter|quater|quinquies|sexies|septies|octies|novies|nonies|decies))?)"
    r"(?:\s*\((.*?)\))?",
    re.IGNORECASE,
)
ARTICLE_REF_RE = re.compile(
    r"art\.?\s*(\d+(?:[-\s](?:bis|ter|quater|quinquies|sexies|septies|octies|novies|nonies|decies))?)",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = text.replace("’", "'")
    text = re.sub(r"[^a-z0-9\-\s']+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def canonical_article_label(label: str) -> str:
    s = normalize_text(label)
    s = s.replace("art", "").replace(".", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace(" ", "-")
    s = s.replace("nonies", "novies")
    return s


def tokenize(text: str) -> List[str]:
    text = normalize_text(text)
    tokens = [t for t in re.split(r"\s+", text) if t and t not in STOPWORDS]
    return tokens


def infer_rubrica(document: str, metadata: Dict[str, Any]) -> str:
    for key in ("rubrica", "article_rubrica", "rubrica_articolo", "title", "heading"):
        value = (metadata or {}).get(key)
        if isinstance(value, str) and value.strip():
            cleaned = value.strip().strip("() ")
            cleaned = re.sub(r"^\(+|\)+$", "", cleaned).strip()
            if cleaned:
                return cleaned
    first_line = (document or "").splitlines()[0] if document else ""
    m = ARTICLE_IN_TEXT_RE.search(first_line)
    if m and m.group(2):
        cleaned = re.sub(r"^\(+|\)+$", "", m.group(2)).strip()
        if cleaned:
            return cleaned
    return ""


def infer_article_label(document: str, metadata: Dict[str, Any]) -> str:
    for key in ("article_label", "article_label_original", "articolo", "article"):
        value = (metadata or {}).get(key)
        if isinstance(value, str) and value.strip():
            return canonical_article_label(value)
    citation = (metadata or {}).get("citation_text", "")
    m = ARTICLE_REF_RE.search(citation)
    if m:
        return canonical_article_label(m.group(1))
    first_line = (document or "").splitlines()[0] if document else ""
    m = ARTICLE_IN_TEXT_RE.search(first_line)
    if m:
        return canonical_article_label(m.group(1))
    return ""


def infer_domain(collection_name: str, metadata: Dict[str, Any]) -> str:
    domain = (metadata or {}).get("domain_code") or (metadata or {}).get("domain")
    if isinstance(domain, str) and domain.strip():
        return domain.strip()
    if "241" in (collection_name or ""):
        return "l241_1990"
    if "tuel" in (collection_name or "").lower() or "267" in (collection_name or ""):
        return "tuel"
    return collection_name or "unknown"


def build_citation(metadata: Dict[str, Any], article_label: str) -> str:
    if metadata.get("citation_text"):
        return str(metadata["citation_text"])
    domain = infer_domain("", metadata)
    if domain == "l241_1990":
        return f"Legge n. 241/1990, art. {article_label}"
    if domain == "tuel":
        return f"D.Lgs. n. 267/2000, art. {article_label}"
    return f"art. {article_label}"


@dataclass
class Candidate:
    collection: str
    domain: str
    chunk_id: str
    document: str
    metadata: Dict[str, Any]
    distance: float
    article_label: str
    rubrica: str
    citation: str
    uri: str


L241_CONCEPTS = {
    "annullamento d'ufficio": {
        "aliases": ["annullamento d ufficio", "21 novies", "21-novies"],
        "preferred": {"21-novies": 320},
    },
    "silenzio assenso": {
        "aliases": ["silenzio-assenso", "art 20", "20"],
        "preferred": {"20": 320, "17-bis": 90},
    },
    "responsabile del procedimento": {
        "aliases": ["rup procedimento", "responsabile procedimento", "art 4", "art 5", "art 6"],
        "preferred": {"6": 300, "4": 270, "5": 240},
    },
    "preavviso di rigetto": {
        "aliases": [
            "motivi ostativi all accoglimento dell istanza",
            "comunicazione dei motivi ostativi",
            "art 10 bis",
            "10-bis",
        ],
        "preferred": {"10-bis": 460},
    },
    "accesso ai documenti amministrativi": {
        "aliases": ["diritto di accesso", "accesso documentale", "documenti amministrativi"],
        "preferred": {"22": 550, "25": 520, "24": 450, "23": 420, "26": 320, "27": 10, "28": 0},
    },
}

TUEL_CONCEPTS = {
    "debiti fuori bilancio": {
        "aliases": [
            "riconoscimento debiti fuori bilancio",
            "debito fuori bilancio",
            "art 194",
            "194",
        ],
        "preferred": {"194": 420, "193": 120},
    },
    "fondo di riserva": {
        "aliases": ["prelevamento fondo di riserva", "art 166", "art 176", "166", "176"],
        "preferred": {"166": 320, "176": 240},
    },
    "pareri ex art 49": {
        "aliases": ["pareri art 49", "parere art 49", "regolarita tecnica e contabile", "49"],
        "preferred": {"49": 360},
    },
}

DOMAIN_HINTS = {
    "l241_1990": [
        "procedimento", "istanza", "accesso", "silenzio assenso", "annullamento d'ufficio",
        "preavviso di rigetto", "motivi ostativi", "responsabile del procedimento",
    ],
    "tuel": [
        "ente locale", "consiglio comunale", "giunta", "sindaco", "bilancio", "debiti fuori bilancio",
        "fondo di riserva", "pareri ex art 49", "responsabile del servizio", "tuel",
    ],
}

GENERAL_ACCESS_TERMS = [
    "accesso ai documenti amministrativi",
    "diritto di accesso",
    "accesso documentale",
    "accesso ai documenti",
]
SPECIFIC_ACCESS_TERMS = ["commissione", "difensore civico", "ricorsi", "presidenza del consiglio"]


def semantic_score(distance: float) -> float:
    if distance is None:
        return 0.0
    return max(0.0, (1.0 - float(distance)) * 75.0)


def lexical_score(query_norm: str, cand: Candidate) -> float:
    score = 0.0
    rubrica_norm = normalize_text(cand.rubrica)
    citation_norm = normalize_text(cand.citation)
    doc_norm = normalize_text(cand.document[:1800])

    if query_norm and query_norm in rubrica_norm:
        score += 275.0
    if query_norm and query_norm in citation_norm:
        score += 150.0
    if query_norm and query_norm in doc_norm:
        score += 120.0

    q_tokens = tokenize(query_norm)
    rub_tokens = set(tokenize(rubrica_norm))
    cit_tokens = set(tokenize(citation_norm))
    doc_tokens = set(tokenize(doc_norm))

    for tok in q_tokens:
        if tok in rub_tokens:
            score += 70.0
        elif tok in cit_tokens:
            score += 35.0
        elif tok in doc_tokens:
            score += 15.0
    return score


def overlap_score(query_norm: str, cand: Candidate) -> float:
    q_tokens = set(tokenize(query_norm))
    c_tokens = set(tokenize(" ".join([cand.rubrica, cand.citation, cand.document[:1200]])))
    shared = q_tokens.intersection(c_tokens)
    if not shared:
        return 0.0
    score = 0.0
    for tok in shared:
        if tok.isdigit():
            score += 18.0
        elif len(tok) >= 8:
            score += 14.0
        else:
            score += 7.0
    return score


def article_boost(query_norm: str, cand: Candidate) -> float:
    boost = 0.0
    article_refs = ARTICLE_REF_RE.findall(query_norm)
    if not article_refs:
        return 0.0
    candidate_label = canonical_article_label(cand.article_label)
    for ref in article_refs:
        if canonical_article_label(ref) == candidate_label:
            boost += 250.0
    return boost


def domain_hint_boost(query_norm: str, cand: Candidate) -> float:
    hints = DOMAIN_HINTS.get(cand.domain, [])
    for hint in hints:
        if normalize_text(hint) in query_norm:
            return 45.0
    return 0.0


def concept_boost(query_norm: str, cand: Candidate) -> float:
    concepts = L241_CONCEPTS if cand.domain == "l241_1990" else TUEL_CONCEPTS if cand.domain == "tuel" else {}
    candidate_label = canonical_article_label(cand.article_label)
    best = 0.0
    for concept, payload in concepts.items():
        concept_norm = normalize_text(concept)
        aliases = [concept_norm] + [normalize_text(x) for x in payload.get("aliases", [])]
        if any(alias and alias in query_norm for alias in aliases):
            best = max(best, float(payload.get("preferred", {}).get(candidate_label, 0.0)))
    return best


def legal_boost(query_norm: str, cand: Candidate) -> float:
    score = 0.0
    combined = normalize_text(" ".join([cand.rubrica, cand.citation, cand.document[:1500]]))
    q_tokens = tokenize(query_norm)
    for tok in q_tokens:
        if tok in combined:
            if len(tok) >= 10:
                score += 18.0
            elif len(tok) >= 7:
                score += 12.0
            else:
                score += 6.0
    score += domain_hint_boost(query_norm, cand)

    # Regola minima per query generale sull'accesso: privilegia 22-25, deprime 27-28 salvo termini specifici.
    is_general_access = any(normalize_text(x) in query_norm for x in map(str, GENERAL_ACCESS_TERMS))
    is_specific_access = any(normalize_text(x) in query_norm for x in map(str, SPECIFIC_ACCESS_TERMS))
    if cand.domain == "l241_1990" and is_general_access and not is_specific_access:
        label = canonical_article_label(cand.article_label)
        if label in {"22", "23", "24", "25"}:
            score += 35.0
        elif label in {"27", "28"}:
            score -= 45.0
    return score


def score_candidate(query: str, cand: Candidate) -> Dict[str, float]:
    qn = normalize_text(query)
    scores = {
        "semantic_score": round(semantic_score(cand.distance), 4),
        "lexical_score": round(lexical_score(qn, cand), 4),
        "overlap_score": round(overlap_score(qn, cand), 4),
        "legal_boost": round(legal_boost(qn, cand), 4),
        "article_boost": round(article_boost(qn, cand), 4),
        "concept_boost": round(concept_boost(qn, cand), 4),
    }
    scores["score_totale"] = round(sum(scores.values()), 4)
    return scores


def unique_candidates(candidates: List[Candidate]) -> List[Candidate]:
    seen = set()
    out = []
    for c in candidates:
        key = (c.collection, c.chunk_id)
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def fetch_candidates(
    client: "chromadb.PersistentClient",
    model: SentenceTransformer,
    collections: List[str],
    query_text: str,
    n_results: int,
) -> List[Candidate]:
    embedding = model.encode(query_text, normalize_embeddings=True).tolist()
    collected: List[Candidate] = []

    for name in collections:
        try:
            coll = client.get_collection(name)
        except Exception:
            print(f"Attenzione: collection non trovata: {name}", file=sys.stderr)
            continue

        result = coll.query(
            query_embeddings=[embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0] if "ids" in result else [""] * len(docs)

        for doc, meta, dist, cid in zip(docs, metas, dists, ids):
            meta = meta or {}
            rubrica = infer_rubrica(doc or "", meta)
            art_label = infer_article_label(doc or "", meta)
            citation = build_citation(meta, art_label)
            uri = str(meta.get("uri_ufficiale") or meta.get("uri") or "")
            domain = infer_domain(name, meta)
            collected.append(
                Candidate(
                    collection=name,
                    domain=domain,
                    chunk_id=str(cid or meta.get("chunk_id") or ""),
                    document=str(doc or ""),
                    metadata=meta,
                    distance=float(dist) if dist is not None else 1.0,
                    article_label=art_label,
                    rubrica=rubrica,
                    citation=citation,
                    uri=uri,
                )
            )
    return unique_candidates(collected)


def render_result(query: str, ranked: List[Dict[str, Any]]) -> None:
    print(f"\nQuery federata: {query}")
    for idx, row in enumerate(ranked, start=1):
        print(f"  [{idx}] chunk_id={row['chunk_id']}")
        print(f"      collection={row['collection']}")
        print(f"      dominio={row['domain']}")
        print(f"      citazione={row['citation']}")
        print(f"      rubrica={row['rubrica']}")
        print(f"      score_totale={row['score_totale']}")
        print(f"      semantic_score={row['semantic_score']}")
        print(f"      lexical_score={row['lexical_score']}")
        print(f"      overlap_score={row['overlap_score']}")
        print(f"      legal_boost={row['legal_boost']}")
        print(f"      article_boost={row['article_boost']}")
        print(f"      concept_boost={row['concept_boost']}")
        print(f"      distanza={row['distance']}")
        print(f"      uri={row['uri']}")
        text = row["document"].replace("\n", " ")
        if len(text) > 420:
            text = text[:417] + "..."
        print(f"      testo={text}")


def run_query(
    client: "chromadb.PersistentClient",
    model: SentenceTransformer,
    collections: List[str],
    query_text: str,
    per_collection_k: int,
    final_top_k: int,
) -> List[Dict[str, Any]]:
    candidates = fetch_candidates(client, model, collections, query_text, per_collection_k)
    rows: List[Dict[str, Any]] = []
    for cand in candidates:
        scores = score_candidate(query_text, cand)
        row = {
            "collection": cand.collection,
            "domain": cand.domain,
            "chunk_id": cand.chunk_id,
            "citation": cand.citation,
            "rubrica": cand.rubrica,
            "distance": cand.distance,
            "uri": cand.uri,
            "article_label": cand.article_label,
            "document": cand.document,
            **scores,
        }
        rows.append(row)
    rows.sort(key=lambda x: (-x["score_totale"], x["distance"], x["chunk_id"]))
    return rows[:final_top_k]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Query multi-norma federata TUEL + L. 241/1990 con collection separate e reranking finale unico."
    )
    ap.add_argument("--persist-dir", default="data/chroma", help="Directory persistente di ChromaDB")
    ap.add_argument(
        "--collection",
        action="append",
        dest="collections",
        default=[],
        help="Collection da interrogare. Ripetibile. Default: normattiva_tuel + normattiva_l241_1990",
    )
    ap.add_argument("--query-text", action="append", required=True, help="Query da eseguire. Ripetibile.")
    ap.add_argument("--per-collection-k", type=int, default=8, help="Candidati semantici per ciascuna collection")
    ap.add_argument("--final-top-k", type=int, default=10, help="Risultati finali dopo reranking federato")
    ap.add_argument("--embedding-model", default=DEFAULT_MODEL, help="Modello sentence-transformers")
    ap.add_argument("--output-json", help="Scrive i risultati completi in JSON")
    return ap


def main() -> int:
    args = build_parser().parse_args()
    persist_dir = Path(args.persist_dir)
    collections = args.collections or DEFAULT_COLLECTIONS

    client = chromadb.PersistentClient(path=str(persist_dir))
    model = SentenceTransformer(args.embedding_model)

    all_results: Dict[str, Any] = {
        "persist_dir": str(persist_dir),
        "collections": collections,
        "queries": [],
    }

    for query in args.query_text:
        ranked = run_query(
            client=client,
            model=model,
            collections=collections,
            query_text=query,
            per_collection_k=args.per_collection_k,
            final_top_k=args.final_top_k,
        )
        render_result(query, ranked)
        all_results["queries"].append({"query_text": query, "results": ranked})

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nOutput JSON scritto in: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
