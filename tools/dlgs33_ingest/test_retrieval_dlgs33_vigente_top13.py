from __future__ import annotations

import argparse
from datetime import datetime, UTC
from pathlib import Path
import json
import sys

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# Assicura l'import del package src anche eseguendo lo script da tools/dlgs33_ingest
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.reranker_dlgs33_patch import RetrievalCandidate, RerankerDLGS33Patch
from dlgs33_ingest_utils import DEFAULT_MANIFEST_PATH, load_json, load_manifest_info, save_json


DEFAULT_QUERY_PACK = "query_pack_dlgs33_vigente_top13.json"


def normalize_article(value: str) -> str:
    return str(value or "").strip().lower()


def expand_query_for_retrieval(query_text: str) -> str:
    """
    Espansione lessicale minima per aiutare il candidate retrieval
    nei casi in cui la rubrica normativa non emerga nei primi risultati.
    """
    q = str(query_text or "").strip().lower()

    expansions = {
        "amministrazione trasparente": "amministrazione trasparente sezione amministrazione trasparente",
        "responsabile per la trasparenza": "responsabile per la trasparenza",
    }

    return expansions.get(q, query_text)


def distance_to_score(distance) -> float:
    """
    Chroma restituisce distance: più è bassa, migliore è il match.
    La trasformiamo in score monotono decrescente, sufficiente per il reranker.
    """
    if distance is None:
        return 0.0
    try:
        return -float(distance)
    except (TypeError, ValueError):
        return 0.0


def run_query(collection, query_text: str, fetch_k: int, source_collection_name: str) -> list[dict]:
    result = collection.query(query_texts=[query_text], n_results=fetch_k)
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
                "document_full": document,
                "document_preview": document[:300],
                "atto_tipo": str(metadata.get("atto_tipo", "Decreto legislativo")),
                "atto_numero": str(metadata.get("atto_numero", "33")),
                "atto_anno": str(metadata.get("atto_anno", "2013")),
                "source_collection": source_collection_name,
                "score_vector": distance_to_score(distance),
                "score_lexical": 0.0,
                "metadata": metadata,
            }
        )
    return rows


def rerank_rows(query_text: str, rows: list[dict]) -> list[dict]:
    if not rows:
        return rows

    patcher = RerankerDLGS33Patch()

    candidates: list[RetrievalCandidate] = []
    for row in rows:
        candidates.append(
            RetrievalCandidate(
                retrieval_result_id=row.get("id", ""),
                atto_tipo=row.get("atto_tipo", "Decreto legislativo"),
                atto_numero=row.get("atto_numero", "33"),
                atto_anno=row.get("atto_anno", "2013"),
                articolo=row.get("articolo", ""),
                comma=row.get("comma", ""),
                rubrica=row.get("rubrica", ""),
                testo_unita=row.get("document_full", ""),
                source_collection=row.get("source_collection", ""),
                score_lexical=float(row.get("score_lexical", 0.0) or 0.0),
                score_vector=float(row.get("score_vector", 0.0) or 0.0),
                metadata=row.get("metadata", {}) or {},
            )
        )

    reranked_candidates = patcher.rerank(query_text, candidates)

    row_by_id = {str(row.get("id", "")): row for row in rows}
    reranked_rows: list[dict] = []

    for idx, cand in enumerate(reranked_candidates, start=1):
        base_row = dict(row_by_id.get(cand.retrieval_result_id, {}))
        base_row["rank"] = idx
        base_row["score_reranked"] = cand.score_reranked
        base_row["retrieval_reason"] = cand.retrieval_reason
        reranked_rows.append(base_row)

    return reranked_rows


