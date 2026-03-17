#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from pathlib import Path

from _common import TARGET_COLLECTION, find_repo_root, resolve_chroma_path, resolve_source_map, get_client_and_embedding, collection_count


def main() -> int:
    repo_root = find_repo_root()
    chroma_path = resolve_chroma_path()
    source_map = resolve_source_map()

    print("=== CHECK PERIMETRO SORGENTI — all_4_2 ===")
    print(f"Repo root           : {repo_root}")
    print(f"Target collection   : {TARGET_COLLECTION}")
    print(f"Chroma path         : {chroma_path}")
    print("")

    print("[SORGENTI ATTESE]")
    for key, value in source_map.items():
        status = "OK" if value and value.exists() else "MISSING"
        print(f" - {key:20s}: {status} :: {value if value else 'non trovato'}")

    print("")
    try:
        client, _embedding_fn, _persist_dir = get_client_and_embedding(chroma_path)
        count = collection_count(client, TARGET_COLLECTION)
        print("[COLLECTION STATO]")
        print(f" - name   : {TARGET_COLLECTION}")
        print(f" - count  : {count}")
    except Exception as exc:
        print("[COLLECTION STATO]")
        print(f" - errore accesso Chroma: {exc}")

    print("")
    print("[ESITO DIAGNOSTICO]")
    print(
        "Se la collection esiste, ha count > 0, ma la query runtime fallisce con "
        "'Error creating hnsw segment reader: Nothing found on disk', "
        "la diagnosi più probabile è disallineamento tra registry/logical collection "
        "e artefatti HNSW fisici su disco della sola collection."
    )
    print(
        "In tale scenario la misura corretta è: verificare sorgente -> eventuale rebuild rag_ready "
        "-> delete sicuro della sola collection -> reingest pulito -> smoke/stress test."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
