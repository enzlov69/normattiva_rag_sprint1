from __future__ import annotations

import argparse

from _common import (
    COLLECTION_NAME,
    DEFAULT_CHROMA_PATH,
    DEFAULT_EMBED_MODEL,
    STRESS_QUERIES,
    count_collection,
    encode_query,
    get_client,
    get_collection,
    load_model,
    preview_text,
    print_header,
    safe_peek_ids,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stress test L241 con fresh client loop.")
    parser.add_argument(
        "--loops",
        type=int,
        default=8,
        help="Numero loop completi sulle query.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Numero risultati per query.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print_header("STRESS TEST L241")
    print(f"COLLECTION   : {COLLECTION_NAME}")
    print(f"CHROMA_PATH  : {DEFAULT_CHROMA_PATH}")
    print(f"EMBED_MODEL  : {DEFAULT_EMBED_MODEL}")
    print(f"LOOPS        : {args.loops}")
    print(f"TOP_K        : {args.top_k}")
    print()

    model = load_model(DEFAULT_EMBED_MODEL)
    failures: list[str] = []

    for loop_idx in range(1, args.loops + 1):
        print(f"[LOOP {loop_idx}/{args.loops}]")
        for query in STRESS_QUERIES:
            try:
                client = get_client(DEFAULT_CHROMA_PATH)
                collection = get_collection(client, COLLECTION_NAME)

                count = count_collection(collection)
                peek_ids = safe_peek_ids(collection, limit=3)

                if count <= 0:
                    raise RuntimeError(f"count non valido: {count}")

                query_embedding = encode_query(model, query)
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=args.top_k,
                    include=["documents", "metadatas", "distances"],
                )

                ids = (results.get("ids") or [[]])[0]
                docs = (results.get("documents") or [[]])[0]
                distances = (results.get("distances") or [[]])[0]

                if not ids:
                    raise RuntimeError("nessun risultato")

                top_id = ids[0]
                top_doc = docs[0] if docs else ""
                top_dist = distances[0] if distances else None
                dist_txt = f"{top_dist:.6f}" if isinstance(top_dist, (int, float)) else "n/a"

                print(
                    f"  [OK] query={query} | count={count} | peek_ids={peek_ids} | "
                    f"top_id={top_id} | dist={dist_txt} | text={preview_text(top_doc, 120)}"
                )

            except Exception as e:
                msg = f"loop={loop_idx} | query={query} | error={e}"
                failures.append(msg)
                print(f"  [FAIL] {msg}")

        print()

    print(f"[SUMMARY] failures={len(failures)}")
    if failures:
        for item in failures:
            print(f" - {item}")
        raise SystemExit("[ESITO] STRESS FAIL")

    print("[ESITO] STRESS OK")


if __name__ == "__main__":
    main()