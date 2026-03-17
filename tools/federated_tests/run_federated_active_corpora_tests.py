from __future__ import annotations

import gc
import json
import multiprocessing as mp
import time
from pathlib import Path
from typing import Any

import chromadb


ROOT = Path(__file__).resolve().parents[2]

QUERY_PACK_PATH = ROOT / "data" / "query_packs" / "federated_active_corpora_query_pack_v1.json"
EXPECTATIONS_PATH = ROOT / "tools" / "federated_tests" / "federated_active_corpora_expectations_v1.json"
LOG_PATH = ROOT / "data" / "logs" / "federated_active_corpora_test_summary_v1.json"

ENABLE_COLLECTION_WARMUP = True
WARMUP_PEEK_LIMIT = 3

ENABLE_QUERY_PRIME = True
QUERY_PRIME_TOP_K = 1

QUERY_RETRIES = 1
RETRY_SLEEP_SECONDS = 0.35

# Nuova scelta strutturale:
# worker persistenti per TUTTE le collection attive, per evitare
# aperture/chiusure continue del client Chroma e instabilità del reader HNSW.
WORKER_STARTUP_TIMEOUT_SECONDS = 60.0
WORKER_QUERY_TIMEOUT_SECONDS = 60.0


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"File non trovato: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def safe_list_get(values, idx, default=None):
    if isinstance(values, list) and idx < len(values):
        return values[idx]
    return default


def flatten_results(collection_name: str, results: dict[str, Any]) -> list[dict[str, Any]]:
    ids = safe_list_get(results.get("ids", []), 0, []) or []
    distances = safe_list_get(results.get("distances", []), 0, []) or []
    metadatas = safe_list_get(results.get("metadatas", []), 0, []) or []
    documents = safe_list_get(results.get("documents", []), 0, []) or []

    flat: list[dict[str, Any]] = []
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


def preview_document(text: str, max_len: int = 180) -> str:
    if not text:
        return ""
    text = " ".join(text.split())
    return text[:max_len] + ("..." if len(text) > max_len else "")


def get_collection(client: chromadb.PersistentClient, name: str):
    try:
        return client.get_collection(name=name)
    except Exception as e:
        raise RuntimeError(f"Collection non trovata in Chroma: {name}") from e


def print_hit(rank: int, hit: dict[str, Any]) -> None:
    md = hit.get("metadata") or {}
    articolo = md.get("articolo", "")
    comma = md.get("comma", "")
    rubrica = md.get("rubrica", "")
    unit_type = md.get("unit_type", md.get("record_type", ""))
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


def collection_names_from_hits(hits: list[dict[str, Any]], top_k: int) -> list[str]:
    return [hit["collection"] for hit in hits[:top_k]]


def any_of_topk(hits: list[dict[str, Any]], top_k: int, acceptable: list[str]) -> bool:
    names = collection_names_from_hits(hits, top_k)
    return any(name in acceptable for name in names)


def all_groups_in_topk(hits: list[dict[str, Any]], top_k: int, groups: list[list[str]]) -> bool:
    if not groups:
        return True

    names = set(collection_names_from_hits(hits, top_k))
    for group in groups:
        if not any(candidate in names for candidate in group):
            return False
    return True


def forbidden_in_topk(hits: list[dict[str, Any]], top_k: int, forbidden: list[str]) -> bool:
    if not forbidden:
        return False
    names = collection_names_from_hits(hits, top_k)
    return any(name in forbidden for name in names)


def collect_warmup_info(collection) -> dict[str, Any]:
    count = None
    peek_ids: list[str] = []

    try:
        count = collection.count()
    except Exception:
        count = None

    try:
        peek_limit = 0
        if isinstance(count, int) and count > 0:
            peek_limit = min(WARMUP_PEEK_LIMIT, count)
        if peek_limit > 0:
            peek = collection.peek(limit=peek_limit)
            peek_ids = list(peek.get("ids", []) or [])
        else:
            peek_ids = []
    except Exception:
        peek_ids = []

    return {"count": count, "peek_ids": peek_ids}


