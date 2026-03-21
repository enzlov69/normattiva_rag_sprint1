from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from tools.federated_tests import run_federated_active_corpora_tests as harness


ROOT = Path(__file__).resolve().parents[1]
QUERY_PACK_PATH = ROOT / "data" / "query_packs" / "federated_active_corpora_query_pack_v1.json"

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def load_default_runtime_config() -> dict[str, Any]:
    pack = harness.load_json(QUERY_PACK_PATH)
    return {
        "persist_dir": pack["chroma_path"],
        "embedding_model": pack["embedding_model"],
        "top_k_per_collection": int(pack["top_k_per_collection"]),
        "global_eval_top_k": int(pack["global_eval_top_k"]),
        "collections": list(pack["active_collections"]),
    }


def resolve_local_embedding_model(model_name: str) -> str:
    hub_root = Path.home() / ".cache" / "huggingface" / "hub"
    model_dir = hub_root / f"models--{model_name.replace('/', '--')}"
    ref_main = model_dir / "refs" / "main"
    if ref_main.exists():
        snapshot_id = ref_main.read_text(encoding="utf-8").strip()
        snapshot_dir = model_dir / "snapshots" / snapshot_id
        if snapshot_dir.exists():
            return str(snapshot_dir)
    return model_name


def is_access_denied_error(message: str) -> bool:
    lowered = (message or "").lower()
    return "winerror 5" in lowered or "accesso negato" in lowered


def is_worker_spawn_instability_error(message: str) -> bool:
    lowered = (message or "").lower()
    markers = (
        "winerror 5",
        "accesso negato",
        "access denied",
        "startup worker",
        "worker non avviato",
        "spawn",
    )
    return any(marker in lowered for marker in markers)


def is_chroma_reader_error(message: str) -> bool:
    lowered = (message or "").lower()
    markers = (
        "error creating hnsw segment reader",
        "nothing found on disk",
        "segment reader",
        "collection reader",
        "opening reader",
        "hnsw",
        "chroma",
    )
    return any(marker in lowered for marker in markers)


def _build_runtime_failure(
    *,
    collection_name: str,
    attempt: int,
    error: str,
    stage: str,
    recovered: bool = False,
) -> dict[str, Any]:
    return {
        "query_id": "runtime_single_query",
        "collection": collection_name,
        "attempt": attempt,
        "stage": stage,
        "error": error,
        "recovered": recovered,
    }


def _query_collection_with_clean_reopen(
    *,
    persist_path: Path,
    collection_name: str,
    embedding: list[float],
    top_k_per_collection: int,
) -> list[dict[str, Any]]:
    fresh_client = chromadb.PersistentClient(path=str(persist_path))
    collection = harness.get_collection(fresh_client, collection_name)
    return harness.query_collection_once(
        collection=collection,
        collection_name=collection_name,
        embedding=embedding,
        top_k_per_collection=top_k_per_collection,
    )


