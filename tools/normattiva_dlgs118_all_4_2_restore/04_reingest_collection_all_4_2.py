#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from typing import Any, Dict, List

from _common import (
    TARGET_COLLECTION,
    find_repo_root,
    get_client_and_embedding,
    get_or_create_collection,
    load_jsonl,
    normalize_record,
    resolve_chroma_path,
)


BATCH_SIZE = 32


def main() -> int:
    parser = argparse.ArgumentParser(description="Reingest pulito della sola collection all_4_2")
    parser.add_argument("--replace", action="store_true", help="Se la collection esiste, la cancella e la ricrea.")
    args = parser.parse_args()

    repo_root = find_repo_root()
    rag_ready_path = repo_root / "data/rag_ready/normattiva_dlgs118_2011_all_4_2.jsonl"
    if not rag_ready_path.exists():
        raise SystemExit(
            f"Rag-ready non trovato: {rag_ready_path}. "
            "Esegui prima 02_rebuild_all_4_2_rag_ready.py."
        )

    raw_rows = load_jsonl(rag_ready_path)
    rows = [normalize_record(row, idx) for idx, row in enumerate(raw_rows, start=1)]
    rows = [r for r in rows if r["document"]]

    if not rows:
        raise SystemExit("Il rag_ready esiste ma non contiene documenti utilizzabili.")

    chroma_path = resolve_chroma_path()
    client, embedding_fn, persist_dir = get_client_and_embedding(chroma_path)

    existing = [c.name for c in client.list_collections()]
    if TARGET_COLLECTION in existing and args.replace:
        client.delete_collection(TARGET_COLLECTION)

    collection = get_or_create_collection(client, embedding_fn, TARGET_COLLECTION)

    # Se --replace non è usato ma la collection contiene già dati, falliamo per evitare doppioni.
    existing_count = collection.count()
    if existing_count > 0 and not args.replace:
        raise SystemExit(
            f"La collection {TARGET_COLLECTION} esiste già con count={existing_count}. "
            "Usa --replace dopo il delete o dopo verifica esplicita."
        )

    total = len(rows)
    for start in range(0, total, BATCH_SIZE):
        batch = rows[start : start + BATCH_SIZE]
        ids = [x["id"] for x in batch]
        documents = [x["document"] for x in batch]
        metadatas = [x["metadata"] for x in batch]
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        print(f"[ADD] {start + 1:04d}-{start + len(batch):04d}/{total}")

    print("")
    print("=== REINGEST COMPLETATO ===")
    print(f"Collection finale : {TARGET_COLLECTION}")
    print(f"Persist dir       : {persist_dir}")
    print(f"Count finale      : {collection.count()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
