#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


@dataclass
class BuildIndex:
    source_document: Dict[str, Any]
    norm_units: Dict[str, Dict[str, Any]]
    chunks: List[Dict[str, Any]]


def load_records_from_ndjson(ndjson_path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with ndjson_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"NDJSON non valido alla riga {line_no}: {exc}") from exc
    return records


def load_records_from_json(json_path: Path) -> List[Dict[str, Any]]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "records" in data and isinstance(data["records"], list):
            return data["records"]
        return [data]
    raise ValueError("JSON non riconosciuto: atteso oggetto o lista di record")


def load_records(input_path: Path) -> List[Dict[str, Any]]:
    if not input_path.exists():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    if input_path.suffix.lower() == ".ndjson":
        return load_records_from_ndjson(input_path)
    if input_path.suffix.lower() == ".json":
        return load_records_from_json(input_path)
    raise ValueError("Formato input non supportato: usare .ndjson oppure .json")


def build_index(records: Iterable[Dict[str, Any]]) -> BuildIndex:
    source_document: Optional[Dict[str, Any]] = None
    norm_units: Dict[str, Dict[str, Any]] = {}
    chunks: List[Dict[str, Any]] = []

    for rec in records:
        rtype = rec.get("record_type")
        if rtype == "SourceDocument":
            source_document = rec
        elif rtype == "NormUnit":
            norm_unit_id = rec.get("norm_unit_id")
            if norm_unit_id:
                norm_units[norm_unit_id] = rec
        elif rtype == "ChunkRecord":
            chunks.append(rec)

    if source_document is None:
        raise ValueError("SourceDocument assente nel file rag_ready")
    if not chunks:
        raise ValueError("ChunkRecord assenti nel file rag_ready")

    return BuildIndex(source_document=source_document, norm_units=norm_units, chunks=chunks)


def norm_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()


def make_chunk_metadata(chunk: Dict[str, Any], norm_unit: Dict[str, Any], source_document: Dict[str, Any]) -> Dict[str, Any]:
    articolo = norm_str(norm_unit.get("articolo"))
    comma = norm_str(norm_unit.get("comma"))
    rubrica = norm_str(norm_unit.get("rubrica"))
    hierarchy_path = norm_str(norm_unit.get("hierarchy_path"))
    uri_ufficiale = norm_str(source_document.get("uri_ufficiale"))

    metadata: Dict[str, Any] = {
        "domain_code": "l241_1990",
        "source_id": norm_str(chunk.get("source_id")),
        "norm_unit_id": norm_str(chunk.get("norm_unit_id")),
        "chunk_id": norm_str(chunk.get("chunk_id")),
        "record_type": "ChunkRecord",
        "atto_tipo": norm_str(source_document.get("atto_tipo")),
        "atto_numero": norm_str(source_document.get("atto_numero")),
        "atto_anno": norm_str(source_document.get("atto_anno")),
        "titolo": norm_str(source_document.get("titolo")),
        "uri_ufficiale": uri_ufficiale,
        "stato_vigenza": norm_str(source_document.get("stato_vigenza")),
        "articolo": articolo,
        "comma": comma,
        "rubrica": rubrica,
        "hierarchy_path": hierarchy_path,
        "chunk_sequence": int(chunk.get("chunk_sequence", 0) or 0),
        "retrievable_flag": bool(chunk.get("retrievable_flag", False)),
        "orphan_flag": bool(chunk.get("orphan_flag", False)),
        "quality_flag": norm_str(chunk.get("quality_flag")),
        "parse_confidence": float(chunk.get("parse_confidence", 0.0) or 0.0),
        "trace_id": norm_str(chunk.get("trace_id")),
    }

    citation = f"{metadata['atto_tipo']} n. {metadata['atto_numero']}/{metadata['atto_anno']}"
    if articolo:
        citation += f", art. {articolo}"
    if comma:
        citation += f", comma {comma}"
    metadata["citation_text"] = citation

    # Chroma metadata ammette scalari semplici.
    return metadata


def batched(items: List[Any], batch_size: int) -> Iterable[List[Any]]:
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def get_embedding_function(model_name: str):
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Impossibile importare SentenceTransformerEmbeddingFunction. "
            "Verifica di avere installato chromadb e sentence-transformers."
        ) from exc

    return SentenceTransformerEmbeddingFunction(model_name=model_name)


