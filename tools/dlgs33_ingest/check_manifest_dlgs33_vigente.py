from __future__ import annotations

import argparse
from datetime import datetime, UTC
from pathlib import Path

from dlgs33_ingest_utils import (
    DEFAULT_ARTICLES_DIR,
    DEFAULT_COLLECTION_ARTICLES,
    DEFAULT_COLLECTION_COMMI,
    DEFAULT_COMMI_DIR,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_PERSIST_DIR,
    EXPECTED_ARTICLES,
    EXPECTED_COMMI,
    save_json,
    summarize_folder,
)


def build_manifest(articles_dir: Path, commi_dir: Path, persist_dir: str) -> tuple[dict, bool]:
    article_summary = summarize_folder(articles_dir)
    commi_summary = summarize_folder(commi_dir)

    ready = True
    blockers: list[str] = []

    if article_summary["files"] != EXPECTED_ARTICLES:
        ready = False
        blockers.append(
            f"Conteggio articoli non coerente: attesi {EXPECTED_ARTICLES}, trovati {article_summary['files']}"
        )
    if commi_summary["files"] != EXPECTED_COMMI:
        ready = False
        blockers.append(
            f"Conteggio commi non coerente: attesi {EXPECTED_COMMI}, trovati {commi_summary['files']}"
        )
    if article_summary["missing_text"] > 0:
        ready = False
        blockers.append(f"Articoli con testo mancante: {article_summary['missing_text']}")
    if commi_summary["missing_text"] > 0:
        ready = False
        blockers.append(f"Commi con testo mancante: {commi_summary['missing_text']}")

    manifest = {
        "manifest_id": "dlgs33_2013_vigente_ingest_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "atto": {
            "tipo": "Decreto legislativo",
            "numero": "33",
            "anno": "2013",
            "titolo": (
                "Riordino della disciplina riguardante il diritto di accesso civico e gli obblighi di "
                "pubblicità, trasparenza e diffusione di informazioni da parte delle pubbliche amministrazioni"
            ),
        },
        "source": {
            "fonte_ufficiale": "Normattiva",
            "stato_vigenza": "vigente",
            "uri_ufficiale": "https://www.normattiva.it/",
        },
        "input": {
            "articles_dir": str(articles_dir).replace("\\", "/"),
            "commi_dir": str(commi_dir).replace("\\", "/"),
        },
        "expected_counts": {
            "articles": EXPECTED_ARTICLES,
            "commi": EXPECTED_COMMI,
        },
        "actual_counts": {
            "articles": article_summary["files"],
            "commi": commi_summary["files"],
        },
        "quality": {
            "articles_missing_text": article_summary["missing_text"],
            "articles_missing_uri": article_summary["missing_uri"],
            "commi_missing_text": commi_summary["missing_text"],
            "commi_missing_uri": commi_summary["missing_uri"],
        },
        "collections": {
            "articles": DEFAULT_COLLECTION_ARTICLES,
            "commi": DEFAULT_COLLECTION_COMMI,
        },
        "vectorstore": {
            "persist_dir": persist_dir.replace("\\", "/"),
            "embedding_model": DEFAULT_EMBEDDING_MODEL,
        },
        "status": "READY" if ready else "BLOCKED",
        "blockers": blockers,
        "samples": {
            "articles": article_summary["sample_ids"],
            "commi": commi_summary["sample_ids"],
        },
    }
    return manifest, ready


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica finale manifest ingestione D.Lgs. 33/2013 vigente")
    parser.add_argument("--articles-dir", default=DEFAULT_ARTICLES_DIR)
    parser.add_argument("--commi-dir", default=DEFAULT_COMMI_DIR)
    parser.add_argument("--persist-dir", default=DEFAULT_PERSIST_DIR)
    parser.add_argument("--manifest-path", default=DEFAULT_MANIFEST_PATH)
    args = parser.parse_args()

    articles_dir = Path(args.articles_dir)
    commi_dir = Path(args.commi_dir)
    manifest_path = Path(args.manifest_path)

    manifest, ready = build_manifest(articles_dir, commi_dir, args.persist_dir)
    save_json(manifest_path, manifest)

    print("=== CHECK MANIFEST D.LGS. 33/2013 VIGENTE ===")
    print(f"Manifest: {manifest_path}")
    print(f"Articoli attesi/trovati: {EXPECTED_ARTICLES}/{manifest['actual_counts']['articles']}")
    print(f"Commi attesi/trovati: {EXPECTED_COMMI}/{manifest['actual_counts']['commi']}")
    print(f"Status: {manifest['status']}")
    if manifest["blockers"]:
        print("Blocchi:")
        for block in manifest["blockers"]:
            print(f"- {block}")
        return 1
    print("Manifest verificato. Pronto per ingestione.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
