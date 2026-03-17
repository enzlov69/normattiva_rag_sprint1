#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from _common import TARGET_COLLECTION, get_client_and_embedding, get_collection, resolve_chroma_path


TEST_QUERIES = [
    "fondo pluriennale vincolato",
    "fpv",
    "esigibilità",
    "reimputazione",
    "cronoprogramma",
    "spesa impegnata ma esigibile esercizi successivi",
    "accertamento entrata esigibile",
    "imputazione contabile",
]

ROUNDS = 5


def main() -> int:
    chroma_path = resolve_chroma_path()
    client, embedding_fn, persist_dir = get_client_and_embedding(chroma_path)
    collection = get_collection(client, embedding_fn, TARGET_COLLECTION)

    total_runs = 0
    failures = 0

    print("=== MINI STRESS TEST all_4_2 ===")
    print(f"Collection  : {TARGET_COLLECTION}")
    print(f"Persist dir : {persist_dir}")
    print(f"Count       : {collection.count()}")
    print(f"Rounds      : {ROUNDS}")
    print("")

    for round_idx in range(1, ROUNDS + 1):
        print(f"[ROUND {round_idx}]")
        for q in TEST_QUERIES:
            total_runs += 1
            try:
                result = collection.query(query_texts=[q], n_results=3)
                ids = result.get("ids", [[]])[0]
                print(f" - OK     :: {q} :: hits={len(ids)}")
            except Exception as exc:
                failures += 1
                print(f" - FAIL   :: {q} :: {exc}")
        print("")

    print("=== ESITO MINI STRESS ===")
    print(f"Total runs : {total_runs}")
    print(f"Failures   : {failures}")
    if failures > 0:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
