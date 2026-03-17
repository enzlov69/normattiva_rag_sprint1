#!/usr/bin/env python3
"""
Canonical broader accounting-branch validation baseline for the active
D.Lgs. 118/2011 + D.Lgs. 126/2014 collections.

Scope of this file:
- validates the active 118/126 accounting collections as a branch
- does not replace the separate surgical maintenance baseline for
  normattiva_dlgs118_2011_all_4_2 under tools/normattiva_dlgs118_all_4_2_restore/
- does not promote cantiere_118/ to active baseline; cantiere_118/ remains
  rebuild provenance unless explicitly reconsolidated
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import chromadb
from sentence_transformers import SentenceTransformer

QUERY_FILE = Path("data/test_queries/test_queries_dlgs118_rrs_micro.json")
CHROMA_PATH = "data/chroma"
OUTPUT_FILE = Path("data/test_results/dlgs118_retrieval_results.json")
TOP_K = 5

TARGET_COLLECTIONS = [
    "normattiva_dlgs118_2011_main",
    "normattiva_dlgs126_2014_main",
    "normattiva_dlgs126_2014_articles",
    "normattiva_dlgs118_2011_all_1",
    "normattiva_dlgs118_2011_all_4_1",
    "normattiva_dlgs118_2011_all_4_2",
]


def normalize_expected(value: str | None) -> str:
    if not value:
        return ""
    mapping = {
        "main": "normattiva_dlgs118_2011_main",
        "126_2014": "normattiva_dlgs126_2014_main",
        "all_1": "normattiva_dlgs118_2011_all_1",
        "all_4_1": "normattiva_dlgs118_2011_all_4_1",
        "all_4_2": "normattiva_dlgs118_2011_all_4_2",
    }
    return mapping.get(value.strip(), value.strip())


def evaluate_result(
    expected_primary: str,
    expected_secondary: str,
    results_by_collection: List[Dict[str, Any]],
) -> Dict[str, Any]:
    expected = [x for x in [expected_primary, expected_secondary] if x]

    ranked_hits: List[Dict[str, Any]] = []
    for row in results_by_collection:
        if not row["has_results"]:
            continue

        first_distance = None
        if row["results"]:
            first_distance = row["results"][0].get("distance")

        ranked_hits.append({
            "collection": row["collection"],
            "first_distance": first_distance,
        })

    # ordina per distanza crescente: più bassa = migliore
    ranked_hits.sort(
        key=lambda x: x["first_distance"] if x["first_distance"] is not None else 999999.0
    )

    found_collections = [r["collection"] for r in ranked_hits]

    first_correct_rank = None
    first_correct_collection = None

    for idx, coll in enumerate(found_collections, start=1):
        if coll in expected:
            first_correct_rank = idx
            first_correct_collection = coll
            break

    top3_collections = found_collections[:3]
    top3_ok = any(coll in expected for coll in top3_collections)

    if not expected:
        if ranked_hits:
            return {
                "status": "INFO",
                "first_correct_rank": None,
                "first_correct_collection": None,
                "top3_ok": None,
                "note": "Nessuna collection attesa definita per questa query.",
                "ranked_collections": found_collections,
            }
        return {
            "status": "KO",
            "first_correct_rank": None,
            "first_correct_collection": None,
            "top3_ok": False,
            "note": "Nessun risultato disponibile.",
            "ranked_collections": [],
        }

    if first_correct_rank == 1:
        status = "OK"
        note = "La collection attesa è al primo posto per distanza minima."
    elif top3_ok:
        status = "WARNING"
        note = "La collection attesa è presente entro le prime 3 collection per distanza minima."
    else:
        status = "KO"
        note = "La collection attesa non è presente entro le prime 3 collection per distanza minima."

    return {
        "status": status,
        "first_correct_rank": first_correct_rank,
        "first_correct_collection": first_correct_collection,
        "top3_ok": top3_ok,
        "note": note,
        "ranked_collections": found_collections,
    }

def main() -> int:
    if not QUERY_FILE.exists():
        print(f"File query NON trovato: {QUERY_FILE}")
        return 2

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with QUERY_FILE.open("r", encoding="utf-8") as f:
        queries = json.load(f)

    print("=== RETRIEVAL TEST DLGS 118 — TARGET ONLY ===")
    print("CHROMA_PATH:", CHROMA_PATH)

    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    existing_collections = {c.name for c in client.list_collections()}

    print("\n=== COLLECTIONS TARGET ===")
    missing = []
    for name in TARGET_COLLECTIONS:
        if name in existing_collections:
            print("-", name)
        else:
            print("-", name, "[MANCANTE]")
            missing.append(name)

    if missing:
        print("\nERRORE: mancano collection target necessarie al test.")
        return 3

    all_results: List[Dict[str, Any]] = []
    summary = {"OK": 0, "WARNING": 0, "KO": 0, "INFO": 0}

    for q in queries:
        test_id = q["test_id"]
        area = q.get("area", "")
        query_text = q["query"]
        expected_primary = normalize_expected(q.get("expected_primary"))
        expected_secondary = normalize_expected(q.get("expected_secondary"))

        print("\n==============================")
        print("TEST:", test_id)
        print("AREA:", area)
        print("QUERY:", query_text)
        print("EXPECTED_PRIMARY:", expected_primary or "-")
        print("EXPECTED_SECONDARY:", expected_secondary or "-")

        query_embedding = model.encode(query_text).tolist()

        results_by_collection: List[Dict[str, Any]] = []

        for collection_name in TARGET_COLLECTIONS:
            collection = client.get_collection(collection_name)

            result = collection.query(
                query_embeddings=[query_embedding],
                n_results=TOP_K,
                include=["documents", "metadatas", "distances"],
            )

            docs = (result.get("documents") or [[]])[0]
            metas = (result.get("metadatas") or [[]])[0]
            distances = (result.get("distances") or [[]])[0]

            collection_row: Dict[str, Any] = {
                "collection": collection_name,
                "has_results": bool(docs),
                "results": [],
            }

            if docs:
                print("\nCOLLECTION:", collection_name)
                for i, doc in enumerate(docs, start=1):
                    meta = metas[i - 1] if i - 1 < len(metas) else {}
                    dist = distances[i - 1] if i - 1 < len(distances) else None
                    snippet = (doc or "").replace("\n", " ").strip()[:140]

                    print(f"{i}. distanza={dist} | {snippet}")

                    collection_row["results"].append({
                        "rank_in_collection": i,
                        "distance": dist,
                        "snippet": snippet,
                        "citation_text": (meta or {}).get("citation_text", ""),
                        "articolo": (meta or {}).get("articolo", ""),
                        "comma": (meta or {}).get("comma", ""),
                        "rubrica": (meta or {}).get("rubrica", ""),
                    })

            results_by_collection.append(collection_row)

        evaluation = evaluate_result(
            expected_primary=expected_primary,
            expected_secondary=expected_secondary,
            results_by_collection=results_by_collection,
        )

        status = evaluation["status"]
        summary[status] += 1

        print("\nESITO:", status)
        print("NOTE:", evaluation["note"])
        print("FIRST_CORRECT_RANK:", evaluation["first_correct_rank"])
        print("FIRST_CORRECT_COLLECTION:", evaluation["first_correct_collection"])

        all_results.append({
            "test_id": test_id,
            "area": area,
            "query": query_text,
            "expected_primary": expected_primary,
            "expected_secondary": expected_secondary,
            "evaluation": evaluation,
            "results_by_collection": results_by_collection,
        })

    output_payload = {
        "status": "OK",
        "chroma_path": CHROMA_PATH,
        "target_collections": TARGET_COLLECTIONS,
        "summary": summary,
        "tests": all_results,
    }

    OUTPUT_FILE.write_text(
        json.dumps(output_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n==============================")
    print("=== SUMMARY ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nRisultati salvati in: {OUTPUT_FILE}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
