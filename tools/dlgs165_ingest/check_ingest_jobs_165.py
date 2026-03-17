from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INGEST_JOBS_PATH = ROOT / "data" / "manifests" / "dlgs165_2001" / "ingest_jobs.json"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> None:
    if not INGEST_JOBS_PATH.exists():
        raise FileNotFoundError(f"Ingest jobs non trovato: {INGEST_JOBS_PATH}")

    payload = json.loads(INGEST_JOBS_PATH.read_text(encoding="utf-8"))
    jobs = payload.get("jobs", [])

    print("=== CHECK INGEST JOBS 165 ===")
    print(f"Jobs: {len(jobs)}")

    if not jobs:
        raise SystemExit("[ERRORE] Nessun job presente in ingest_jobs.json")

    errors = 0

    for job in jobs:
        collection_id = job.get("collection_id", "")
        input_path_raw = job.get("input_path", "")
        ingest_mode = job.get("ingest_mode", "")
        unit_type = job.get("unit_type", "")

        input_path = ROOT / input_path_raw

        print(f"- {collection_id} ({unit_type})")
        print(f"  ingest_mode: {ingest_mode}")

        if not input_path.exists():
            print(f"  [ERRORE] input path non trovato: {input_path_raw}")
            errors += 1
            continue

        json_files = sorted(input_path.glob("*.json"))
        print(f"  [OK] input: {input_path_raw}")
        print(f"  [OK] file json trovati: {len(json_files)}")

        if len(json_files) == 0:
            print("  [ERRORE] directory vuota")
            errors += 1

    if errors:
        raise SystemExit(f"[ERRORE] check ingest jobs fallito. Errori: {errors}")

    print("[OK] check ingest jobs completato con esito positivo")


if __name__ == "__main__":
    main()