def position_of_expected(rows: list[dict], expected_article: str) -> int | None:
    expected = normalize_article(expected_article)
    for row in rows:
        if normalize_article(row.get("articolo", "")) == expected:
            return int(row["rank"])
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Test retrieval D.Lgs. 33/2013 vigente con soglie TOP1/TOP3")
    parser.add_argument("--manifest-path", default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--persist-dir", default=None)
    parser.add_argument("--query-pack", default=DEFAULT_QUERY_PACK)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--fetch-k", type=int, default=20)
    parser.add_argument("--top3-threshold", type=int, default=3)
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

    print("=== TEST RETRIEVAL D.LGS. 33/2013 VIGENTE — TOP1/TOP3 ===")
    print(f"Persist dir: {persist_dir}")
    print(f"Query pack: {query_pack_path}")
    print(f"Top-k finale: {args.top_k}")
    print(f"Fetch-k retrieval: {args.fetch_k}")

    results: list[dict] = []
    top1_passed = 0
    top3_passed = 0
    weak_cases = []
    fail_cases = []

    for case in query_pack:
        if case["target_collection"] == "articles":
            collection = article_collection
            source_collection_name = info.collection_articles
        else:
            collection = commi_collection
            source_collection_name = info.collection_commi

        retrieval_query = expand_query_for_retrieval(case["query"])
        raw_rows = run_query(collection, retrieval_query, args.fetch_k, source_collection_name)
        rows = rerank_rows(case["query"], raw_rows)[: args.top_k]

        expected_article = case["expected_article"]
        pos = position_of_expected(rows, expected_article)

        is_top1 = pos == 1
        is_top3 = pos is not None and pos <= args.top3_threshold

        if is_top1:
            top1_passed += 1
        if is_top3:
            top3_passed += 1

        if is_top3 and not is_top1:
            weak_cases.append(case["test_id"])
        if not is_top3:
            fail_cases.append(case["test_id"])

        result_item = {
            "test_id": case["test_id"],
            "query": case["query"],
            "retrieval_query": retrieval_query,
            "target_collection": case["target_collection"],
            "expected_article": expected_article,
            "expected_position": {
                "must_be_top1": bool(case.get("must_be_top1", True)),
                "must_be_top3": bool(case.get("must_be_top3", True)),
            },
            "actual_position": {
                "found_rank": pos,
                "is_top1": is_top1,
                "is_top3": is_top3,
            },
            "top_results": rows,
            "note": case.get("note", ""),
        }
        results.append(result_item)

        label = "PASS_STRONG" if is_top1 else ("PASS_SOFT" if is_top3 else "FAIL")
        print(f"[{case['test_id']}] expected art. {expected_article} -> {label}")
        if retrieval_query != case["query"]:
            print(f"  retrieval query: {retrieval_query}")
        if rows:
            top = rows[0]
            print(f"  top1: art. {top['articolo']} comma {top['comma']} | {top['rubrica'][:100]}")
            print(f"  expected rank: {pos}")
            if "score_reranked" in top:
                print(f"  reranked score: {top['score_reranked']:.4f}")

    total = len(results)
    if top1_passed == total:
        final_status = "PASS_STRONG"
    elif top3_passed == total:
        final_status = "PASS_SOFT"
    else:
        final_status = "FAIL"

    report = {
        "report_id": "dlgs33_2013_vigente_retrieval_top13_report_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "manifest_id": manifest.get("manifest_id"),
        "summary": {
            "total": total,
            "top1_passed": top1_passed,
            "top1_failed": total - top1_passed,
            "top3_passed": top3_passed,
            "top3_failed": total - top3_passed,
            "weak_cases_top3_not_top1": weak_cases,
            "fail_cases_outside_top3": fail_cases,
            "final_status": final_status,
            "top_k": args.top_k,
            "fetch_k": args.fetch_k,
        },
        "results": results,
    }

    log_path = Path("data/logs/dlgs33_2013_vigente_retrieval_top13_report.json")
    save_json(log_path, report)

    print("\n=== SUMMARY ===")
    print(f"Top1 passed: {top1_passed}/{total}")
    print(f"Top3 passed: {top3_passed}/{total}")
    print(f"Weak cases: {weak_cases}")
    print(f"Fail cases: {fail_cases}")
    print(f"Final status: {final_status}")
    print(f"Report: {log_path}")

    return 0 if final_status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())