def ingest(args: argparse.Namespace) -> int:
    try:
        import chromadb
    except Exception as exc:  # pragma: no cover
        eprint("Errore: chromadb non installato o non importabile.")
        eprint(str(exc))
        return 2

    records = load_records(Path(args.input))
    idx = build_index(records)

    client = chromadb.PersistentClient(path=args.persist_dir)
    embedding_fn = get_embedding_function(args.embedding_model)

    if args.reset_collection:
        try:
            client.delete_collection(args.collection)
            print(f"Collection eliminata: {args.collection}")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=args.collection,
        metadata={
            "domain_code": "l241_1990",
            "source_layer": "B",
            "schema_version": "v2",
            "source_document_id": norm_str(idx.source_document.get("record_id")),
            "atto_tipo": norm_str(idx.source_document.get("atto_tipo")),
            "atto_numero": norm_str(idx.source_document.get("atto_numero")),
            "atto_anno": norm_str(idx.source_document.get("atto_anno")),
        },
        embedding_function=embedding_fn,
    )

    chunk_records: List[Tuple[str, str, Dict[str, Any]]] = []
    skipped: List[str] = []

    for chunk in idx.chunks:
        if not chunk.get("retrievable_flag", True):
            skipped.append(norm_str(chunk.get("chunk_id")))
            continue
        if chunk.get("orphan_flag", False):
            skipped.append(norm_str(chunk.get("chunk_id")))
            continue
        chunk_text = norm_str(chunk.get("chunk_text"))
        if not chunk_text:
            skipped.append(norm_str(chunk.get("chunk_id")))
            continue
        norm_unit_id = norm_str(chunk.get("norm_unit_id"))
        norm_unit = idx.norm_units.get(norm_unit_id)
        if not norm_unit:
            skipped.append(norm_str(chunk.get("chunk_id")))
            continue
        metadata = make_chunk_metadata(chunk, norm_unit, idx.source_document)
        chunk_id = norm_str(chunk.get("chunk_id")) or norm_str(chunk.get("record_id"))
        if not chunk_id:
            skipped.append("<missing_chunk_id>")
            continue
        chunk_records.append((chunk_id, chunk_text, metadata))

    if not chunk_records:
        eprint("Nessun ChunkRecord ingestibile trovato.")
        return 3

    total = len(chunk_records)
    for batch_no, batch in enumerate(batched(chunk_records, args.batch_size), start=1):
        ids = [x[0] for x in batch]
        docs = [x[1] for x in batch]
        metas = [x[2] for x in batch]

        if args.upsert:
            collection.upsert(ids=ids, documents=docs, metadatas=metas)
        else:
            # add fallisce su ID duplicati: utile se si vuole evitare sovrascritture silenziose.
            collection.add(ids=ids, documents=docs, metadatas=metas)

        print(f"Batch {batch_no}: ingestiti {len(batch)} chunk")

    collection_count = collection.count()
    manifest = {
        "status": "OK",
        "collection": args.collection,
        "persist_dir": args.persist_dir,
        "embedding_model": args.embedding_model,
        "ingested_chunks": total,
        "collection_count": collection_count,
        "skipped_chunks": len(skipped),
        "source_document": {
            "atto_tipo": norm_str(idx.source_document.get("atto_tipo")),
            "atto_numero": norm_str(idx.source_document.get("atto_numero")),
            "atto_anno": norm_str(idx.source_document.get("atto_anno")),
            "titolo": norm_str(idx.source_document.get("titolo")),
            "uri_ufficiale": norm_str(idx.source_document.get("uri_ufficiale")),
        },
    }

    if args.manifest:
        Path(args.manifest).parent.mkdir(parents=True, exist_ok=True)
        Path(args.manifest).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))

    if args.test_query:
        print("\n=== TEST QUERY ===")
        for q in args.test_query:
            result = collection.query(
                query_texts=[q],
                n_results=args.top_k,
                include=["documents", "metadatas", "distances"],
            )
            print_query_result(q, result)

    return 0


