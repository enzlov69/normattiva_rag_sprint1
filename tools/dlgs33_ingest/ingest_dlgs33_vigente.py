from __future__ import annotations

import argparse
from datetime import datetime, UTC
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from dlgs33_ingest_utils import (
    DEFAULT_MANIFEST_PATH,
    iter_json_files,
    load_json,
    load_manifest_info,
    normalize_record,
    save_json,
)


def prepare_payload(folder: Path, source_kind: str) -> tuple[list[str], list[str], list[dict]]:
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for path in iter_json_files(folder):
        raw = load_json(path)
        item_id, document, metadata = normalize_record(raw, source_kind=source_kind, fallback_id=path.stem)
        ids.append(item_id)
        documents.append(document)
        metadatas.append(metadata)

    return ids, documents, metadatas


def recreate_collection(client: chromadb.PersistentClient, name: str, embedding_function):
    try:
        client.delete_collection(name)
    except Exception:
        pass
    return client.get_or_create_collection(
        name=name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )


def get_collection(client: chromadb.PersistentClient, name: str, embedding_function, reset: bool):
    if reset:
        return recreate_collection(client, name, embedding_function)
    return client.get_or_create_collection(
        name=name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )


def ingest_collection(collection, ids: list[str], documents: list[str], metadatas: list[dict], batch_size: int) -> int:
    inserted = 0
    total = len(ids)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )
        inserted += end - start
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingestione D.Lgs. 33/2013 vigente nel vector store")
    parser.add_argument("--manifest-path", default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--persist-dir", default=None)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    manifest, info = load_manifest_info(args.manifest_path)
    if manifest.get("status") != "READY":
        print("Manifest non pronto. Eseguire prima check_manifest_dlgs33_vigente.py")
        return 1

    persist_dir = Path(args.persist_dir) if args.persist_dir else info.persist_dir
    persist_dir.mkdir(parents=True, exist_ok=True)

    embedding_function = SentenceTransformerEmbeddingFunction(model_name=info.embedding_model)
    client = chromadb.PersistentClient(path=str(persist_dir))

    print("=== INGESTIONE D.LGS. 33/2013 VIGENTE ===")
    print(f"Persist dir: {persist_dir}")
    print(f"Embedding model: {info.embedding_model}")

    article_ids, article_documents, article_metadatas = prepare_payload(info.articles_dir, "articles")
    commi_ids, commi_documents, commi_metadatas = prepare_payload(info.commi_dir, "commi")

    article_collection = get_collection(client, info.collection_articles, embedding_function, args.reset)
    commi_collection = get_collection(client, info.collection_commi, embedding_function, args.reset)

    inserted_articles = ingest_collection(
        article_collection,
        article_ids,
        article_documents,
        article_metadatas,
        args.batch_size,
    )
    inserted_commi = ingest_collection(
        commi_collection,
        commi_ids,
        commi_documents,
        commi_metadatas,
        args.batch_size,
    )

    report = {
        "report_id": "dlgs33_2013_vigente_ingest_report_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "manifest_id": manifest.get("manifest_id"),
        "persist_dir": str(persist_dir).replace("\\", "/"),
        "embedding_model": info.embedding_model,
        "collections": {
            "articles": {
                "name": info.collection_articles,
                "inserted": inserted_articles,
                "count_after_ingest": article_collection.count(),
            },
            "commi": {
                "name": info.collection_commi,
                "inserted": inserted_commi,
                "count_after_ingest": commi_collection.count(),
            },
        },
        "status": "SUCCESS",
    }

    log_path = Path("data/logs/dlgs33_2013_vigente_ingest_report.json")
    save_json(log_path, report)

    print(f"Collection articoli: {info.collection_articles} -> {article_collection.count()}")
    print(f"Collection commi: {info.collection_commi} -> {commi_collection.count()}")
    print(f"Report: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
