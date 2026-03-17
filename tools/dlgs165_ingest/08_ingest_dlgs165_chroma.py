from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parents[2]

INGEST_JOBS_PATH = ROOT / "data" / "manifests" / "dlgs165_2001" / "ingest_jobs.json"
CHROMA_PATH = ROOT / "data" / "chroma"
LOGS_DIR = ROOT / "data" / "logs"

EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
BATCH_SIZE = 64


def load_ingest_jobs() -> dict[str, Any]:
    if not INGEST_JOBS_PATH.exists():
        raise FileNotFoundError(f"Ingest jobs non trovato: {INGEST_JOBS_PATH}")
    return json.loads(INGEST_JOBS_PATH.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def normalize_metadata_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)):
        return value
    if value is None:
        return ""
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def build_metadata(payload: dict[str, Any], collection_id: str, unit_type: str) -> dict[str, Any]:
    fields = [
        "record_id",
        "record_type",
        "norm_unit_id",
        "source_id",
        "unit_type",
        "articolo",
        "comma",
        "lettera",
        "numero",
        "allegato",
        "rubrica",
        "position_index",
        "hierarchy_path",
        "vigenza_ref_id",
        "norm_unit_status",
        "created_at",
        "updated_at",
        "schema_version",
        "record_version",
        "source_layer",
        "trace_id",
        "active_flag",
    ]

    md: dict[str, Any] = {
        "collection_id": collection_id,
        "job_unit_type": unit_type,
    }

    for field in fields:
        if field in payload:
            md[field] = normalize_metadata_value(payload.get(field))

    return md


def load_records_from_dir(input_dir: Path, collection_id: str, unit_type: str) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input path non trovato: {input_dir}")

    json_files = sorted(input_dir.glob("*.json"))
    if not json_files:
        raise RuntimeError(f"Nessun file JSON trovato in: {input_dir}")

    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict[str, Any]] = []

    for jf in json_files:
        payload = json.loads(jf.read_text(encoding="utf-8"))
        record_id = payload.get("record_id")
        testo_unita = payload.get("testo_unita", "")

        if not record_id:
            raise ValueError(f"record_id mancante in {jf}")

        if not testo_unita or not str(testo_unita).strip():
            raise ValueError(f"testo_unita vuoto in {jf}")

        ids.append(str(record_id))
        docs.append(str(testo_unita))
        metas.append(build_metadata(payload, collection_id=collection_id, unit_type=unit_type))

    return ids, docs, metas


def chunked(seq: list[Any], size: int):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def main() -> None:
    payload = load_ingest_jobs()
    jobs = payload.get("jobs", [])

    if not jobs:
        raise SystemExit("[ERRORE] ingest_jobs.json non contiene jobs")

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    print("=== INGEST D.LGS. 165/2001 IN CHROMA ===")
    print(f"Ingest jobs : {rel(INGEST_JOBS_PATH)}")
    print(f"Chroma path : {rel(CHROMA_PATH)}")
    print(f"Model       : {EMBED_MODEL_NAME}")
    print(f"Batch size  : {BATCH_SIZE}")
    print()

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    model = SentenceTransformer(EMBED_MODEL_NAME)

    summary: dict[str, Any] = {
        "dataset_id": payload.get("dataset_id", "dlgs165_2001"),
        "jobs_total": len(jobs),
        "jobs_completed": [],
        "jobs_failed": [],
    }

    for job in jobs:
        job_id = job.get("job_id", "")
        collection_id = job.get("collection_id", "")
        input_path_raw = job.get("input_path", "")
        unit_type = job.get("unit_type", "")
        ingest_mode = job.get("ingest_mode", "")

        input_dir = ROOT / input_path_raw

        print("-" * 100)
        print(f"JOB         : {job_id}")
        print(f"COLLECTION  : {collection_id}")
        print(f"INPUT       : {input_path_raw}")
        print(f"UNIT TYPE   : {unit_type}")
        print(f"INGEST MODE : {ingest_mode}")

        try:
            ids, docs, metas = load_records_from_dir(
                input_dir=input_dir,
                collection_id=collection_id,
                unit_type=unit_type,
            )

            print(f"[OK] record caricati da disco: {len(ids)}")

            if ingest_mode == "full_replace":
                try:
                    client.delete_collection(name=collection_id)
                    print(f"[INFO] collection esistente eliminata: {collection_id}")
                except Exception:
                    print(f"[INFO] collection non preesistente: {collection_id}")

            collection = client.create_collection(name=collection_id)
            print(f"[OK] collection creata: {collection_id}")

            inserted = 0

            for ids_batch, docs_batch, metas_batch in zip(
                chunked(ids, BATCH_SIZE),
                chunked(docs, BATCH_SIZE),
                chunked(metas, BATCH_SIZE),
            ):
                embeddings_batch = model.encode(docs_batch).tolist()

                collection.add(
                    ids=ids_batch,
                    documents=docs_batch,
                    metadatas=metas_batch,
                    embeddings=embeddings_batch,
                )
                inserted += len(ids_batch)
                print(f"[OK] batch ingestito: {inserted}/{len(ids)}")

            summary["jobs_completed"].append(
                {
                    "job_id": job_id,
                    "collection_id": collection_id,
                    "input_path": input_path_raw,
                    "unit_type": unit_type,
                    "records_ingested": inserted,
                    "status": "completed",
                }
            )

        except Exception as e:
            print(f"[ERRORE] job fallito: {e}")
            summary["jobs_failed"].append(
                {
                    "job_id": job_id,
                    "collection_id": collection_id,
                    "input_path": input_path_raw,
                    "unit_type": unit_type,
                    "status": "failed",
                    "error": str(e),
                }
            )

    summary_path = LOGS_DIR / "dlgs165_2001_vigente_ingest_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("=" * 100)
    print(f"[INFO] log riepilogo: {rel(summary_path)}")

    if summary["jobs_failed"]:
        raise SystemExit(f"[ERRORE] ingestione completata con errori. Jobs falliti: {len(summary['jobs_failed'])}")

    print("[OK] ingestione completata con esito positivo")


if __name__ == "__main__":
    main()