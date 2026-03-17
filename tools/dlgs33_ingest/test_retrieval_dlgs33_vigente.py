from __future__ import annotations

import argparse
from datetime import datetime, UTC
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from dlgs33_ingest_utils import DEFAULT_MANIFEST_PATH, load_json, load_manifest_info, save_json


DEFAULT_QUERY_PACK = "query_pack_dlgs33_vigente.json"


def run_query(collection, query_text: str, top_k: int) -> list[dict]:
    result = collection.query(query_texts=[query_text], n_results=top_k)
    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    rows: list[dict] = []
    for idx, item_id in enumerate(ids):
        metadata = metadatas[idx] if idx < len(metadatas) else {}
        document = documents[idx] if idx < len(documents) else ""
        distance = distances[idx] if idx < len(distances) else None
        rows.append(
            {
                "rank": idx + 1,
                "id": item_id,
                "articolo": str(metadata.get("articolo", "")),
                "comma": str(metadata.get("comma", "")),
                "rubrica": str(metadata.get("rubrica", "")),
                "distance": distance,
                "document_preview": document[:400],
            }
        )
    return rows


def evaluate_case(rows: list[dict], expected_article: str, pass_top_k: int) -> bool:
    expected = expected_article.strip().lower()
    for row in rows[:pass_top_k]:
        if str(row.get("articolo", "")).strip().lower() == expected:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Test retrieval D.Lgs. 33/2013 vigente")
    parser.add_argument("--manifest-path", default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--persist-dir", default=None)
    parser.add_argument("--query-pack", default=DEFAULT_QUERY_PACK)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--pass-top-k", type=int, default=3)
    args = parser.parse_args()

    manifest, info = load_manifest_info(args.manifest_path)
    if manifest.get("status") != "READY":
        print("Manifest non pronto. Eseguire prima check_manifest_dlgs33_vigente.py")
        return 1

    persist_dir = Path(args.persist_dir) if args.persist_dir else info.persist_dir
    query_pack_path = Path(args.query_pack)
    if not query_pack_path.exists():
        query_pack_path = Path(__file__).resolve().parent / args.query_pack

    query_pack = load_json(query_pack_path)

    embedding_function = SentenceTransformerEmbeddingFunction(model_name=info.embedding_model)
    client = chromadb.PersistentClient(path=str(persist_dir))
    article_collection = client.get_collection(info.collection_articles, embedding_function=embedding_function)
    commi_collection = client.get_collection(info.collection_commi, embedding_function=embedding_function)

    print("=== TEST RETRIEVAL D.LGS. 33/2013 VIGENTE ===")
    print(f"Persist dir: {persist_dir}")
    print(f"Query pack: {query_pack_path}")

    results: list[dict] = []
    passed = 0

    for case in query_pack:
        collection = article_collection if case["target_collection"] == "articles" else commi_collection
        rows = run_query(collection, case["query"], args.top_k)
        is_pass = evaluate_case(rows, case["expected_article"], args.pass_top_k)
        if is_pass:
            passed += 1
        result_item = {
            "test_id": case["test_id"],
            "query": case["query"],
            "target_collection": case["target_collection"],
            "expected_article": case["expected_article"],
            "pass": is_pass,
            "results": rows,
        }
        results.append(result_item)
        print(f"[{case['test_id']}] expected art. {case['expected_article']} -> {'PASS' if is_pass else 'FAIL'}")
        if rows:
            top = rows[0]
            print(
                f"  top1: art. {top['articolo']} comma {top['comma']} | {top['rubrica'][:100]}"
            )

    report = {
        "report_id": "dlgs33_2013_vigente_retrieval_test_report_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "manifest_id": manifest.get("manifest_id"),
        "top_k": args.top_k,
        "pass_top_k": args.pass_top_k,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "status": "PASS" if passed == len(results) else "CHECK_REQUIRED",
        },
        "results": results,
    }

    log_path = Path("data/logs/dlgs33_2013_vigente_retrieval_test_report.json")
    save_json(log_path, report)
    print(f"Report: {log_path}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
