#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from _common import TARGET_COLLECTION, get_client_and_embedding, get_collection, resolve_chroma_path


TEST_QUERIES = [
    "fondo pluriennale vincolato",
    "esigibilità della spesa",
    "reimputazione degli impegni",
    "cronoprogramma",
    "accertate entrate esigibili",
]


def main() -> int:
    chroma_path = resolve_chroma_path()
    client, embedding_fn, persist_dir = get_client_and_embedding(chroma_path)
    collection = get_collection(client, embedding_fn, TARGET_COLLECTION)

    print("=== SMOKE TEST all_4_2 ===")
    print(f"Collection  : {TARGET_COLLECTION}")
    print(f"Persist dir : {persist_dir}")
    print(f"Count       : {collection.count()}")
    print("")

    for q in TEST_QUERIES:
        result = collection.query(query_texts=[q], n_results=3)
        docs = result.get("documents", [[]])[0]
        ids = result.get("ids", [[]])[0]
        print(f"[QUERY] {q}")
        print(f" - hits: {len(ids)}")
        if ids:
            preview = (docs[0] or "").replace("\n", " ")[:180]
            print(f" - top1 id     : {ids[0]}")
            print(f" - top1 preview: {preview}")
        else:
            print(" - nessun risultato")
        print("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
