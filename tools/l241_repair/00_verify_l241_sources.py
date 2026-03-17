from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from _common import (
    COLLECTION_NAME,
    DEFAULT_CHROMA_PATH,
    DEFAULT_EXPORT_PATH,
    discover_source_files,
    ensure_generated_dir,
    export_collection_to_jsonl,
    get_client,
    load_records_from_jsonl,
    print_header,
    save_manifest,
    safe_peek_ids,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verifica il sorgente L. 241/1990 oppure crea un backup esportando la collection attuale."
    )
    parser.add_argument(
        "--source-file",
        type=str,
        default="",
        help="Percorso manuale del file JSONL sorgente.",
    )
    parser.add_argument(
        "--chroma-path",
        type=str,
        default=str(DEFAULT_CHROMA_PATH),
        help="Persist dir di Chroma.",
    )
    args = parser.parse_args()

    chroma_path = Path(args.chroma_path).resolve()
    ensure_generated_dir()

    print_header("VERIFY L241 SOURCES")
    print(f"COLLECTION   : {COLLECTION_NAME}")
    print(f"CHROMA_PATH  : {chroma_path}")
    print()

    client = get_client(chroma_path)
    existing_names = {c.name for c in client.list_collections()}
    collection_exists = COLLECTION_NAME in existing_names

    collection_count = 0
    collection_peek_ids: list[str] = []

    if collection_exists:
        collection = client.get_collection(COLLECTION_NAME)
        collection_count = int(collection.count())
        collection_peek_ids = safe_peek_ids(collection, limit=3)
        print("[COLLECTION STATO]")
        print(f"exists    : True")
        print(f"count     : {collection_count}")
        print(f"peek_ids  : {collection_peek_ids}")
        print()
    else:
        print("[COLLECTION STATO]")
        print("exists    : False")
        print()

    candidate_sources: list[Path] = []

    if args.source_file:
        manual = Path(args.source_file).resolve()
        candidate_sources.append(manual)
    else:
        candidate_sources.extend(discover_source_files())

    verified_source: Path | None = None
    source_mode = ""
    verified_records = 0

    print("[SOURCE CANDIDATES]")
    if candidate_sources:
        for p in candidate_sources:
            print(f" - {p}")
    else:
        print(" - nessun file sorgente trovato automaticamente")
    print()

    for source_path in candidate_sources:
        if not source_path.exists():
            continue
        try:
            ids, docs, metas = load_records_from_jsonl(source_path)
            verified_source = source_path
            verified_records = len(ids)
            source_mode = "existing_jsonl"
            print("[SOURCE VERIFIED]")
            print(f"path       : {verified_source}")
            print(f"records    : {verified_records}")
            print()
            break
        except Exception as e:
            print(f"[WARN] sorgente non valido: {source_path} -> {e}")

    if verified_source is None:
        if not collection_exists or collection_count <= 0:
            raise SystemExit(
                "[ERRORE] Nessun file sorgente valido trovato e nessuna collection esportabile presente."
            )

        print("[EXPORT FALLBACK]")
        print("Nessun JSONL sorgente trovato: provo a esportare la collection corrente.")
        print()

        exported_count, exported_path = export_collection_to_jsonl(
            chroma_path=chroma_path,
            collection_name=COLLECTION_NAME,
            output_path=DEFAULT_EXPORT_PATH,
        )

        ids, docs, metas = load_records_from_jsonl(exported_path)
        verified_source = exported_path
        verified_records = len(ids)
        source_mode = "export_from_collection"

        print("[EXPORT VERIFIED]")
        print(f"path       : {verified_source}")
        print(f"records    : {verified_records}")
        print(f"exported   : {exported_count}")
        print()

    manifest = {
        "collection_name": COLLECTION_NAME,
        "chroma_path": str(chroma_path),
        "verified_source_path": str(verified_source),
        "verified_source_mode": source_mode,
        "verified_records": verified_records,
        "collection_existed_at_verify": collection_exists,
        "collection_count_at_verify": collection_count,
        "collection_peek_ids_at_verify": collection_peek_ids,
        "verified_at": datetime.now().isoformat(timespec="seconds"),
    }

    save_manifest(manifest)

    print("[MANIFEST WRITTEN]")
    print(f"verified_source_path : {manifest['verified_source_path']}")
    print(f"verified_source_mode : {manifest['verified_source_mode']}")
    print(f"verified_records     : {manifest['verified_records']}")
    print()
    print("[ESITO] VERIFY OK")


if __name__ == "__main__":
    main()