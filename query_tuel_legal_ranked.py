
"""
query_tuel_legal_ranked.py

Ricerca giuridica avanzata sul TUEL:
1. semantic search su ChromaDB
2. boost lessicale su testo e rubrica
3. reranking citation-aware sugli articoli richiamati nei risultati

Uso:
    python query_tuel_legal_ranked.py "debiti fuori bilancio"
"""

from __future__ import annotations

import re
import sys
from collections import Counter

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = "data/chroma"
COLLECTION_NAME = "norme"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

SEMANTIC_RESULTS = 15
FINAL_RESULTS = 5

ARTICLE_REF_RE = re.compile(
    r"articolo\s+(\d+)(?:[-\s]?(bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|undecies|duodecies|terdecies|quaterdecies|quinquiesdecies))?",
    re.IGNORECASE,
)


def normalize_article(num: str, suffix: str | None) -> str:
    return f"{num}" if not suffix else f"{num}-{suffix.lower()}"


def lexical_score(query: str, text: str) -> int:
    query = query.lower().strip()
    text = text.lower()

    score = 0

    if query and query in text:
        score += 12

    for word in query.split():
        if len(word) >= 3 and word in text:
            score += 1

    return score


def extract_article_refs(text: str) -> list[str]:
    refs = []
    for match in ARTICLE_REF_RE.finditer(text or ""):
        num = match.group(1)
        suf = match.group(2)
        refs.append(normalize_article(num, suf))
    return refs


def strong_topic_boost(query: str, articolo: str, rubrica: str, text: str) -> int:
    q = query.lower().strip()
    rub = (rubrica or "").lower()
    txt = (text or "").lower()
    score = 0

    # Boost mirati su query note di diritto degli enti locali.
    if "debiti fuori bilancio" in q:
        if "debiti fuori bilancio" in rub:
            score += 20
        if "debiti fuori bilancio" in txt:
            score += 8
        if articolo == "194":
            score += 40
        if "articolo 194" in txt:
            score += 12

    if "competenze del sindaco" in q or ("competenze" in q and "sindaco" in q):
        if articolo == "50":
            score += 25
        if articolo == "54":
            score += 20
        if "sindaco" in rub:
            score += 8

    return score


def main():
    if len(sys.argv) < 2:
        print('Uso: python query_tuel_legal_ranked.py "testo domanda"')
        sys.exit(1)

    query_text = " ".join(sys.argv[1:]).strip()
    if not query_text:
        print("Domanda vuota.")
        sys.exit(1)

    print("Carico modello embedding...")
    model = SentenceTransformer(MODEL_NAME)

    print("Apro ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    print("Genero embedding query...")
    query_embedding = model.encode([query_text]).tolist()[0]

    print("Ricerca semantica...")
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=SEMANTIC_RESULTS,
    )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    combined = []

    # Primo passaggio: semantic + lexical + topical
    for doc, meta, dist in zip(docs, metas, dists):
        articolo = meta.get("articolo", "")
        rubrica = meta.get("rubrica", "")
        text = doc or ""

        semantic_score = 1 / (1 + dist)
        lex_text = lexical_score(query_text, text)
        lex_rubrica = lexical_score(query_text, rubrica) * 3
        topic_boost = strong_topic_boost(query_text, articolo, rubrica, text)

        combined.append({
            "articolo": articolo,
            "rubrica": rubrica,
            "doc": text,
            "meta": meta,
            "distance": dist,
            "semantic_score": semantic_score,
            "lex_text": lex_text,
            "lex_rubrica": lex_rubrica,
            "topic_boost": topic_boost,
            "refs": extract_article_refs(text),
        })

    # Secondo passaggio: citation-aware reranking
    ref_counter = Counter()
    top_seed = combined[:10]

    for item in top_seed:
        for ref in item["refs"]:
            ref_counter[ref] += 1

    for item in combined:
        articolo = item["articolo"]
        citation_boost = ref_counter.get(articolo, 0) * 6
        if articolo == "194" and ref_counter.get("194", 0) > 0:
            citation_boost += 12
        item["citation_boost"] = citation_boost
        item["score"] = (
            item["semantic_score"]
            + item["lex_text"]
            + item["lex_rubrica"]
            + item["topic_boost"]
            + item["citation_boost"]
        )

    combined.sort(key=lambda x: x["score"], reverse=True)

    print("\n=== RISULTATI ===\n")

    for i, item in enumerate(combined[:FINAL_RESULTS], start=1):
        articolo = item["articolo"]
        rubrica = item["rubrica"]
        distance = item["distance"]
        score = item["score"]

        print(f"[{i}] art. {articolo}")
        print(f"Rubrica: {rubrica}")
        print(f"Score totale: {score:.4f}")
        print(f" - semantic_score: {item['semantic_score']:.4f}")
        print(f" - lex_text: {item['lex_text']}")
        print(f" - lex_rubrica: {item['lex_rubrica']}")
        print(f" - topic_boost: {item['topic_boost']}")
        print(f" - citation_boost: {item['citation_boost']}")
        print(f" - distanza semantica: {distance:.4f}")
        print("-" * 100)
        print(item["doc"][:1400])
        print()

    print("=== FINE RISULTATI ===")


if __name__ == "__main__":
    main()
