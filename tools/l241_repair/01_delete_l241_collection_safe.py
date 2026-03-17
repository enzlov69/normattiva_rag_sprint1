from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from _common import (
    COLLECTION_NAME,
    DEFAULT_CHROMA_PATH,
    MANIFEST_PATH,
    get_client,
    load_manifest,
    print_header,
    save_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cancella in modo sicuro solo la collection normattiva_l241_1990."
    )
    parser.add_argument(
        "--chroma-path",
        type=str,
        default=str(DEFAULT_CHROMA_PATH),
        help="Persist dir di Chroma.",
    )
    parser.add_argument(
        "--yes-delete",
        action="store_true",
        help="Conferma esplicita della cancellazione.",
    )
    args = parser.parse_args()

    chroma_path = Path(args.chroma_path).resolve()

    print_header("DELETE L241 COLLECTION SAFE")
    print(f"COLLECTION   : {COLLECTION_NAME}")
    print(f"CHROMA_PATH  : {chroma_path}")
    print()

    manifest = load_manifest()
    if not manifest:
        raise SystemExit(
            "[ERRORE] Nessun manifest trovato. Esegui prima 00_verify_l241_sources.py."
        )

    source_path = manifest.get("verified_source_path", "")
    if not source_path:
        raise SystemExit(
            "[ERRORE] Manifest privo di verified_source_path. Riesegui 00_verify_l241_sources.py."
        )

    source_file = Path(source_path)
    if not source_file.exists():
        raise SystemExit(
            "[ERRORE] Nessun sorgente/backup verificato. Esegui prima 00_verify_l241_sources.py e non cancellare la collection."
        )

    print("[MANIFEST]")
    print(f"path       : {MANIFEST_PATH}")
    print(f"source     : {source_file}")
    print(f"mode       : {manifest.get('verified_source_mode', '')}")
    print(f"records    : {manifest.get('verified_records', '')}")
    print()

    client = get_client(chroma_path)
    existing = {c.name for c in client.list_collections()}

    if COLLECTION_NAME not in existing:
        print("[INFO] Collection già assente.")
        print("[ESITO] DELETE SAFE OK")
        return

    if not args.yes_delete:
        print("[DRY RUN] La collection esiste ma non è stata cancellata.")
        print("Per procedere usa: --yes-delete")
        return

    client.delete_collection(COLLECTION_NAME)

    updated = dict(manifest)
    updated["deleted_at"] = datetime.now().isoformat(timespec="seconds")
    updated["deleted_collection_name"] = COLLECTION_NAME
    updated["deleted_on_chroma_path"] = str(chroma_path)
    save_manifest(updated)

    print("[DELETE EXECUTED]")
    print(f"collection  : {COLLECTION_NAME}")
    print("[ESITO] DELETE SAFE OK")


if __name__ == "__main__":
    main()