def _query_collection_sequential(
    *,
    persist_path: Path,
    collection_name: str,
    embedding: list[float],
    top_k_per_collection: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    errors: list[dict[str, Any]] = []

    try:
        client = chromadb.PersistentClient(path=str(persist_path))
        collection = harness.get_collection(client, collection_name)
        hits = harness.query_collection_once(
            collection=collection,
            collection_name=collection_name,
            embedding=embedding,
            top_k_per_collection=top_k_per_collection,
        )
        return hits, errors, False
    except Exception as exc:
        errors.append(
            _build_runtime_failure(
                collection_name=collection_name,
                attempt=1,
                error=str(exc),
                stage="sequential_query",
            )
        )
        if not is_chroma_reader_error(str(exc)):
            return [], errors, True

    try:
        hits = _query_collection_with_clean_reopen(
            persist_path=persist_path,
            collection_name=collection_name,
            embedding=embedding,
            top_k_per_collection=top_k_per_collection,
        )
        errors.append(
            _build_runtime_failure(
                collection_name=collection_name,
                attempt=2,
                error="Recovered with clean client reopen after reader failure.",
                stage="sequential_query_clean_reopen",
                recovered=True,
            )
        )
        return hits, errors, False
    except Exception as retry_exc:
        errors.append(
            _build_runtime_failure(
                collection_name=collection_name,
                attempt=2,
                error=str(retry_exc),
                stage="sequential_query_clean_reopen",
            )
        )
        return [], errors, True


def _load_collection_count_with_retry(
    *,
    persist_path: Path,
    smoke_client: chromadb.PersistentClient,
    collection_name: str,
) -> tuple[int | None, dict[str, Any] | None]:
    try:
        collection = harness.get_collection(smoke_client, collection_name)
        return collection.count(), None
    except Exception as exc:
        message = str(exc)
        if not is_chroma_reader_error(message):
            raise

        try:
            fresh_client = chromadb.PersistentClient(path=str(persist_path))
            collection = harness.get_collection(fresh_client, collection_name)
            return collection.count(), None
        except Exception as retry_exc:
            return None, _build_runtime_failure(
                collection_name=collection_name,
                attempt=1,
                error=str(retry_exc),
                stage="collection_open_retry",
            )


def run_federated_query(
    query_text: str,
    persist_dir: str | Path,
    collections: list[str],
    top_k_per_collection: int,
    global_eval_top_k: int,
) -> dict[str, Any]:
    config = load_default_runtime_config()
    persist_path = Path(persist_dir)
    if not persist_path.is_absolute():
        persist_path = (ROOT / persist_path).resolve()

    if not persist_path.exists():
        raise FileNotFoundError(f"Persist dir non trovato: {persist_path}")
    if not collections:
        raise ValueError("Almeno una collection deve essere specificata")

    smoke_client = chromadb.PersistentClient(path=str(persist_path))
    existing = {c.name for c in smoke_client.list_collections()}
    missing_collections = [name for name in collections if name not in existing]
    if missing_collections:
        raise RuntimeError(f"Collection attive mancanti in Chroma: {missing_collections}")

    collection_counts: dict[str, int | None] = {}
    runtime_failures: list[dict[str, Any]] = []
    degraded_collections: list[str] = []
    queryable_collections: list[str] = []
    for name in collections:
        count, failure = _load_collection_count_with_retry(
            persist_path=persist_path,
            smoke_client=smoke_client,
            collection_name=name,
        )
        collection_counts[name] = count
        if failure is not None:
            runtime_failures.append(failure)
            degraded_collections.append(name)
            continue
        queryable_collections.append(name)

    ctx = mp.get_context("spawn")
    workers: dict[str, harness.CollectionWorker] = {
        name: harness.CollectionWorker(ctx=ctx, chroma_path=persist_path, collection_name=name)
        for name in queryable_collections
    }

    model_source = resolve_local_embedding_model(config["embedding_model"])
    model = SentenceTransformer(model_source, local_files_only=True)
    embedding = model.encode(query_text).tolist()

    pooled_hits: list[dict[str, Any]] = []
    fallback_collections: list[str] = []
    execution_mode = "worker_pool"
    sequential_fallback_reason: str | None = None

    try:
        for collection_name in queryable_collections:
            if execution_mode == "worker_pool":
                hits, errors = harness.query_collection_with_retry(
                    workers=workers,
                    collection_name=collection_name,
                    embedding=embedding,
                    top_k_per_collection=top_k_per_collection,
                    query_id="runtime_single_query",
                    retries=harness.QUERY_RETRIES,
                    retry_sleep_seconds=harness.RETRY_SLEEP_SECONDS,
                )
            else:
                hits, errors, failed = _query_collection_sequential(
                    persist_path=persist_path,
                    collection_name=collection_name,
                    embedding=embedding,
                    top_k_per_collection=top_k_per_collection,
                )
                if failed:
                    degraded_collections.append(collection_name)
                pooled_hits.extend(hits)
                runtime_failures.extend(errors)
                continue

            if (
                execution_mode == "worker_pool"
                and not hits
                and errors
                and all(is_worker_spawn_instability_error(err.get("error", "")) for err in errors)
            ):
                execution_mode = "sequential_fallback"
                sequential_fallback_reason = errors[-1].get("error", "worker_pool_unstable")
                for worker in workers.values():
                    worker.stop(silent=True)
                hits, seq_errors, failed = _query_collection_sequential(
                    persist_path=persist_path,
                    collection_name=collection_name,
                    embedding=embedding,
                    top_k_per_collection=top_k_per_collection,
                )
                errors.extend(seq_errors)
                if failed:
                    degraded_collections.append(collection_name)
                else:
                    fallback_collections.append(collection_name)
            elif not hits and errors and all(is_access_denied_error(err.get("error", "")) for err in errors):
                try:
                    collection = harness.get_collection(smoke_client, collection_name)
                    hits = harness.query_collection_once(
                        collection=collection,
                        collection_name=collection_name,
                        embedding=embedding,
                        top_k_per_collection=top_k_per_collection,
                    )
                    fallback_collections.append(collection_name)
                    errors = []
                except Exception as fallback_exc:
                    errors.append(
                        _build_runtime_failure(
                            collection_name=collection_name,
                            attempt=len(errors) + 1,
                            error=str(fallback_exc),
                            stage="collection_query_sync_fallback",
                        )
                    )
                    degraded_collections.append(collection_name)
                    hits = []
            elif not hits and errors and any(is_chroma_reader_error(err.get("error", "")) for err in errors):
                try:
                    hits = _query_collection_with_clean_reopen(
                        persist_path=persist_path,
                        collection_name=collection_name,
                        embedding=embedding,
                        top_k_per_collection=top_k_per_collection,
                    )
                    fallback_collections.append(collection_name)
                    errors.append(
                        _build_runtime_failure(
                            collection_name=collection_name,
                            attempt=len(errors) + 1,
                            error="Recovered with clean client reopen after reader failure.",
                            stage="collection_query_clean_reopen",
                            recovered=True,
                        )
                    )
                except Exception as retry_exc:
                    errors.append(
                        _build_runtime_failure(
                            collection_name=collection_name,
                            attempt=len(errors) + 1,
                            error=str(retry_exc),
                            stage="collection_query_clean_reopen",
                        )
                    )
                    degraded_collections.append(collection_name)
            pooled_hits.extend(hits)
            runtime_failures.extend(errors)
    finally:
        for worker in workers.values():
            worker.stop(silent=True)

    pooled_hits.sort(
        key=lambda x: x["distance"] if isinstance(x.get("distance"), (int, float)) else 999999.0
    )

    return {
        "query_text": query_text,
        "persist_dir": str(persist_path),
        "embedding_model": config["embedding_model"],
        "embedding_model_source": model_source,
        "collections": list(collections),
        "top_k_per_collection": int(top_k_per_collection),
        "global_eval_top_k": int(global_eval_top_k),
        "collection_counts": collection_counts,
        "fallback_collections": fallback_collections,
        "degraded_collections": list(dict.fromkeys(degraded_collections)),
        "execution_mode": execution_mode,
        "sequential_fallback_reason": sequential_fallback_reason,
        "runtime_failures": runtime_failures,
        "hits_total": len(pooled_hits),
        "results": pooled_hits[:global_eval_top_k],
    }


def build_parser() -> argparse.ArgumentParser:
    defaults = load_default_runtime_config()
    parser = argparse.ArgumentParser(description="Runtime riusabile per query federata globale singola")
    parser.add_argument("--query-text", required=True)
    parser.add_argument("--persist-dir", default=defaults["persist_dir"])
    parser.add_argument("--collection", action="append", dest="collections")
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--top-k-per-collection", type=int, default=defaults["top_k_per_collection"])
    parser.add_argument("--global-eval-top-k", type=int, default=defaults["global_eval_top_k"])
    return parser


def main() -> None:
    args = build_parser().parse_args()
    defaults = load_default_runtime_config()
    collections = args.collections or defaults["collections"]

    payload = run_federated_query(
        query_text=args.query_text,
        persist_dir=args.persist_dir,
        collections=collections,
        top_k_per_collection=args.top_k_per_collection,
        global_eval_top_k=args.global_eval_top_k,
    )

    print("=== FEDERATED GLOBAL RUNTIME ===")
    print(f"QUERY_TEXT          : {payload['query_text']}")
    print(f"PERSIST_DIR         : {payload['persist_dir']}")
    print(f"TOP_K_PER_COLL      : {payload['top_k_per_collection']}")
    print(f"GLOBAL_EVAL_TOP_K   : {payload['global_eval_top_k']}")
    print(f"RUNTIME_FAILURES    : {len(payload['runtime_failures'])}")
    print()
    print("[GLOBAL TOP RESULTS]")
    for idx, hit in enumerate(payload["results"], start=1):
        harness.print_hit(idx, hit)

    if args.output_json:
        output_path = Path(args.output_json)
        if not output_path.is_absolute():
            output_path = (ROOT / output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print()
        print(f"[INFO] output json    : {output_path}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
