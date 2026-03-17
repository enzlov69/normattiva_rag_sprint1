from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

import chromadb
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = Path(__file__).resolve().parent
GENERATED_DIR = TOOLS_DIR / "_generated"
MANIFEST_PATH = GENERATED_DIR / "l241_repair_manifest.json"

COLLECTION_NAME = "normattiva_l241_1990"
DEFAULT_EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_CHROMA_PATH = ROOT / "data" / "chroma"
DEFAULT_EXPORT_PATH = GENERATED_DIR / "l241_1990_export_from_collection.jsonl"

DEFAULT_SOURCE_CANDIDATES = [
    ROOT / "data" / "rag_ready" / "l241_1990_rag_ready.jsonl",
    ROOT / "data" / "rag_ready" / "l241_1990.jsonl",
    ROOT / "data" / "processed" / "l241_1990_rag_ready.jsonl",
    ROOT / "data" / "processed" / "l241" / "l241_1990_rag_ready.jsonl",
    ROOT / "data" / "processed" / "l241_1990.jsonl",
    ROOT / "data" / "normalized" / "l241_1990_rag_ready.jsonl",
    ROOT / "data" / "normalized" / "l241_1990.jsonl",
    DEFAULT_EXPORT_PATH,
]

SMOKE_QUERIES = [
    "annullamento d'ufficio",
    "responsabile del procedimento",
    "motivazione del provvedimento",
]

STRESS_QUERIES = [
    "annullamento d'ufficio",
    "responsabile del procedimento",
    "motivazione del provvedimento",
    "accesso ai documenti amministrativi",
    "conferenza di servizi",
    "silenzio assenso",
    "comunicazione di avvio del procedimento",
    "partecipazione al procedimento amministrativo",
]


def ensure_generated_dir() -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def print_header(title: str) -> None:
    print(f"=== {title} ===")


def get_client(chroma_path: Path | None = None) -> chromadb.PersistentClient:
    resolved = Path(chroma_path) if chroma_path else DEFAULT_CHROMA_PATH
    return chromadb.PersistentClient(path=str(resolved))


def existing_collection_names(client: chromadb.PersistentClient) -> list[str]:
    return sorted(c.name for c in client.list_collections())


def get_collection(
    client: chromadb.PersistentClient,
    collection_name: str = COLLECTION_NAME,
):
    return client.get_collection(name=collection_name)


def safe_peek_ids(collection, limit: int = 3) -> list[str]:
    try:
        payload = collection.peek(limit=limit)
        ids = payload.get("ids", []) if isinstance(payload, dict) else []
        return ids or []
    except Exception:
        return []


def count_collection(collection) -> int:
    try:
        return int(collection.count())
    except Exception:
        return -1


def preview_text(text: str, max_len: int = 180) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= max_len:
        return compact
    return compact[:max_len] + "..."


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest() -> dict[str, Any] | None:
    if not MANIFEST_PATH.exists():
        return None
    return read_json(MANIFEST_PATH)


def save_manifest(payload: dict[str, Any]) -> None:
    ensure_generated_dir()
    write_json(MANIFEST_PATH, payload)


def discover_source_files() -> list[Path]:
    found: list[Path] = []
    seen: set[str] = set()

    for candidate in DEFAULT_SOURCE_CANDIDATES:
        if candidate.exists():
            resolved = str(candidate.resolve())
            if resolved not in seen:
                seen.add(resolved)
                found.append(candidate.resolve())

    recursive_roots = [ROOT / "data", ROOT / "tools"]
    for base in recursive_roots:
        if not base.exists():
            continue
        for file in base.rglob("*.jsonl"):
            lower = file.name.lower()
            if "l241" not in lower and "241_1990" not in lower:
                continue
            resolved = str(file.resolve())
            if resolved not in seen:
                seen.add(resolved)
                found.append(file.resolve())

    return found


