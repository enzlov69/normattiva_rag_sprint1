from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from _common import (
    COLLECTION_NAME,
    DEFAULT_CHROMA_PATH,
    DEFAULT_EMBED_MODEL,
    get_client,
    load_manifest,
    load_model,
    load_records_from_jsonl,
    print_header,
    safe_peek_ids,
    save_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reingest pulito della collection normattiva_l241_1990."
    )
    parser.add_argument(
        "--source-file",
        type=str,
        default="",
        help="JSONL sorgente esplicito. Se omesso usa il manifest.",
    )
    parser.add_argument(
        "--chroma-path",
        type=str,
        default=str(DEFAULT_CHROMA_PATH),
        help="Persist dir di Chroma.",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default=DEFAULT_EMBED_MODEL,
        help="Embedding model.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Dimensione batch add/embedding.",
    )
    args = parser.parse_args()

    chroma_path = Path(args.chroma_path).resolve()
    batch_size = max(1, int(args.batch_size))

    manifest = load_manifest()
    source_path = ""

    if args.source_file:
        source_path = str(Path(args.source_file).resolve())
    elif manifest and manifest.get("verified_source_path"):
        source_path = str(Path(manifest["verified_source_path"]).resolve())

    if not source_path:
        raise SystemExit(
            "[ERRORE] Nessun file sorgente disponibile. Esegui prima 00_verify_l241_sources.py oppure usa --source-file."
        )

    source_file = Path(source_path)
    if not source_file.exists():
        raise SystemExit(f"[ERRORE] File sorgente non trovato: {source_file}")

    print_header("REINGEST L241 COLLECTION")
    print(f"COLLECTION   : {COLLECTION_NAME}")
    print(f"CHROMA_PATH  : {chroma_path}")
    print(f"SOURCE_FILE  : {source_file}")
    print(f"MODEL        : {args.embedding_model}")
    print(f"BATCH_SIZE   : {batch_size}")
    print()

    ids, docs, metas = load_records_from_jsonl(source_file)

    print("[SOURCE LOADED]")
    print(f"records      : {len(ids)}")
    print()

    client = get_client(chroma_path)
    existing = {c.name for c in client.list_collections()}
    if COLLECTION_NAME in existing:
        raise SystemExit(
            f"[ERRORE] La collection {COLLECTION_NAME} esiste già. Cancella prima con 01_delete_l241_collection_safe.py."
        )

    model = load_model(args.embedding_model)
    collection = client.create_collection(name=COLLECTION_NAME)

    inserted = 0
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        batch_ids = ids[start:end]
        batch_docs = docs[start:end]
        batch_metas = metas[start:end]

        batch_embeddings = model.encode(batch_docs, show_progress_bar=False)
        if hasattr(batch_embeddings, "tolist"):
            batch_embeddings = batch_embeddings.tolist()

        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_metas,
            embeddings=batch_embeddings,
        )
        inserted += len(batch_ids)
        print(f"[BATCH] inserted={inserted}")

    final_count = int(collection.count())
    final_peek = safe_peek_ids(collection, limit=3)

    print()
    print("[FINAL]")
    print(f"count        : {final_count}")
    print(f"peek_ids     : {final_peek}")
    print()

    updated = manifest.copy() if manifest else {}
    updated["collection_name"] = COLLECTION_NAME
    updated["chroma_path"] = str(chroma_path)
    updated["verified_source_path"] = str(source_file)
    updated["reingest_model"] = args.embedding_model
    updated["reingest_batch_size"] = batch_size
    updated["reingest_inserted"] = inserted
    updated["reingest_final_count"] = final_count
    updated["reingest_peek_ids"] = final_peek
    updated["reingested_at"] = datetime.now().isoformat(timespec="seconds")
    save_manifest(updated)

    if final_count != len(ids):
        raise SystemExit(
            f"[ERRORE] Reingest incompleto: attesi {len(ids)} record, trovati {final_count}."
        )

    print("[ESITO] REINGEST OK")


if __name__ == "__main__":
    main()