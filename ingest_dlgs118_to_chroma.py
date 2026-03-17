#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def norm_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"File non trovato: {path}")
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSONL non valido in {path} riga {line_no}: {exc}") from exc
    return rows


def batched(items: List[Any], batch_size: int) -> Iterable[List[Any]]:
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def get_embedding_function(model_name: str):
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except Exception as exc:
        raise RuntimeError(
            "Impossibile importare SentenceTransformerEmbeddingFunction. "
            "Verifica di avere installato chromadb e sentence-transformers."
        ) from exc
    return SentenceTransformerEmbeddingFunction(model_name=model_name)


def ingest_fulltext_collection(
    client,
    embedding_fn,
    collection_name: str,
    input_path: Path,
    metadata: Dict[str, Any],
    reset_collection: bool,
) -> Dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(f"File fulltext non trovato: {input_path}")

    if reset_collection:
        try:
            client.delete_collection(collection_name)
            print(f"Collection eliminata: {collection_name}")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata=metadata,
        embedding_function=embedding_fn,
    )

    text = input_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"File fulltext vuoto: {input_path}")

    doc_id = f"{collection_name}::fulltext"
    doc_meta = {
        **metadata,
        "record_type": "FullTextRecord",
        "chunk_id": doc_id,
        "source_path": str(input_path),
        "citation_text": f"{metadata.get('atto_tipo', '')} n. {metadata.get('atto_numero', '')}/{metadata.get('atto_anno', '')}",
    }

    collection.upsert(
        ids=[doc_id],
        documents=[text],
        metadatas=[doc_meta],
    )

    return {
        "collection": collection_name,
        "mode": "fulltext",
        "input_path": str(input_path),
        "count": collection.count(),
    }


def build_chunk_metadata(
    collection_name: str,
    source_path: Path,
    row: Dict[str, Any],
    default_meta: Dict[str, Any],
    idx: int,
) -> Dict[str, Any]:
    meta = dict(default_meta)
    meta["record_type"] = "ChunkRecord"
    meta["source_path"] = str(source_path)

    for key in [
        "chunk_id",
        "source_id",
        "norm_unit_id",
        "article_id",
        "articolo",
        "comma",
        "rubrica",
        "titolo",
        "hierarchy_path",
        "trace_id",
        "quality_flag",
    ]:
        if key in row:
            meta[key] = norm_str(row.get(key))

    if "chunk_sequence" in row:
        try:
            meta["chunk_sequence"] = int(row.get("chunk_sequence") or 0)
        except Exception:
            meta["chunk_sequence"] = idx

    if "parse_confidence" in row:
        try:
            meta["parse_confidence"] = float(row.get("parse_confidence") or 0.0)
        except Exception:
            meta["parse_confidence"] = 0.0

    return meta


def extract_chunk_text(row: Dict[str, Any]) -> str:
    for key in ["chunk_text", "text", "content", "document"]:
        val = row.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def extract_chunk_id(collection_name: str, row: Dict[str, Any], idx: int) -> str:
    for key in ["chunk_id", "id", "record_id"]:
        val = norm_str(row.get(key))
        if val:
            return val
    return f"{collection_name}::chunk::{idx:05d}"


def ingest_chunk_collection(
    client,
    embedding_fn,
    collection_name: str,
    input_path: Path,
    metadata: Dict[str, Any],
    batch_size: int,
    reset_collection: bool,
) -> Dict[str, Any]:
    rows = load_jsonl(input_path)

    if reset_collection:
        try:
            client.delete_collection(collection_name)
            print(f"Collection eliminata: {collection_name}")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata=metadata,
        embedding_function=embedding_fn,
    )

    records: List[Dict[str, Any]] = []
    skipped = 0

    for idx, row in enumerate(rows, start=1):
        text = extract_chunk_text(row)
        if not text:
            skipped += 1
            continue

        chunk_id = extract_chunk_id(collection_name, row, idx)
        meta = build_chunk_metadata(collection_name, input_path, row, metadata, idx)

        articolo = norm_str(meta.get("articolo"))
        comma = norm_str(meta.get("comma"))
        citation = f"{metadata.get('atto_tipo', '')} n. {metadata.get('atto_numero', '')}/{metadata.get('atto_anno', '')}"
        if articolo:
            citation += f", art. {articolo}"
        if comma:
            citation += f", comma {comma}"
        meta["citation_text"] = citation

        records.append({
            "id": chunk_id,
            "document": text,
            "metadata": meta,
        })

    if not records:
        raise ValueError(f"Nessun chunk ingestibile trovato in: {input_path}")

    for batch_no, batch in enumerate(batched(records, batch_size), start=1):
        ids = [x["id"] for x in batch]
        docs = [x["document"] for x in batch]
        metas = [x["metadata"] for x in batch]

        collection.upsert(ids=ids, documents=docs, metadatas=metas)
        print(f"{collection_name} - batch {batch_no}: ingestiti {len(batch)} chunk")

    return {
        "collection": collection_name,
        "mode": "chunked",
        "input_path": str(input_path),
        "ingested_chunks": len(records),
        "skipped_chunks": skipped,
        "count": collection.count(),
    }


