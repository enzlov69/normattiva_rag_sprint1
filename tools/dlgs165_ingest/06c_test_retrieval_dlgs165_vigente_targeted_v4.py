from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parents[2]

CHROMA_PATH = ROOT / "data" / "chroma"
QUERY_PACK_PATH = ROOT / "data" / "query_packs" / "dlgs165_2001_vigente_query_pack_v4.json"
EXPECTATIONS_PATH = ROOT / "tools" / "dlgs165_ingest" / "06b_eval_dlgs165_retrieval_expectations_v3.json"

COLLECTIONS = [
    "normattiva_dlgs165_2001_vigente_articles",
    "normattiva_dlgs165_2001_vigente_commi",
]

EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K_PER_COLLECTION = 3
TOP_K_GLOBAL = 3


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"File non trovato: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def get_collection(client: chromadb.PersistentClient, name: str):
    try:
        return client.get_collection(name=name)
    except Exception as e:
        raise RuntimeError(f"Collection non trovata in Chroma: {name}") from e


def safe_list_get(values, idx, default=None):
    if isinstance(values, list) and idx < len(values):
        return values[idx]
    return default


def flatten_results(collection_name: str, results: dict[str, Any]) -> list[dict[str, Any]]:
    ids = safe_list_get(results.get("ids", []), 0, []) or []
    distances = safe_list_get(results.get("distances", []), 0, []) or []
    metadatas = safe_list_get(results.get("metadatas", []), 0, []) or []
    documents = safe_list_get(results.get("documents", []), 0, []) or []

    flat = []
    for i, rid in enumerate(ids):
        metadata = metadatas[i] if i < len(metadatas) and metadatas[i] else {}
        document = documents[i] if i < len(documents) and documents[i] else ""
        distance = distances[i] if i < len(distances) else None

        flat.append(
            {
                "collection": collection_name,
                "rank_in_collection": i + 1,
                "record_id": rid,
                "distance": distance,
                "metadata": metadata,
                "document": document,
            }
        )
    return flat


def preview_document(text: str, max_len: int = 220) -> str:
    if not text:
        return ""
    text = " ".join(text.split())
    return text[:max_len] + ("..." if len(text) > max_len else "")


def print_hit(rank: int, hit: dict[str, Any]) -> None:
    md = hit.get("metadata") or {}
    articolo = md.get("articolo", "")
    comma = md.get("comma", "")
    rubrica = md.get("rubrica", "")
    unit_type = md.get("unit_type", "")
    distance = hit.get("distance")
    distance_txt = f"{distance:.6f}" if isinstance(distance, (int, float)) else "n/a"

    print(f"  [{rank}] {hit['collection']}")
    print(f"      record_id : {hit['record_id']}")
    print(f"      distance  : {distance_txt}")
    print(f"      unit_type : {unit_type}")
    print(f"      articolo  : {articolo}")
    print(f"      comma     : {comma}")
    print(f"      rubrica   : {rubrica}")
    print(f"      testo     : {preview_document(hit.get('document', ''))}")


def normalize_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def criterion_match(hit: dict[str, Any], criterion: dict[str, Any]) -> bool:
    md = hit.get("metadata") or {}

    checks = {
        "record_id": normalize_str(hit.get("record_id")),
        "collection": normalize_str(hit.get("collection")),
        "unit_type": normalize_str(md.get("unit_type")),
        "articolo": normalize_str(md.get("articolo")),
        "comma": normalize_str(md.get("comma")),
        "rubrica": normalize_str(md.get("rubrica")),
    }

    for key, expected in criterion.items():
        if key == "rubrica_contains":
            if normalize_str(expected).lower() not in checks["rubrica"].lower():
                return False
            continue

        if key not in checks:
            return False

        if checks[key] != normalize_str(expected):
            return False

    return True


def evaluate_query(global_hits: list[dict[str, Any]], expectation: dict[str, Any]) -> tuple[bool, str]:
    if expectation.get("skip_evaluation", False):
        return True, "SKIPPED"

    expected_any = expectation.get("expected_global_any_of", [])
    if not expected_any:
        return False, "NO_EXPECTATIONS_DEFINED"

    top_hits = global_hits[:TOP_K_GLOBAL]

    for criterion in expected_any:
        for hit in top_hits:
            if criterion_match(hit, criterion):
                articolo = (hit.get("metadata") or {}).get("articolo", "")
                comma = (hit.get("metadata") or {}).get("comma", "")
                return True, f"MATCH articolo={articolo} comma={comma}"

    return False, "NO_EXPECTED_TARGET_IN_GLOBAL_TOP3"