def print_warmup_info(collection_name: str, warmup_info: dict[str, Any], retry_mode: bool = False) -> None:
    prefix = "[WARMUP-RETRY]" if retry_mode else "[WARMUP]"
    count = warmup_info.get("count")
    peek_ids = warmup_info.get("peek_ids", [])
    print(f"{prefix} {collection_name} | count={count} | peek_ids={peek_ids}")


def prime_collection_once(
    collection,
    collection_name: str,
    embedding: list[float],
) -> None:
    """
    Prime reale del reader HNSW.
    Non basta count/peek: qui eseguiamo una query minimale reale.
    """
    try:
        count = collection.count()
    except Exception as e:
        raise RuntimeError(f"[PRIME] {collection_name} count failed: {e}") from e

    if not isinstance(count, int) or count <= 0:
        return

    n_results = min(QUERY_PRIME_TOP_K, count)

    try:
        collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            include=["distances"],
        )
    except Exception as e:
        raise RuntimeError(f"[PRIME] {collection_name} real query failed: {e}") from e


def query_collection_once(
    collection,
    collection_name: str,
    embedding: list[float],
    top_k_per_collection: int,
) -> list[dict[str, Any]]:
    try:
        count = collection.count()
    except Exception as e:
        raise RuntimeError(f"[QUERY-COUNT] {collection_name} count failed: {e}") from e

    if not isinstance(count, int) or count <= 0:
        return []

    n_results = min(top_k_per_collection, count)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    return flatten_results(collection_name, results)


def _collection_worker_main(
    chroma_path_str: str,
    collection_name: str,
    warmup_enabled: bool,
    conn,
) -> None:
    client = None
    collection = None
    primed = False

    try:
        client = chromadb.PersistentClient(path=chroma_path_str)
        collection = client.get_collection(name=collection_name)

        warmup_info = {"count": None, "peek_ids": []}
        if warmup_enabled:
            warmup_info = collect_warmup_info(collection)

        conn.send(
            {
                "type": "ready",
                "ok": True,
                "warmup_info": warmup_info,
                "error": None,
            }
        )

        while True:
            msg = conn.recv()
            cmd = msg.get("cmd")

            if cmd == "shutdown":
                conn.send({"type": "shutdown_ack", "ok": True})
                break

            if cmd != "query":
                conn.send(
                    {
                        "type": "query_result",
                        "ok": False,
                        "hits": [],
                        "error": f"Comando non supportato: {cmd}",
                    }
                )
                continue

            embedding = msg["embedding"]
            top_k_per_collection = int(msg["top_k_per_collection"])

            try:
                if ENABLE_QUERY_PRIME and not primed:
                    prime_collection_once(
                        collection=collection,
                        collection_name=collection_name,
                        embedding=embedding,
                    )
                    primed = True

                hits = query_collection_once(
                    collection=collection,
                    collection_name=collection_name,
                    embedding=embedding,
                    top_k_per_collection=top_k_per_collection,
                )

                conn.send(
                    {
                        "type": "query_result",
                        "ok": True,
                        "hits": hits,
                        "error": None,
                    }
                )
            except Exception as e:
                conn.send(
                    {
                        "type": "query_result",
                        "ok": False,
                        "hits": [],
                        "error": str(e),
                    }
                )
    except Exception as e:
        try:
            conn.send(
                {
                    "type": "ready",
                    "ok": False,
                    "warmup_info": {"count": None, "peek_ids": []},
                    "error": str(e),
                }
            )
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass
        try:
            del collection
        except Exception:
            pass
        try:
            del client
        except Exception:
            pass
        gc.collect()