def run_ingest(args: argparse.Namespace) -> int:
    try:
        import chromadb
    except Exception as exc:
        eprint("Errore: chromadb non installato o non importabile.")
        eprint(str(exc))
        return 2

    client = chromadb.PersistentClient(path=args.persist_dir)
    embedding_fn = get_embedding_function(args.embedding_model)

    jobs = [
        {
            "collection": "normattiva_dlgs118_2011_main",
            "mode": "fulltext",
            "path": Path("cantiere_118/data/normalized/main_text/dlgs118_2011_rebuilt_clean.txt"),
            "meta": {
                "domain_code": "dlgs118_2011",
                "source_layer": "B",
                "schema_version": "v2",
                "atto_tipo": "Decreto legislativo",
                "atto_numero": "118",
                "atto_anno": "2011",
                "titolo": "Disposizioni in materia di armonizzazione dei sistemi contabili e degli schemi di bilancio",
            },
        },
        {
            "collection": "normattiva_dlgs126_2014_main",
            "mode": "fulltext",
            "path": Path("cantiere_118/data/normalized/main_text/dlgs126_2014_rebuilt_clean.txt"),
            "meta": {
                "domain_code": "dlgs126_2014",
                "source_layer": "B",
                "schema_version": "v2",
                "atto_tipo": "Decreto legislativo",
                "atto_numero": "126",
                "atto_anno": "2014",
                "titolo": "Disposizioni integrative e correttive del decreto legislativo 23 giugno 2011, n. 118",
            },
        },
        {
            "collection": "normattiva_dlgs118_2011_all_1",
            "mode": "chunked",
            "path": Path("cantiere_118/data/chunks/annexes_118/all_1_chunks.jsonl"),
            "meta": {
                "domain_code": "dlgs118_2011_all_1",
                "source_layer": "B",
                "schema_version": "v2",
                "atto_tipo": "D.Lgs.",
                "atto_numero": "118",
                "atto_anno": "2011",
                "titolo": "Allegato 1 - Principi generali o postulati",
                "allegato": "1",
            },
        },
        {
            "collection": "normattiva_dlgs118_2011_all_4_1",
            "mode": "chunked",
            "path": Path("cantiere_118/data/chunks/annexes_118/all_4_1_chunks.jsonl"),
            "meta": {
                "domain_code": "dlgs118_2011_all_4_1",
                "source_layer": "B",
                "schema_version": "v2",
                "atto_tipo": "D.Lgs.",
                "atto_numero": "118",
                "atto_anno": "2011",
                "titolo": "Allegato 4/1 - Principio contabile applicato della programmazione",
                "allegato": "4/1",
            },
        },
        {
            "collection": "normattiva_dlgs118_2011_all_4_2",
            "mode": "chunked",
            "path": Path("cantiere_118/data/chunks/annexes_118/all_4_2_chunks.jsonl"),
            "meta": {
                "domain_code": "dlgs118_2011_all_4_2",
                "source_layer": "B",
                "schema_version": "v2",
                "atto_tipo": "D.Lgs.",
                "atto_numero": "118",
                "atto_anno": "2011",
                "titolo": "Allegato 4/2 - Principio contabile applicato della contabilità finanziaria",
                "allegato": "4/2",
            },
        },
    ]

    manifest: Dict[str, Any] = {
        "status": "OK",
        "persist_dir": args.persist_dir,
        "embedding_model": args.embedding_model,
        "jobs": [],
    }

    for job in jobs:
        if job["mode"] == "fulltext":
            result = ingest_fulltext_collection(
                client=client,
                embedding_fn=embedding_fn,
                collection_name=job["collection"],
                input_path=job["path"],
                metadata=job["meta"],
                reset_collection=args.reset_collection,
            )
        else:
            result = ingest_chunk_collection(
                client=client,
                embedding_fn=embedding_fn,
                collection_name=job["collection"],
                input_path=job["path"],
                metadata=job["meta"],
                batch_size=args.batch_size,
                reset_collection=args.reset_collection,
            )

        manifest["jobs"].append(result)

    if args.manifest:
        manifest_path = Path(args.manifest)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Ingestione finale D.Lgs. 118/2011 + allegati in ChromaDB.")
    p.add_argument("--persist-dir", default="data/chroma", help="Directory persistente di ChromaDB")
    p.add_argument(
        "--embedding-model",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="Modello di embedding",
    )
    p.add_argument("--batch-size", type=int, default=32, help="Dimensione batch per collection chunked")
    p.add_argument("--reset-collection", action="store_true", help="Elimina prima le collection se esistono")
    p.add_argument(
        "--manifest",
        default="cantiere_118/logs/dlgs118_chroma_manifest.json",
        help="Manifest finale ingestione",
    )
    return p


def main(argv: List[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    try:
        return run_ingest(args)
    except FileNotFoundError as exc:
        eprint(f"Errore: {exc}")
        return 4
    except Exception as exc:
        eprint(f"Errore fatale: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())