def main() -> None:
    print("=== VALIDAZIONE MIRATA RETRIEVAL D.LGS. 165/2001 V4 ===")
    print(f"CHROMA_PATH      : {CHROMA_PATH}")
    print(f"QUERY_PACK_PATH  : {QUERY_PACK_PATH}")
    print(f"EXPECTATIONS     : {EXPECTATIONS_PATH}")
    print(f"COLLECTIONS      : {COLLECTIONS}")
    print(f"MODEL            : {EMBED_MODEL_NAME}")
    print()

    if not CHROMA_PATH.exists():
        raise FileNotFoundError(f"Persist dir non trovato: {CHROMA_PATH}")

    query_pack = load_json(QUERY_PACK_PATH)
    expectations_payload = load_json(EXPECTATIONS_PATH)

    queries = query_pack.get("queries", [])
    expectations_list = expectations_payload.get("expectations", [])
    expectations = {item["query_id"]: item for item in expectations_list}

    active_queries = [q for q in queries if q.get("active", True)]

    if not active_queries:
        raise SystemExit("[ERRORE] Nessuna query attiva nel query pack v4")

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    model = SentenceTransformer(EMBED_MODEL_NAME)

    collections = {name: get_collection(client, name=name) for name in COLLECTIONS}

    summary = {
        "queries_total": len(queries),
        "queries_active": len(active_queries),
        "passed": [],
        "failed": [],
        "skipped": [],
    }

    for q in queries:
        query_id = q["query_id"]
        active = q.get("active", True)

        if not active:
            print("=" * 110)
            print(f"QUERY_ID : {query_id}")
            print("[SKIP] query inattiva nel query pack")
            print()
            summary["skipped"].append(query_id)
            continue

        area = q["area"]
        query_text = q["query_text"]

        embedding = model.encode(query_text).tolist()

        print("=" * 110)
        print(f"QUERY_ID : {query_id}")
        print(f"AREA     : {area}")
        print(f"QUERY    : {query_text}")
        print("-" * 110)

        global_hits: list[dict[str, Any]] = []

        for collection_name, collection in collections.items():
            results = collection.query(
                query_embeddings=[embedding],
                n_results=TOP_K_PER_COLLECTION,
                include=["documents", "metadatas", "distances"],
            )
            hits = flatten_results(collection_name, results)
            global_hits.extend(hits)

        global_hits.sort(
            key=lambda x: x["distance"] if isinstance(x.get("distance"), (int, float)) else 999999.0
        )

        print("[GLOBAL TOP3]")
        for idx, hit in enumerate(global_hits[:TOP_K_GLOBAL], start=1):
            print_hit(idx, hit)
        print()

        expectation = expectations.get(query_id, {})
        passed, reason = evaluate_query(global_hits, expectation)

        if reason == "SKIPPED":
            print("[VERDETTO] SKIP")
            print()
            summary["skipped"].append(query_id)
            continue

        if passed:
            print(f"[VERDETTO] PASS -> {reason}")
            print()
            summary["passed"].append({"query_id": query_id, "reason": reason})
        else:
            print(f"[VERDETTO] FAIL -> {reason}")
            print()
            summary["failed"].append({"query_id": query_id, "reason": reason})

    print("=" * 110)
    print("=== RIEPILOGO VALIDAZIONE V4 ===")
    print(f"Queries attive : {len(active_queries)}")
    print(f"PASS           : {len(summary['passed'])}")
    print(f"FAIL           : {len(summary['failed'])}")
    print(f"SKIP           : {len(summary['skipped'])}")

    if summary["failed"]:
        print()
        print("[QUERY FAIL]")
        for item in summary["failed"]:
            print(f" - {item['query_id']}: {item['reason']}")

    summary_path = ROOT / "data" / "logs" / "dlgs165_2001_vigente_targeted_validation_summary_v4.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print(f"[INFO] summary log: {summary_path}")

    if summary["failed"]:
        raise SystemExit("[ESITO] VALIDAZIONE V4 NON CONSOLIDATA: presenti query FAIL")

    print("[ESITO] VALIDAZIONE V4 CONSOLIDATA: nessuna query FAIL")


if __name__ == "__main__":
    main()