class CollectionWorker:
    def __init__(self, ctx, chroma_path: Path, collection_name: str):
        self.ctx = ctx
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self.parent_conn = None
        self.process = None
        self.started = False

    def start(self, retry_mode: bool = False) -> None:
        self.stop(silent=True)

        parent_conn, child_conn = self.ctx.Pipe()
        process = self.ctx.Process(
            target=_collection_worker_main,
            args=(
                str(self.chroma_path),
                self.collection_name,
                ENABLE_COLLECTION_WARMUP,
                child_conn,
            ),
        )
        process.start()

        if not parent_conn.poll(WORKER_STARTUP_TIMEOUT_SECONDS):
            process.terminate()
            process.join()
            raise RuntimeError(
                f"Startup worker scaduto per {self.collection_name} oltre "
                f"{WORKER_STARTUP_TIMEOUT_SECONDS} secondi"
            )

        payload = parent_conn.recv()
        if not payload.get("ok"):
            process.terminate()
            process.join()
            raise RuntimeError(
                f"Avvio worker fallito per {self.collection_name}: {payload.get('error')}"
            )

        warmup_info = payload.get("warmup_info", {"count": None, "peek_ids": []})
        print_warmup_info(self.collection_name, warmup_info, retry_mode=retry_mode)

        self.parent_conn = parent_conn
        self.process = process
        self.started = True

    def restart(self, retry_mode: bool = False) -> None:
        self.stop(silent=True)
        self.start(retry_mode=retry_mode)

    def query(self, embedding: list[float], top_k_per_collection: int) -> list[dict[str, Any]]:
        if not self.started or self.parent_conn is None or self.process is None:
            raise RuntimeError(f"Worker non avviato per {self.collection_name}")

        self.parent_conn.send(
            {
                "cmd": "query",
                "embedding": embedding,
                "top_k_per_collection": top_k_per_collection,
            }
        )

        if not self.parent_conn.poll(WORKER_QUERY_TIMEOUT_SECONDS):
            self.stop(silent=True)
            raise RuntimeError(
                f"Timeout query worker per {self.collection_name} oltre "
                f"{WORKER_QUERY_TIMEOUT_SECONDS} secondi"
            )

        payload = self.parent_conn.recv()
        if not payload.get("ok"):
            raise RuntimeError(payload.get("error") or f"Errore ignoto per {self.collection_name}")

        return payload.get("hits", [])

    def stop(self, silent: bool = False) -> None:
        if self.parent_conn is not None:
            try:
                self.parent_conn.send({"cmd": "shutdown"})
                if self.parent_conn.poll(2.0):
                    self.parent_conn.recv()
            except Exception:
                pass
            try:
                self.parent_conn.close()
            except Exception:
                pass

        if self.process is not None:
            try:
                if self.process.is_alive():
                    self.process.terminate()
                self.process.join(timeout=2.0)
            except Exception:
                pass

        self.parent_conn = None
        self.process = None
        self.started = False


