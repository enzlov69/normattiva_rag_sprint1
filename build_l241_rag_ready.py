from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SUFFIX_ORDER = {
    "": 0,
    "bis": 1,
    "ter": 2,
    "quater": 3,
    "quinquies": 4,
    "sexies": 5,
    "septies": 6,
    "octies": 7,
    "novies": 8,
    "nonies": 8,
    "decies": 9,
}

EXPECTED_COUNT = 51
SOURCE_ID = "source_norm_241_1990"
CORPUS_DOMAIN_ID = "corpus_l241_1990"
DOMAIN_CODE = "l241_1990"
SCHEMA_VERSION = "2.0"
RECORD_VERSION = 1


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def clean_spaces(value: str) -> str:
    return " ".join((value or "").replace("\xa0", " ").split())


def split_label(label: str) -> tuple[int, str]:
    parts = clean_spaces(label).lower().replace("-", " ").split()
    n = int(parts[0])
    suffix = parts[1] if len(parts) > 1 else ""
    return n, suffix


def sort_tuple(label: str) -> tuple[int, int, str]:
    n, suffix = split_label(label)
    return n, SUFFIX_ORDER.get(suffix, 99), suffix


def load_articles(raw_dir: Path) -> list[dict[str, Any]]:
    articles = []
    for path in sorted(raw_dir.glob("art_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["_file_path"] = str(path)
        articles.append(payload)
    articles.sort(key=lambda x: (
        x.get("ordine_indice", 9999),
        sort_tuple(x.get("article_label_index") or x.get("article_label_heading") or x.get("article_label_slug", "999")),
    ))
    return articles


def build_corpus_domain(created_at: str, count: int, hash_corpus: str) -> dict[str, Any]:
    return {
        "record_id": "corpusdomain_l241_1990",
        "record_type": "CorpusDomain",
        "corpus_domain_id": CORPUS_DOMAIN_ID,
        "domain_code": DOMAIN_CODE,
        "domain_name": "Legge 241/1990",
        "domain_description": "Corpus ufficiale della L. 7 agosto 1990, n. 241 in vista multivigente da Normattiva.",
        "authoritative_scope": "fonte primaria ufficiale",
        "source_priority_order": ["Normattiva"],
        "coverage_scope": f"{count}/{EXPECTED_COUNT} articoli attesi",
        "update_policy": "manual_controlled_refresh",
        "dedup_policy": "hash_plus_article_anchor",
        "corpus_status": "READY" if count == EXPECTED_COUNT else "INCOMPLETE",
        "created_at": created_at,
        "updated_at": created_at,
        "schema_version": SCHEMA_VERSION,
        "record_version": RECORD_VERSION,
        "source_layer": "B",
        "active_flag": True,
        "jurisdiction_scope": "Stato",
        "applicable_entity_scope": "pubbliche amministrazioni",
        "contains_annexes_flag": False,
        "contains_multivigente_flag": True,
        "corpus_hash": hash_corpus,
    }


def build_source_document(articles: list[dict[str, Any]], created_at: str) -> dict[str, Any]:
    first = articles[0]
    corpus_text = "\n\n".join(a.get("testo_plain", "") for a in articles)
    return {
        "record_id": "srcdoc_l241_1990_full",
        "record_type": "SourceDocument",
        "source_id": SOURCE_ID,
        "source_type": "norma",
        "corpus_domain_id": CORPUS_DOMAIN_ID,
        "atto_tipo": first.get("atto_tipo", "Legge"),
        "atto_numero": first.get("atto_numero", "241"),
        "atto_anno": first.get("atto_anno", "1990"),
        "titolo": first.get("titolo"),
        "ente_emittente": first.get("ente_emittente", "Stato"),
        "pubblicazione": first.get("pubblicazione", "Gazzetta Ufficiale"),
        "data_pubblicazione": first.get("data_pubblicazione", "1990-08-18"),
        "uri_ufficiale": first.get("uri_ufficiale") or first.get("uri_ufficiale_articolo"),
        "stato_verifica_fonte": first.get("stato_verifica_fonte", "VERIFIED"),
        "stato_vigenza": first.get("stato_vigenza", "VIGENTE_VERIFICATA"),
        "versione_documento": first.get("versione_documento", "vigente"),
        "hash_contenuto": sha256_text(corpus_text),
        "data_vigenza_inizio": min((a.get("data_vigenza_inizio") for a in articles if a.get("data_vigenza_inizio")), default=None),
        "data_vigenza_fine": None,
        "lingua": "it",
        "dominio_ppav": first.get("dominio_ppav", "procedimento_amministrativo"),
        "authoritative_flag": True,
        "last_verified_at": created_at,
        "human_verified_flag": False,
        "document_status": "VERIFIED",
        "parse_ready_flag": True,
        "index_ready_flag": True,
        "annex_presence_flag": False,
        "multivigente_flag": True,
        "created_at": created_at,
        "updated_at": created_at,
        "schema_version": SCHEMA_VERSION,
        "record_version": RECORD_VERSION,
        "source_layer": "B",
        "trace_id": f"trace_build_l241_{created_at.replace(':','').replace('-','')}",
        "active_flag": True,
        "codice_redazionale": first.get("codice_redazionale"),
        "gazzetta_numero": first.get("gazzetta_numero"),
        "gazzetta_anno": first.get("gazzetta_anno"),
        "effective_text_variant": "multivigente",
        "article_count": len(articles),
    }


def build_norm_unit(article: dict[str, Any], created_at: str) -> dict[str, Any]:
    label = article.get("article_label_heading") or article.get("article_label_index")
    return {
        "record_id": f"normunit_l241_1990_art_{article['article_label_slug']}",
        "record_type": "NormUnit",
        "norm_unit_id": f"l241_1990_art_{article['article_label_slug']}",
        "source_id": SOURCE_ID,
        "unit_type": "articolo",
        "articolo": label,
        "comma": None,
        "lettera": None,
        "numero": None,
        "allegato": None,
        "rubrica": article.get("rubrica_articolo"),
        "testo_unita": article.get("testo_plain"),
        "position_index": article.get("ordine_indice"),
        "hierarchy_path": {
            "atto": f"L. 241/1990",
            "capo": article.get("capo"),
            "capo_rubrica": article.get("capo_rubrica"),
            "articolo": label,
        },
        "cross_reference_ids": [],
        "vigenza_ref_id": f"vigenza_l241_1990_art_{article['article_label_slug']}",
        "norm_unit_status": "PARSED",
        "created_at": created_at,
        "updated_at": created_at,
        "schema_version": SCHEMA_VERSION,
        "record_version": RECORD_VERSION,
        "source_layer": "B",
        "trace_id": article.get("trace_id"),
        "active_flag": True,
        "source_record_ref": article.get("record_id"),
        "uri_ufficiale": article.get("uri_ufficiale_articolo"),
        "stato_vigenza": article.get("stato_vigenza"),
        "hash_contenuto": article.get("hash_contenuto"),
    }


def build_chunk_record(article: dict[str, Any], created_at: str) -> dict[str, Any]:
    text = article.get("testo_plain", "")
    return {
        "record_id": f"chunkrec_l241_1990_art_{article['article_label_slug']}_001",
        "record_type": "ChunkRecord",
        "chunk_id": f"l241_1990_art_{article['article_label_slug']}_001",
        "source_id": SOURCE_ID,
        "norm_unit_id": f"l241_1990_art_{article['article_label_slug']}",
        "chunk_text": text,
        "chunk_sequence": 1,
        "chunk_context_before": clean_spaces(article.get("capo_rubrica") or ""),
        "chunk_context_after": clean_spaces(article.get("rubrica_articolo") or ""),
        "embedding_vector_ref": None,
        "lexical_index_ref": None,
        "quality_flag": "GOOD" if text else "LOW",
        "parse_confidence": 0.99 if text else 0.0,
        "retrievable_flag": bool(text),
        "orphan_flag": False,
        "chunk_status": "READY" if text else "EMPTY",
        "created_at": created_at,
        "updated_at": created_at,
        "schema_version": SCHEMA_VERSION,
        "record_version": RECORD_VERSION,
        "source_layer": "B",
        "trace_id": article.get("trace_id"),
        "active_flag": True,
        "uri_ufficiale": article.get("uri_ufficiale_articolo"),
        "article_label": article.get("article_label_heading") or article.get("article_label_index"),
    }


def build_vigenza_record(article: dict[str, Any], created_at: str) -> dict[str, Any]:
    return {
        "record_id": f"vigenzarec_l241_1990_art_{article['article_label_slug']}",
        "record_type": "VigenzaRecord",
        "vigenza_id": f"vigenza_l241_1990_art_{article['article_label_slug']}",
        "source_id": SOURCE_ID,
        "norm_unit_id": f"l241_1990_art_{article['article_label_slug']}",
        "vigore_status": article.get("stato_vigenza", "VIGENTE_VERIFICATA"),
        "vigore_start_date": article.get("data_vigenza_inizio"),
        "vigore_end_date": article.get("data_vigenza_fine"),
        "vigore_basis": "Normattiva multivigente",
        "verification_method": "source_page_label",
        "verification_confidence": 0.9,
        "essential_point_flag": False,
        "block_if_uncertain_flag": True,
        "created_at": created_at,
        "updated_at": created_at,
        "schema_version": SCHEMA_VERSION,
        "record_version": RECORD_VERSION,
        "source_layer": "B",
        "trace_id": article.get("trace_id"),
        "active_flag": True,
    }


def build_citation_record(article: dict[str, Any], created_at: str) -> dict[str, Any]:
    citation_text = f"{article.get('atto_tipo', 'Legge')} {article.get('atto_numero', '241')}/{article.get('atto_anno', '1990')}, art. {article.get('article_label_heading') or article.get('article_label_index')}"
    return {
        "record_id": f"citationrec_l241_1990_art_{article['article_label_slug']}",
        "record_type": "CitationRecord",
        "citation_id": f"citation_l241_1990_art_{article['article_label_slug']}",
        "source_id": SOURCE_ID,
        "atto_tipo": article.get("atto_tipo", "Legge"),
        "atto_numero": article.get("atto_numero", "241"),
        "atto_anno": article.get("atto_anno", "1990"),
        "articolo": article.get("article_label_heading") or article.get("article_label_index"),
        "comma": None,
        "allegato": None,
        "uri_ufficiale": article.get("uri_ufficiale_articolo"),
        "stato_vigenza": article.get("stato_vigenza", "VIGENTE_VERIFICATA"),
        "citation_text": citation_text,
        "citation_status": "VALID",
        "case_id": None,
        "norm_unit_id": f"l241_1990_art_{article['article_label_slug']}",
        "chunk_id": f"l241_1990_art_{article['article_label_slug']}_001",
        "quote_span": None,
        "source_authority_flag": True,
        "reconstructible_flag": True,
        "opponibile_flag": True,
        "validation_errors": [],
        "block_refs": [],
        "created_at": created_at,
        "updated_at": created_at,
        "schema_version": SCHEMA_VERSION,
        "record_version": RECORD_VERSION,
        "source_layer": "B",
        "trace_id": article.get("trace_id"),
        "active_flag": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build rag_ready files for L. 241/1990 from raw article JSONs.")
    parser.add_argument("--raw-dir", default="data/raw/l241_1990/articles", help="Directory containing raw article JSON files")
    parser.add_argument("--output-dir", default="data/processed/l241", help="Output directory for rag_ready files")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not raw_dir.exists():
        raise SystemExit(f"Directory raw non trovata: {raw_dir}")

    articles = load_articles(raw_dir)
    if not articles:
        raise SystemExit("Nessun articolo JSON trovato nel raw-dir.")

    created_at = now_iso()
    corpus_hash = sha256_text("\n".join(a.get("hash_contenuto", "") for a in articles))

    corpus_domain = build_corpus_domain(created_at, len(articles), corpus_hash)
    source_document = build_source_document(articles, created_at)
    norm_units = [build_norm_unit(a, created_at) for a in articles]
    chunk_records = [build_chunk_record(a, created_at) for a in articles]
    vigenza_records = [build_vigenza_record(a, created_at) for a in articles]
    citation_records = [build_citation_record(a, created_at) for a in articles]

    ready = {
        "build_meta": {
            "generated_at": created_at,
            "source_raw_dir": str(raw_dir),
            "schema_version": SCHEMA_VERSION,
            "record_version": RECORD_VERSION,
            "domain_code": DOMAIN_CODE,
            "expected_articles": EXPECTED_COUNT,
            "actual_articles": len(articles),
            "status": "READY" if len(articles) == EXPECTED_COUNT else "INCOMPLETE",
        },
        "corpus_domain": corpus_domain,
        "source_document": source_document,
        "norm_units": norm_units,
        "chunk_records": chunk_records,
        "vigenza_records": vigenza_records,
        "citation_records": citation_records,
    }

    json_path = output_dir / "l241_rag_ready.json"
    ndjson_path = output_dir / "l241_rag_ready.ndjson"
    manifest_path = output_dir / "l241_build_manifest.json"

    json_path.write_text(json.dumps(ready, ensure_ascii=False, indent=2), encoding="utf-8")

    with ndjson_path.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(corpus_domain, ensure_ascii=False) + "\n")
        fh.write(json.dumps(source_document, ensure_ascii=False) + "\n")
        for rec in norm_units:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        for rec in chunk_records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        for rec in vigenza_records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        for rec in citation_records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    manifest = {
        "generated_at": created_at,
        "input_raw_dir": str(raw_dir),
        "output_json": str(json_path),
        "output_ndjson": str(ndjson_path),
        "domain_code": DOMAIN_CODE,
        "source_id": SOURCE_ID,
        "counts": {
            "articles": len(articles),
            "norm_units": len(norm_units),
            "chunk_records": len(chunk_records),
            "vigenza_records": len(vigenza_records),
            "citation_records": len(citation_records),
        },
        "status": "READY" if len(articles) == EXPECTED_COUNT else "INCOMPLETE",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