def print_query_result(query: str, result: Dict[str, Any]) -> None:
    print(f"\nQuery: {query}")
    ids = (result.get("ids") or [[]])[0]
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    if not ids:
        print("  Nessun risultato")
        return

    for idx, chunk_id in enumerate(ids, start=1):
        meta = metas[idx - 1] or {}
        doc = docs[idx - 1] or ""
        dist = distances[idx - 1] if idx - 1 < len(distances) else None
        articolo = meta.get("articolo", "")
        rubrica = meta.get("rubrica", "")
        citation = meta.get("citation_text", "")
        uri = meta.get("uri_ufficiale", "")
        excerpt = doc.replace("\n", " ").strip()
        excerpt = excerpt[:300] + ("..." if len(excerpt) > 300 else "")
        print(f"  [{idx}] chunk_id={chunk_id}")
        print(f"      citazione={citation}")
        print(f"      rubrica={rubrica}")
        print(f"      distanza={dist}")
        if uri:
            print(f"      uri={uri}")
        print(f"      testo={excerpt}")


def query(args: argparse.Namespace) -> int:
    try:
        import chromadb
    except Exception as exc:  # pragma: no cover
        eprint("Errore: chromadb non installato o non importabile.")
        eprint(str(exc))
        return 2

    client = chromadb.PersistentClient(path=args.persist_dir)
    embedding_fn = get_embedding_function(args.embedding_model)
    collection = client.get_collection(name=args.collection, embedding_function=embedding_fn)

    result = collection.query(
        query_texts=[args.query_text],
        n_results=args.top_k,
        include=["documents", "metadatas", "distances"],
    )
    print_query_result(args.query_text, result)
    return 0


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Ingestione ChromaDB della L. 241/1990 in collection separata, con query test opzionali."
    )
    sub = p.add_subparsers(dest="command", required=False)

    ingest_p = sub.add_parser("ingest", help="Ingesta il file rag_ready nella collection ChromaDB")
    ingest_p.add_argument(
        "--input",
        default="data/processed/l241/l241_rag_ready.ndjson",
        help="Percorso al file rag_ready (.ndjson consigliato)",
    )
    ingest_p.add_argument(
        "--persist-dir",
        default="data/chroma",
        help="Directory persistente di ChromaDB",
    )
    ingest_p.add_argument(
        "--collection",
        default="normattiva_l241_1990",
        help="Nome collection ChromaDB dedicata alla L. 241/1990",
    )
    ingest_p.add_argument(
        "--embedding-model",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="Modello di embedding da usare in ChromaDB",
    )
    ingest_p.add_argument("--batch-size", type=int, default=32, help="Dimensione batch di ingestione")
    ingest_p.add_argument("--upsert", action="store_true", help="Usa upsert invece di add")
    ingest_p.add_argument(
        "--reset-collection",
        action="store_true",
        help="Elimina prima la collection se già esiste",
    )
    ingest_p.add_argument(
        "--manifest",
        default="data/processed/l241/l241_chroma_manifest.json",
        help="Manifest finale di ingestione",
    )
    ingest_p.add_argument(
        "--test-query",
        action="append",
        help="Query di test da eseguire subito dopo l'ingestione (ripetibile)",
    )
    ingest_p.add_argument("--top-k", type=int, default=5, help="Numero risultati per query di test")
    ingest_p.set_defaults(func=ingest)

    query_p = sub.add_parser("query", help="Interroga una collection già esistente")
    query_p.add_argument("--persist-dir", default="data/chroma", help="Directory persistente di ChromaDB")
    query_p.add_argument(
        "--collection",
        default="normattiva_l241_1990",
        help="Nome collection ChromaDB dedicata alla L. 241/1990",
    )
    query_p.add_argument(
        "--embedding-model",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="Modello di embedding da usare in ChromaDB",
    )
    query_p.add_argument("--query-text", required=True, help="Testo query")
    query_p.add_argument("--top-k", type=int, default=5, help="Numero risultati")
    query_p.set_defaults(func=query)

    # Compatibilità: se l'utente lancia lo script senza subcommand, trattiamo come ingest.
    p.set_defaults(func=None)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    if args.func is None:
        # fallback su ingest per uso rapido
        fallback_args = ["ingest"] + (argv or sys.argv[1:])
        args = parser.parse_args(fallback_args)

    try:
        return int(args.func(args))
    except FileNotFoundError as exc:
        eprint(f"Errore: {exc}")
        return 4
    except Exception as exc:
        eprint(f"Errore fatale: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
