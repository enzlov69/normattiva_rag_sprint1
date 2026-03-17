#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from _common import TARGET_COLLECTION, find_repo_root, resolve_source_map, load_jsonl, dump_jsonl, normalize_record


def build_from_chunks(chunks_path: Path) -> List[Dict[str, Any]]:
    raw_rows = load_jsonl(chunks_path)
    out: List[Dict[str, Any]] = []
    for idx, row in enumerate(raw_rows, start=1):
        row = dict(row)
        row["record_origin"] = "chunks_jsonl"
        norm = normalize_record(row, idx)
        if norm["document"]:
            out.append(norm)
    return out


def build_from_document_dir(doc_dir: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    json_files = sorted(doc_dir.rglob("*.json"))
    for idx, p in enumerate(json_files, start=1):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            data["record_origin"] = "document_level_json"
            norm = normalize_record(data, idx)
            if norm["document"]:
                out.append(norm)
    return out


def build_from_canonical_text(txt_path: Path) -> List[Dict[str, Any]]:
    text = txt_path.read_text(encoding="utf-8")
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    out: List[Dict[str, Any]] = []
    for idx, para in enumerate(paragraphs, start=1):
        digest = hashlib.sha1(para.encode("utf-8")).hexdigest()[:12]
        out.append(
            {
                "id": f"{TARGET_COLLECTION}::canon_{idx:04d}_{digest}",
                "document": para,
                "metadata": {
                    "source_collection": TARGET_COLLECTION,
                    "record_origin": "canonical_cleantext_fallback",
                    "paragraph_index": idx,
                },
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild rag_ready per all_4_2")
    parser.add_argument("--force", action="store_true", help="Rigenera anche se il file rag_ready esiste già.")
    args = parser.parse_args()

    repo_root = find_repo_root()
    source_map = resolve_source_map()
    rag_ready_path = repo_root / "data/rag_ready/normattiva_dlgs118_2011_all_4_2.jsonl"

    if rag_ready_path.exists() and not args.force:
        print("Rag-ready già presente; nessuna azione.")
        print(f"File: {rag_ready_path}")
        return 0

    rows: List[Dict[str, Any]] = []

    if source_map["chunks_jsonl"] and source_map["chunks_jsonl"].exists():
        rows = build_from_chunks(source_map["chunks_jsonl"])
        strategy = "chunks_jsonl"
    elif source_map["document_level_dir"] and source_map["document_level_dir"].exists():
        rows = build_from_document_dir(source_map["document_level_dir"])
        strategy = "document_level_dir"
    elif source_map["canonical_cleantext"] and source_map["canonical_cleantext"].exists():
        rows = build_from_canonical_text(source_map["canonical_cleantext"])
        strategy = "canonical_cleantext_fallback"
    else:
        raise SystemExit(
            "ERRORE: nessuna sorgente utilizzabile trovata per il rebuild "
            "(né chunks_jsonl, né document_level_dir, né canonical_cleantext)."
        )

    if not rows:
        raise SystemExit(f"ERRORE: rebuild completato ma nessun record utile prodotto da {strategy}.")

    dump_jsonl(rag_ready_path, rows)
    print("=== REBUILD RAG_READY COMPLETATO ===")
    print(f"Strategia usata : {strategy}")
    print(f"Output file     : {rag_ready_path}")
    print(f"Record prodotti : {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
