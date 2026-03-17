from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = BASE_DIR / "src" / "tools" / "normattiva_bootstrap_config.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def main() -> None:
    cfg = load_config()
    manifests_dir = BASE_DIR / cfg["manifests_dir"]
    manifests_dir.mkdir(parents=True, exist_ok=True)

    dataset_id = cfg["dataset_id"]
    version = cfg["versione"]

    sources_manifest = {
        "manifest_type": "sources_manifest",
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "dataset_title": f"{cfg['atto_tipo']} {cfg['atto_numero']}/{cfg['atto_anno']} - Corpus {version}",
        "sources": [
            {
                "source_id": f"normattiva_{dataset_id}_{version}_html",
                "source_type": "html",
                "authority": "Normattiva",
                "title": f"{cfg['atto_tipo']} {cfg['atto_numero']}/{cfg['atto_anno']} - testo {version}",
                "local_path": cfg["raw_html_path"],
                "status": "active",
                "role": "primary_source"
            },
            {
                "source_id": f"normattiva_{dataset_id}_{version}_articles",
                "source_type": "norm_units_json",
                "authority": "Normattiva / pipeline interna",
                "title": f"{cfg['atto_tipo']} {cfg['atto_numero']}/{cfg['atto_anno']} - articoli {version}",
                "local_path": cfg["articles_out_dir"],
                "status": "active",
                "role": "structured_articles"
            },
            {
                "source_id": f"normattiva_{dataset_id}_{version}_commi",
                "source_type": "norm_units_json",
                "authority": "Normattiva / pipeline interna",
                "title": f"{cfg['atto_tipo']} {cfg['atto_numero']}/{cfg['atto_anno']} - commi {version}",
                "local_path": cfg["commi_out_dir"],
                "status": "active",
                "role": "structured_commi"
            }
        ]
    }

    collections_manifest = {
        "manifest_type": "collections_manifest",
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "collections": [
            {
                "collection_id": f"normattiva_{dataset_id}_{version}_articles",
                "collection_type": "normative_articles",
                "source_path": cfg["articles_out_dir"],
                "record_type": "NormUnit",
                "unit_type": "articolo",
                "status": "ready_for_ingestion",
                "priority": "high"
            },
            {
                "collection_id": f"normattiva_{dataset_id}_{version}_commi",
                "collection_type": "normative_commi",
                "source_path": cfg["commi_out_dir"],
                "record_type": "NormUnit",
                "unit_type": "comma",
                "status": "ready_for_ingestion",
                "priority": "high"
            }
        ]
    }

    ingest_jobs = {
        "manifest_type": "ingest_jobs",
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "jobs": [
            {
                "job_id": f"ingest_normattiva_{dataset_id}_{version}_articles",
                "collection_id": f"normattiva_{dataset_id}_{version}_articles",
                "input_path": cfg["articles_out_dir"],
                "record_type": "NormUnit",
                "unit_type": "articolo",
                "ingest_mode": "full_replace",
                "status": "planned"
            },
            {
                "job_id": f"ingest_normattiva_{dataset_id}_{version}_commi",
                "collection_id": f"normattiva_{dataset_id}_{version}_commi",
                "input_path": cfg["commi_out_dir"],
                "record_type": "NormUnit",
                "unit_type": "comma",
                "ingest_mode": "full_replace",
                "status": "planned"
            }
        ]
    }

    (manifests_dir / "sources_manifest.json").write_text(json.dumps(sources_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (manifests_dir / "collections_manifest.json").write_text(json.dumps(collections_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (manifests_dir / "ingest_jobs.json").write_text(json.dumps(ingest_jobs, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] manifests generati in: {manifests_dir}")


if __name__ == "__main__":
    main()