def export_collection_to_jsonl(
    chroma_path: Path,
    collection_name: str,
    output_path: Path,
) -> tuple[int, Path]:
    ensure_generated_dir()

    client = get_client(chroma_path)
    collection = get_collection(client, collection_name)

    count = count_collection(collection)
    if count <= 0:
        raise RuntimeError(f"La collection {collection_name} risulta vuota o non leggibile (count={count})")

    payload = collection.get(include=["documents", "metadatas"])

    ids = payload.get("ids", []) or []
    documents = payload.get("documents", []) or []
    metadatas = payload.get("metadatas", []) or []

    if not ids:
        raise RuntimeError(
            f"Export impossibile: collection {collection_name} senza ids leggibili tramite get()."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for idx, rid in enumerate(ids):
            doc = documents[idx] if idx < len(documents) and documents[idx] is not None else ""
            meta = metadatas[idx] if idx < len(metadatas) and metadatas[idx] is not None else {}
            row = {
                "id": rid,
                "document": doc,
                "metadata": meta,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return count, output_path


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except Exception as e:
                raise ValueError(f"JSON non valido in {path} alla riga {lineno}: {e}") from e
            if not isinstance(obj, dict):
                raise ValueError(f"Record non oggetto in {path} alla riga {lineno}")
            yield obj


def _first_non_empty(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize_record(obj: dict[str, Any], seq: int) -> tuple[str, str, dict[str, Any]]:
    rid = _first_non_empty(
        obj.get("id"),
        obj.get("record_id"),
        obj.get("chunk_id"),
        obj.get("doc_id"),
    )

    document = _first_non_empty(
        obj.get("document"),
        obj.get("text"),
        obj.get("content"),
        obj.get("page_content"),
        obj.get("testo"),
        obj.get("testo_unita"),
        obj.get("body"),
    )

    metadata = obj.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    if not document:
        fallback_meta_doc = _first_non_empty(
            metadata.get("text"),
            metadata.get("document"),
            metadata.get("content"),
            metadata.get("testo"),
        )
        document = fallback_meta_doc

    if not rid:
        articolo = _first_non_empty(
            metadata.get("articolo"),
            obj.get("articolo"),
        )
        comma = _first_non_empty(
            metadata.get("comma"),
            obj.get("comma"),
        )
        suffix = f"_art_{articolo}" if articolo else ""
        suffix += f"_com_{comma}" if comma else ""
        rid = f"l241_1990_rec_{seq:04d}{suffix}"

    if not document:
        raise ValueError(f"Record senza document/testo utile al progressivo {seq}")

    if not metadata:
        metadata = {
            k: v
            for k, v in obj.items()
            if k not in {
                "id",
                "record_id",
                "chunk_id",
                "doc_id",
                "document",
                "text",
                "content",
                "page_content",
                "testo",
                "testo_unita",
                "body",
            }
        }

    return rid, document, metadata


def load_records_from_jsonl(path: Path) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for seq, obj in enumerate(iter_jsonl(path), start=1):
        rid, doc, meta = normalize_record(obj, seq=seq)

        if rid in seen_ids:
            raise ValueError(f"ID duplicato nel sorgente: {rid}")

        seen_ids.add(rid)
        ids.append(rid)
        docs.append(doc)
        metas.append(meta if isinstance(meta, dict) else {})

    if not ids:
        raise RuntimeError(f"Nessun record valido trovato nel file {path}")

    return ids, docs, metas


def load_model(model_name: str = DEFAULT_EMBED_MODEL) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def encode_documents(
    model: SentenceTransformer,
    docs: list[str],
) -> list[list[float]]:
    embeddings = model.encode(docs, show_progress_bar=False)
    if hasattr(embeddings, "tolist"):
        return embeddings.tolist()
    return embeddings


def encode_query(
    model: SentenceTransformer,
    query: str,
) -> list[float]:
    embedding = model.encode(query)
    if hasattr(embedding, "tolist"):
        return embedding.tolist()
    return embedding


def chunked(values: list[Any], batch_size: int) -> Iterator[list[Any]]:
    for i in range(0, len(values), batch_size):
        yield values[i:i + batch_size]