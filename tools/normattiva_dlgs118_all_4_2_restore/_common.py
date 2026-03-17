#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

TARGET_COLLECTION = "normattiva_dlgs118_2011_all_4_2"
EMBED_MODEL = os.environ.get(
    "NR_EMBED_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)

PROJECT_ROOT_CANDIDATES = [
    Path.cwd(),
    Path.cwd().parent,
    Path(__file__).resolve().parents[1] if len(Path(__file__).resolve().parents) >= 2 else Path.cwd(),
    Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) >= 3 else Path.cwd(),
]

CHROMA_CANDIDATES = [
    Path("data/chroma"),
    Path("../data/chroma"),
    Path("../../data/chroma"),
]

ALL_4_2_SOURCE_CANDIDATES = {
    "canonical_cleantext": [
        # path "attesi" standard
        Path("data/normalized/annexes_118/all_4_2/all_4_2_canonical_cleantext.txt"),
        Path("data/normalized/annexes_118/all_4_2/all_4_2_canonical_clean.txt"),
        Path("data/normalized/annexes_118/all_4_2/all_4_2_canonical_fixed.txt"),
        Path("data/normalized/annexes_118/all_4_2_canonical_cleantext.txt"),
        Path("data/normalized/annexes_118/all_4_2_canonical_clean.txt"),
        Path("data/normalized/annexes_118/all_4_2_canonical_fixed.txt"),
        # path reali emersi dal discovery
        Path("cantiere_118/data/normalized/annexes_118/all_4_2/all_4_2_canonical_clean.txt"),
        Path("cantiere_118/data/normalized/annexes_118/all_4_2/all_4_2_canonical_fixed.txt"),
    ],
    "chunks_jsonl": [
        # path standard
        Path("data/chunks/annexes_118/all_4_2_chunks.jsonl"),
        Path("data/chunks/all_4_2_chunks.jsonl"),
        # path reale emerso dal discovery
        Path("cantiere_118/data/chunks/annexes_118/all_4_2_chunks.jsonl"),
    ],
    "rag_ready_jsonl": [
        Path("data/rag_ready/normattiva_dlgs118_2011_all_4_2.jsonl"),
        Path("data/rag_ready/annexes_118/normattiva_dlgs118_2011_all_4_2.jsonl"),
        Path("data/processed/rag_ready/normattiva_dlgs118_2011_all_4_2.jsonl"),
    ],
    "document_level_dir": [
        Path("data/processed/annexes_118/all_4_2"),
        Path("data/normalized/norm_units/dlgs118_2011_all_4_2"),
        Path("data/processed/dlgs118_2011/all_4_2"),
        Path("cantiere_118/data/processed/annexes_118/all_4_2"),
    ],
}


def eprint(*args: Any, **kwargs: Any) -> None:
    print(*args, file=sys.stderr, **kwargs)


def find_existing_path(candidates: Iterable[Path]) -> Optional[Path]:
    for base in PROJECT_ROOT_CANDIDATES:
        for rel in candidates:
            p = (base / rel).resolve()
            if p.exists():
                return p
    return None


def find_repo_root() -> Path:
    markers = [
        ".git",
        "pyproject.toml",
        "requirements.txt",
        "data",
        "tools",
        "tests",
    ]
    for base in PROJECT_ROOT_CANDIDATES:
        score = sum(1 for m in markers if (base / m).exists())
        if score >= 2:
            return base.resolve()
    return Path.cwd().resolve()


def resolve_chroma_path() -> Path:
    root = find_repo_root()
    for rel in CHROMA_CANDIDATES:
        p = (root / rel).resolve()
        if p.exists():
            return p
    return (root / "data/chroma").resolve()


def resolve_source_map() -> Dict[str, Optional[Path]]:
    return {
        key: find_existing_path(candidates)
        for key, candidates in ALL_4_2_SOURCE_CANDIDATES.items()
    }


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for idx, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"JSONL non valido in {path} riga {idx}: {exc}") from exc
    return rows


def dump_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def coerce_scalar(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return " | ".join(str(x) for x in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def sanitize_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    clean: Dict[str, Any] = {}
    for k, v in meta.items():
        if v is None:
            continue
        if k in {"embedding", "embeddings", "vector", "chunk_text", "text", "document"}:
            continue
        clean[str(k)] = coerce_scalar(v)
    return clean


def normalize_record(raw: Dict[str, Any], seq: int) -> Dict[str, Any]:
    record_id = (
        raw.get("id")
        or raw.get("chunk_id")
        or raw.get("record_id")
        or raw.get("norm_unit_id")
        or f"{TARGET_COLLECTION}::row_{seq:04d}"
    )
    document = (
        raw.get("document")
        or raw.get("chunk_text")
        or raw.get("text")
        or raw.get("testo_unita")
        or ""
    )
    if not isinstance(document, str):
        document = str(document)
    document = document.strip()

    metadata = raw.get("metadata")
    if isinstance(metadata, dict):
        meta = dict(metadata)
    else:
        meta = {
            k: v for k, v in raw.items()
            if k not in {
                "id", "chunk_id", "record_id",
                "document", "chunk_text", "text", "testo_unita",
                "metadata"
            }
        }

    meta.setdefault("source_collection", TARGET_COLLECTION)
    meta.setdefault("rebuild_sequence", seq)
    meta.setdefault("record_origin", raw.get("record_origin") or "unknown")
    meta = sanitize_metadata(meta)

    return {
        "id": str(record_id),
        "document": document,
        "metadata": meta,
    }


def import_chromadb():
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        return chromadb, embedding_functions
    except Exception as exc:
        raise RuntimeError(
            "Impossibile importare chromadb. Attiva il venv corretto e verifica le dipendenze."
        ) from exc


def get_client_and_embedding(chroma_path: Optional[Path] = None):
    chromadb, embedding_functions = import_chromadb()
    persist_dir = (chroma_path or resolve_chroma_path()).resolve()
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )
    return client, embedding_fn, persist_dir


def get_collection(client, embedding_fn, name: str = TARGET_COLLECTION):
    return client.get_collection(name=name, embedding_function=embedding_fn)


def get_or_create_collection(client, embedding_fn, name: str = TARGET_COLLECTION):
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
        embedding_function=embedding_fn,
    )


def collection_count(client, name: str = TARGET_COLLECTION) -> int:
    try:
        coll = client.get_collection(name=name)
        return coll.count()
    except Exception:
        return 0