#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse

from _common import TARGET_COLLECTION, get_client_and_embedding, resolve_chroma_path, collection_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete sicuro della sola collection all_4_2")
    parser.add_argument("--yes", action="store_true", help="Conferma esplicita della cancellazione.")
    args = parser.parse_args()

    if not args.yes:
        raise SystemExit(
            "Operazione bloccata. Riesegui con --yes per cancellare solo la collection "
            f"{TARGET_COLLECTION}."
        )

    chroma_path = resolve_chroma_path()
    client, _embedding_fn, _persist_dir = get_client_and_embedding(chroma_path)
    before_count = collection_count(client, TARGET_COLLECTION)

    try:
        client.delete_collection(TARGET_COLLECTION)
        print("=== DELETE COLLECTION OK ===")
        print(f"Collection  : {TARGET_COLLECTION}")
        print(f"Count prima : {before_count}")
    except Exception as exc:
        raise SystemExit(f"DELETE FAILED su {TARGET_COLLECTION}: {exc}") from exc

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