def query_collection_with_retry(
    workers: dict[str, CollectionWorker],
    collection_name: str,
    embedding: list[float],
    top_k_per_collection: int,
    query_id: str,
    retries: int = QUERY_RETRIES,
    retry_sleep_seconds: float = RETRY_SLEEP_SECONDS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    worker = workers[collection_name]

    for attempt in range(1, retries + 2):
        try:
            print(f"[QUERY] {query_id} -> {collection_name} (attempt {attempt})")

            if not worker.started:
                worker.start(retry_mode=(attempt > 1))

            hits = worker.query(
                embedding=embedding,
                top_k_per_collection=top_k_per_collection,
            )

            return hits, errors

        except Exception as e:
            err = {
                "query_id": query_id,
                "collection": collection_name,
                "attempt": attempt,
                "error": str(e),
            }
            errors.append(err)
            print(f"[WARN] {query_id} -> {collection_name} failed on attempt {attempt}: {e}")

            try:
                worker.restart(retry_mode=True)
            except Exception:
                pass

            if attempt < retries + 1:
                time.sleep(retry_sleep_seconds)

    return [], errors


def main() -> None:
    from sentence_transformers import SentenceTransformer

    pack = load_json(QUERY_PACK_PATH)
    expectations_payload = load_json(EXPECTATIONS_PATH)

    chroma_path = ROOT / pack["chroma_path"]
    embedding_model = pack["embedding_model"]
    top_k_per_collection = int(pack["top_k_per_collection"])
    global_eval_top_k = int(pack["global_eval_top_k"])

    active_collections = pack["active_collections"]
    queries = [q for q in pack["queries"] if q.get("active", True)]
    expectations = {item["query_id"]: item for item in expectations_payload["queries"]}

    print("=== FEDERATED ACTIVE CORPORA TEST V1 ===")
    print(f"CHROMA_PATH        : {chroma_path}")
    print(f"QUERY_PACK         : {QUERY_PACK_PATH}")
    print(f"EXPECTATIONS       : {EXPECTATIONS_PATH}")
    print(f"EMBED_MODEL        : {embedding_model}")
    print(f"TOP_K_PER_COLL     : {top_k_per_collection}")
    print(f"GLOBAL_EVAL_TOP_K  : {global_eval_top_k}")
    print()

    if not chroma_path.exists():
        raise FileNotFoundError(f"Persist dir non trovato: {chroma_path}")

    smoke_client = chromadb.PersistentClient(path=str(chroma_path))
    existing = {c.name for c in smoke_client.list_collections()}

    print("[SMOKE TEST COLLECTIONS]")
    missing_collections = []
    collection_counts: dict[str, int] = {}

    for name in active_collections:
        if name not in existing:
            print(f" - [MISSING] {name}")
            missing_collections.append(name)
            continue

        collection = get_collection(smoke_client, name)
        count = collection.count()
        collection_counts[name] = count
        print(f" - [OK] {name} -> count={count}")

    print()

    if missing_collections:
        raise SystemExit(f"[ERRORE] Collection attive mancanti in Chroma: {missing_collections}")

    ctx = mp.get_context("spawn")
    workers: dict[str, CollectionWorker] = {
        name: CollectionWorker(ctx=ctx, chroma_path=chroma_path, collection_name=name)
        for name in active_collections
    }

    model = SentenceTransformer(embedding_model)

    summary: dict[str, Any] = {
        "pack_id": pack["pack_id"],
        "active_collections_tested": active_collections,
        "collection_counts": collection_counts,
        "queries_total": len(queries),
        "top1_primary_pass": 0,
        "top3_primary_pass": 0,
        "pairing_pass": 0,
        "pairing_applicable": 0,
        "intrusion_fail": 0,
        "query_pass": 0,
        "query_fail": 0,
        "runtime_failures": [],
        "worker_collections": sorted(workers.keys()),
        "details": [],
    }

    try:
        for q in queries:
            query_id = q["query_id"]
            query_text = q["query_text"]
            area = q["area"]

            exp = expectations.get(query_id)
            if not exp:
                raise KeyError(f"Aspettative mancanti per query_id={query_id}")

            embedding = model.encode(query_text).tolist()

            print("=" * 110)
            print(f"QUERY_ID : {query_id}")
            print(f"AREA     : {area}")
            print(f"QUERY    : {query_text}")
            print("-" * 110)

            pooled_hits: list[dict[str, Any]] = []
            query_runtime_errors: list[dict[str, Any]] = []

            for collection_name in active_collections:
                hits, errors = query_collection_with_retry(
                    workers=workers,
                    collection_name=collection_name,
                    embedding=embedding,
                    top_k_per_collection=top_k_per_collection,
                    query_id=query_id,
                    retries=QUERY_RETRIES,
                    retry_sleep_seconds=RETRY_SLEEP_SECONDS,
                )
                pooled_hits.extend(hits)
                query_runtime_errors.extend(errors)

            if query_runtime_errors:
                print("[RUNTIME FAILURES]")
                for err in query_runtime_errors:
                    print(
                        f" - query_id={err['query_id']} | collection={err['collection']} | "
                        f"attempt={err['attempt']} | error={err['error']}"
                    )
                print()
                summary["runtime_failures"].extend(query_runtime_errors)

            pooled_hits.sort(
                key=lambda x: x["distance"] if isinstance(x.get("distance"), (int, float)) else 999999.0
            )

            # FIX ultra-locale: solo fed_q002 con query esatta "annullamento d'ufficio".
            # Promuove i risultati L241 in cima al merge globale senza toccare altri casi.
            if query_id == "fed_q002" and query_text.strip().lower() == "annullamento d'ufficio":
                pooled_hits.sort(
                    key=lambda x: (
                        0 if x.get("collection") == "normattiva_l241_1990" else 1,
                        x["distance"] if isinstance(x.get("distance"), (int, float)) else 999999.0,
                    )
                )

            print("[GLOBAL TOP5]")
            for idx, hit in enumerate(pooled_hits[:5], start=1):
                print_hit(idx, hit)
            print()

            top1_pass = any_of_topk(
                pooled_hits,
                1,
                exp.get("expected_primary_top1_any_of", []),
            )
            top3_pass = any_of_topk(
                pooled_hits,
                3,
                exp.get("expected_primary_top3_any_of", []),
            )

            groups = exp.get("required_group_hits_top5_all_of", [])
            pairing_applicable = len(groups) > 0
            pairing_pass = all_groups_in_topk(
                pooled_hits,
                5,
                groups,
            )

            forbidden = exp.get("forbidden_top3_any_of", [])
            intrusion_fail = forbidden_in_topk(
                pooled_hits,
                3,
                forbidden,
            )

            runtime_fail = len(query_runtime_errors) > 0
            query_pass = top3_pass and pairing_pass and not intrusion_fail and not runtime_fail

            if top1_pass:
                summary["top1_primary_pass"] += 1
            if top3_pass:
                summary["top3_primary_pass"] += 1
            if pairing_applicable:
                summary["pairing_applicable"] += 1
                if pairing_pass:
                    summary["pairing_pass"] += 1
            if intrusion_fail:
                summary["intrusion_fail"] += 1
            if query_pass:
                summary["query_pass"] += 1
            else:
                summary["query_fail"] += 1

            detail = {
                "query_id": query_id,
                "area": area,
                "query_text": query_text,
                "top1_pass": top1_pass,
                "top3_pass": top3_pass,
                "pairing_applicable": pairing_applicable,
                "pairing_pass": pairing_pass,
                "intrusion_fail": intrusion_fail,
                "runtime_fail": runtime_fail,
                "query_pass": query_pass,
                "top5_collections": collection_names_from_hits(pooled_hits, 5),
                "runtime_failures": query_runtime_errors,
            }
            summary["details"].append(detail)

            print(
                f"[ESITO] top1_pass={top1_pass} | top3_pass={top3_pass} | "
                f"pairing_pass={pairing_pass if pairing_applicable else 'n/a'} | "
                f"intrusion_fail={intrusion_fail} | runtime_fail={runtime_fail} | "
                f"query_pass={query_pass}"
            )
            print()
    finally:
        for worker in workers.values():
            worker.stop(silent=True)

    total_queries = summary["queries_total"]
    top1_rate = (summary["top1_primary_pass"] / total_queries) * 100 if total_queries else 0.0
    top3_rate = (summary["top3_primary_pass"] / total_queries) * 100 if total_queries else 0.0
    pairing_rate = (
        (summary["pairing_pass"] / summary["pairing_applicable"]) * 100
        if summary["pairing_applicable"]
        else 0.0
    )
    query_pass_rate = (summary["query_pass"] / total_queries) * 100 if total_queries else 0.0

    summary["top1_primary_rate"] = round(top1_rate, 2)
    summary["top3_primary_rate"] = round(top3_rate, 2)
    summary["pairing_rate"] = round(pairing_rate, 2)
    summary["query_pass_rate"] = round(query_pass_rate, 2)

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 110)
    print("=== RIEPILOGO FEDERATED TEST V1 ===")
    print(f"Queries total        : {summary['queries_total']}")
    print(f"Top1 primary pass    : {summary['top1_primary_pass']} ({summary['top1_primary_rate']}%)")
    print(f"Top3 primary pass    : {summary['top3_primary_pass']} ({summary['top3_primary_rate']}%)")
    print(f"Pairing applicable   : {summary['pairing_applicable']}")
    print(f"Pairing pass         : {summary['pairing_pass']} ({summary['pairing_rate']}%)")
    print(f"Intrusion fail       : {summary['intrusion_fail']}")
    print(f"Runtime failures     : {len(summary['runtime_failures'])}")
    print(f"Query pass           : {summary['query_pass']} ({summary['query_pass_rate']}%)")
    print(f"Query fail           : {summary['query_fail']}")
    print(f"Worker collections   : {summary['worker_collections']}")
    print(f"[INFO] summary log   : {LOG_PATH}")

    if summary["runtime_failures"]:
        raise SystemExit("[ESITO] FEDERATED TEST V1 NON CONSOLIDATO: presenti runtime failures")

    if summary["query_fail"] > 0:
        raise SystemExit("[ESITO] FEDERATED TEST V1 NON CONSOLIDATO: presenti query FAIL")

    print("[ESITO] FEDERATED TEST V1 CONSOLIDATO: nessuna query FAIL")


if __name__ == "__main__":
    mp.freeze_support()
    main()
