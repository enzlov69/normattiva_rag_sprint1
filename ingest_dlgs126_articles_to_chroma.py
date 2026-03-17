#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def norm_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()


def get_embedding_function(model_name: str):
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except Exception as exc:
        raise RuntimeError(
            "Impossibile importare SentenceTransformerEmbeddingFunction. "
            "Verifica di avere installato chromadb e sentence-transformers."
        ) from exc
    return SentenceTransformerEmbeddingFunction(model_name=model_name)


def extract_article_number_from_filename(path: Path) -> str:
    m = re.search(r"art[_\- ]?(\d+)", path.stem, re.IGNORECASE)
    if m:
        return str(int(m.group(1)))
    return ""


def extract_rubrica_and_text(text: str) -> tuple[str, str]:
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    if not lines:
        return "", ""

    rubrica = ""
    body = text.strip()

    if len(lines) >= 2 and lines[0].lower().startswith("art"):
        rubrica = lines[1]
    elif lines:
        rubrica = lines[0]

    return rubrica[:300], body


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingestione articoli D.Lgs. 126/2014 in ChromaDB.")
    parser.add_argument("--articles-dir", default="cantiere_118/data/normalized/articles_126", help="Directory articoli 126")
    parser.add_argument("--persist-dir", default="data/chroma", help="Directory persistente Chroma")
    parser.add_argument("--collection", default="normattiva_dlgs126_2014_articles", help="Nome collection")
    parser.add_argument(
        "--embedding-model",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="Modello embeddings",
    )
    parser.add_argument("--reset-collection", action="store_true", help="Elimina prima la collection se esiste")
    parser.add_argument(
        "--manifest",
        default="cantiere_118/logs/dlgs126_articles_chroma_manifest.json",
        help="Manifest finale",
    )
    args = parser.parse_args(argv)

    try:
        import chromadb
    except Exception as exc:
        eprint("Errore: chromadb non installato o non importabile.")
        eprint(str(exc))
        return 2

    articles_dir = Path(args.articles_dir)
    if not articles_dir.exists():
        eprint(f"Directory non trovata: {articles_dir}")
        return 3

    files = sorted(articles_dir.glob("*.txt"))
    if not files:
        eprint(f"Nessun file .txt trovato in: {articles_dir}")
        return 4

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
            "domain_code": "dlgs126_2014_articles",
            "source_layer": "B",
            "schema_version": "v2",
            "atto_tipo": "Decreto legislativo",
            "atto_numero": "126",
            "atto_anno": "2014",
            "titolo": "Disposizioni integrative e correttive del decreto legislativo 23 giugno 2011, n. 118",
        },
        embedding_function=embedding_fn,
    )

    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    for path in files:
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            continue

        articolo = extract_article_number_from_filename(path)
        rubrica, body = extract_rubrica_and_text(raw)

        doc_id = f"normattiva_dlgs126_2014_articles::art_{articolo.zfill(3) if articolo else path.stem}"

        meta: Dict[str, Any] = {
            "record_type": "ArticleRecord",
            "source_path": str(path),
            "atto_tipo": "Decreto legislativo",
            "atto_numero": "126",
            "atto_anno": "2014",
            "titolo": "Disposizioni integrative e correttive del decreto legislativo 23 giugno 2011, n. 118",
            "articolo": articolo,
            "rubrica": rubrica,
            "citation_text": f"Decreto legislativo n. 126/2014, art. {articolo}" if articolo else "Decreto legislativo n. 126/2014",
        }

        ids.append(doc_id)
        documents.append(body)
        metadatas.append(meta)

    if not ids:
        eprint("Nessun articolo ingestibile trovato.")
        return 5

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    manifest = {
        "status": "OK",
        "collection": args.collection,
        "persist_dir": args.persist_dir,
        "embedding_model": args.embedding_model,
        "articles_ingested": len(ids),
        "collection_count": collection.count(),
        "articles_dir": str(articles_dir),
    }

    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())