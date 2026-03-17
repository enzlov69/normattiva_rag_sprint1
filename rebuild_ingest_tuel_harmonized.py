#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCHEMA_VERSION = "2.0"
RECORD_VERSION = 1
DEFAULT_DOMAIN_CODE = "tuel_267_2000"
DEFAULT_COLLECTION = "normattiva_tuel_267_2000"
DEFAULT_EXPECTED_COUNT = 294
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


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_spaces(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\xa0", " ").split())


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def first_nonempty(*values: Any) -> Optional[str]:
    for v in values:
        s = clean_spaces(v)
        if s:
            return s
    return None


def parse_article_label(value: Any) -> str:
    raw = clean_spaces(value)
    if not raw:
        return ""
    lowered = raw.lower().replace("articolo", "").replace("art.", "").strip()
    lowered = lowered.replace("-", " ")
    parts = lowered.split()
    if not parts:
        return raw
    if parts[0].isdigit():
        if len(parts) > 1 and parts[1] in SUFFIX_ORDER:
            return f"{int(parts[0])}-{parts[1]}"
        return str(int(parts[0]))
    return raw


def article_slug(label: str) -> str:
    label = clean_spaces(label).lower()
    label = label.replace("articolo", "").replace("art.", "").strip()
    label = label.replace("-", "_").replace(" ", "_")
    return label


def sort_tuple(label: str) -> Tuple[int, int, str]:
    raw = clean_spaces(label).lower().replace("-", " ")
    parts = raw.split()
    if not parts:
        return (9999, 99, "")
    try:
        n = int(parts[0])
    except Exception:
        return (9999, 99, raw)
    suffix = parts[1] if len(parts) > 1 else ""
    return (n, SUFFIX_ORDER.get(suffix, 99), suffix)


def stringify_hierarchy_path(path_obj: Any) -> str:
    if isinstance(path_obj, dict):
        pieces = []
        for k in ("titolo", "parte", "libro", "titolo_interno", "capo", "capo_rubrica", "articolo"):
            v = clean_spaces(path_obj.get(k))
            if v:
                pieces.append(v)
        return " > ".join(pieces)
    return clean_spaces(path_obj)


def infer_title(payload: Dict[str, Any]) -> str:
    return first_nonempty(
        payload.get("titolo"),
        payload.get("atto_titolo"),
        payload.get("titolo_atto"),
        payload.get("document_title"),
        "Testo unico delle leggi sull'ordinamento degli enti locali",
    ) or "Testo unico delle leggi sull'ordinamento degli enti locali"


def infer_atto_tipo(payload: Dict[str, Any]) -> str:
    return first_nonempty(payload.get("atto_tipo"), payload.get("tipo_atto"), "Decreto legislativo") or "Decreto legislativo"


def infer_uri(payload: Dict[str, Any]) -> str:
    return first_nonempty(
        payload.get("uri_ufficiale_articolo"),
        payload.get("uri_ufficiale"),
        payload.get("article_url"),
        payload.get("source_url"),
        payload.get("url"),
        "",
    ) or ""


def infer_trace_id(payload: Dict[str, Any], slug: str) -> str:
    return first_nonempty(payload.get("trace_id"), f"trace_tuel_{slug}") or f"trace_tuel_{slug}"


def infer_rubrica(payload: Dict[str, Any], text: str) -> str:
    direct = first_nonempty(payload.get("rubrica_articolo"), payload.get("rubrica"), payload.get("article_rubrica"))
    if direct:
        return direct
    # Fallback dal testo: "Articolo 194 - Riconoscimento di legittimità di debiti fuori bilancio"
    lines = [clean_spaces(x) for x in text.splitlines() if clean_spaces(x)]
    if not lines:
        return ""
    first = lines[0]
    if " - " in first:
        left, right = first.split(" - ", 1)
        if left.lower().startswith("articolo"):
            return right.strip()
    if len(lines) >= 2 and lines[0].lower().startswith("articolo") and not lines[1].lower().startswith("articolo"):
        return lines[1]
    return ""


def normalize_raw_article(payload: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
    text = first_nonempty(
        payload.get("testo_plain"),
        payload.get("testo_unita"),
        payload.get("text"),
        payload.get("contenuto"),
        payload.get("testo"),
        "",
    ) or ""
    articolo = parse_article_label(
        first_nonempty(
            payload.get("article_label_heading"),
            payload.get("article_label_index"),
            payload.get("article_label"),
            payload.get("articolo"),
            payload.get("article"),
            payload.get("numero_articolo"),
            file_path.stem.replace("art_", "").replace("_", "-"),
        )
    )
    slug = article_slug(articolo)
    rubrica = infer_rubrica(payload, text)
    hierarchy_path = payload.get("hierarchy_path") or {
        "atto": "D.Lgs. 267/2000",
        "titolo": first_nonempty(payload.get("titolo_parte"), payload.get("parte"), ""),
        "capo": first_nonempty(payload.get("capo"), payload.get("chapter"), ""),
        "capo_rubrica": first_nonempty(payload.get("capo_rubrica"), payload.get("chapter_title"), ""),
        "articolo": articolo,
    }
    return {
        "_file_path": str(file_path),
        "article_label_heading": articolo,
        "article_label_index": articolo,
        "article_label_slug": slug,
        "ordine_indice": int(payload.get("ordine_indice") or payload.get("position_index") or sort_tuple(articolo)[0]),
        "capo": first_nonempty(payload.get("capo"), payload.get("chapter"), ""),
        "capo_rubrica": first_nonempty(payload.get("capo_rubrica"), payload.get("chapter_title"), ""),
        "rubrica_articolo": rubrica,
        "testo_plain": text,
        "atto_tipo": infer_atto_tipo(payload),
        "atto_numero": first_nonempty(payload.get("atto_numero"), payload.get("numero_atto"), "267") or "267",
        "atto_anno": first_nonempty(payload.get("atto_anno"), payload.get("anno_atto"), "2000") or "2000",
        "titolo": infer_title(payload),
        "uri_ufficiale_articolo": infer_uri(payload),
        "uri_ufficiale": infer_uri(payload),
        "stato_vigenza": first_nonempty(payload.get("stato_vigenza"), "VIGENTE_VERIFICATA") or "VIGENTE_VERIFICATA",
        "data_vigenza_inizio": first_nonempty(payload.get("data_vigenza_inizio"), payload.get("vigore_dal"), ""),
        "trace_id": infer_trace_id(payload, slug),
        "hash_contenuto": sha256_text(text),
        "record_id": first_nonempty(payload.get("record_id"), f"raw_tuel_art_{slug}") or f"raw_tuel_art_{slug}",
        "hierarchy_path": hierarchy_path,
    }


def load_raw_articles(raw_dir: Path) -> List[Dict[str, Any]]:
    if not raw_dir.exists():
        raise FileNotFoundError(f"Directory raw non trovata: {raw_dir}")
    articles: List[Dict[str, Any]] = []
    for path in sorted(raw_dir.glob("art_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError(f"JSON non valido: {path} -> {exc}") from exc
        articles.append(normalize_raw_article(payload, path))

    if not articles:
        raise ValueError(f"Nessun file art_*.json trovato in {raw_dir}")

    articles.sort(key=lambda x: (
        int(x.get("ordine_indice", 9999) or 9999),
        sort_tuple(x.get("article_label_heading", "9999")),
    ))
    return articles


def build_corpus_domain(created_at: str, count: int, corpus_hash: str, expected_count: int, domain_code: str) -> Dict[str, Any]:
    return {
        "record_id": f"corpusdomain_{domain_code}",
        "record_type": "CorpusDomain",
        "corpus_domain_id": f"corpus_{domain_code}",
        "domain_code": domain_code,
        "domain_name": "D.Lgs. 267/2000 - TUEL",
        "domain_description": "Corpus armonizzato del Testo unico delle leggi sull'ordinamento degli enti locali.",
        "authoritative_scope": "fonte primaria ufficiale",
        "source_priority_order": ["Normattiva"],
        "coverage_scope": f"{count}/{expected_count} articoli attesi",
        "update_policy": "manual_controlled_refresh",
        "dedup_policy": "hash_plus_article_anchor",
        "corpus_status": "READY" if count == expected_count else "INCOMPLETE",
        "created_at": created_at,
        "updated_at": created_at,
        "schema_version": SCHEMA_VERSION,
        "record_version": RECORD_VERSION,
        "source_layer": "B",
        "active_flag": True,
        "jurisdiction_scope": "Stato",
        "applicable_entity_scope": "enti locali",
        "contains_annexes_flag": False,
        "contains_multivigente_flag": True,
        "corpus_hash": corpus_hash,
    }


def build_source_document(articles: List[Dict[str, Any]], created_at: str, domain_code: str) -> Dict[str, Any]:
    first = articles[0]
    corpus_text = "\n\n".join(a.get("testo_plain", "") for a in articles)
    return {
        "record_id": f"srcdoc_{domain_code}_full",
        "record_type": "SourceDocument",
        "source_id": f"source_{domain_code}",
        "source_type": "norma",
        "corpus_domain_id": f"corpus_{domain_code}",
        "atto_tipo": first.get("atto_tipo", "Decreto legislativo"),
        "atto_numero": first.get("atto_numero", "267"),
        "atto_anno": first.get("atto_anno", "2000"),
        "titolo": first.get("titolo"),
        "ente_emittente": "Stato",
        "pubblicazione": "Gazzetta Ufficiale",
        "data_pubblicazione": first.get("data_pubblicazione") or "2000-09-28",
        "uri_ufficiale": first.get("uri_ufficiale") or "",
        "stato_verifica_fonte": "VERIFIED",
        "stato_vigenza": "VIGENTE_VERIFICATA",
        "versione_documento": "vigente",
        "hash_contenuto": sha256_text(corpus_text),
        "data_vigenza_inizio": min((a.get("data_vigenza_inizio") for a in articles if a.get("data_vigenza_inizio")), default=None),
        "data_vigenza_fine": None,
        "lingua": "it",
        "dominio_ppav": "enti_locali",
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
        "trace_id": f"trace_build_{domain_code}_{created_at.replace(':','').replace('-','')}",
        "active_flag": True,
        "article_count": len(articles),
    }


def build_norm_unit(article: Dict[str, Any], source_id: str, created_at: str, domain_code: str) -> Dict[str, Any]:
    label = article["article_label_heading"]
    return {
        "record_id": f"normunit_{domain_code}_art_{article['article_label_slug']}",
        "record_type": "NormUnit",
        "norm_unit_id": f"{domain_code}_art_{article['article_label_slug']}",
        "source_id": source_id,
        "unit_type": "articolo",
        "articolo": label,
        "comma": None,
        "lettera": None,
        "numero": None,
        "allegato": None,
        "rubrica": article.get("rubrica_articolo", ""),
        "testo_unita": article.get("testo_plain", ""),
        "position_index": article.get("ordine_indice"),
        "hierarchy_path": article.get("hierarchy_path"),
        "cross_reference_ids": [],
        "vigenza_ref_id": f"vigenza_{domain_code}_art_{article['article_label_slug']}",
        "norm_unit_status": "PARSED",
        "created_at": created_at,
        "updated_at": created_at,
        "schema_version": SCHEMA_VERSION,
        "record_version": RECORD_VERSION,
        "source_layer": "B",
        "trace_id": article.get("trace_id"),
        "active_flag": True,
        "uri_ufficiale": article.get("uri_ufficiale_articolo", ""),
        "stato_vigenza": article.get("stato_vigenza"),
        "hash_contenuto": article.get("hash_contenuto"),
    }


def build_chunk_record(article: Dict[str, Any], source_id: str, created_at: str, domain_code: str) -> Dict[str, Any]:
    text = article.get("testo_plain", "")
    return {
        "record_id": f"chunkrec_{domain_code}_art_{article['article_label_slug']}_001",
        "record_type": "ChunkRecord",
        "chunk_id": f"{domain_code}_art_{article['article_label_slug']}_001",
        "source_id": source_id,
        "norm_unit_id": f"{domain_code}_art_{article['article_label_slug']}",
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
        "uri_ufficiale": article.get("uri_ufficiale_articolo", ""),
        "article_label": article.get("article_label_heading"),
    }


def build_vigenza_record(article: Dict[str, Any], source_id: str, created_at: str, domain_code: str) -> Dict[str, Any]:
    return {
        "record_id": f"vigenzarec_{domain_code}_art_{article['article_label_slug']}",
        "record_type": "VigenzaRecord",
        "vigenza_id": f"vigenza_{domain_code}_art_{article['article_label_slug']}",
        "source_id": source_id,
        "norm_unit_id": f"{domain_code}_art_{article['article_label_slug']}",
        "stato_vigenza": article.get("stato_vigenza", "VIGENTE_VERIFICATA"),
        "data_inizio": article.get("data_vigenza_inizio") or None,
        "data_fine": None,
        "vigenza_status": "READY",
        "created_at": created_at,
        "updated_at": created_at,
        "schema_version": SCHEMA_VERSION,
        "record_version": RECORD_VERSION,
        "source_layer": "B",
        "trace_id": article.get("trace_id"),
        "active_flag": True,
    }


def citation_prefix(atto_tipo: str, numero: str, anno: str) -> str:
    lowered = clean_spaces(atto_tipo).lower()
    if "decreto legislativo" in lowered:
        return f"D.Lgs. n. {numero}/{anno}"
    return f"{atto_tipo} n. {numero}/{anno}"


def build_citation_record(article: Dict[str, Any], source_document: Dict[str, Any], created_at: str, domain_code: str) -> Dict[str, Any]:
    art = article["article_label_heading"]
    citation_text = f"{citation_prefix(source_document['atto_tipo'], source_document['atto_numero'], source_document['atto_anno'])}, art. {art}"
    return {
        "record_id": f"citationrec_{domain_code}_art_{article['article_label_slug']}",
        "record_type": "CitationRecord",
        "citation_id": f"citation_{domain_code}_art_{article['article_label_slug']}",
        "source_id": source_document["source_id"],
        "norm_unit_id": f"{domain_code}_art_{article['article_label_slug']}",
        "atto_tipo": source_document["atto_tipo"],
        "atto_numero": source_document["atto_numero"],
        "atto_anno": source_document["atto_anno"],
        "articolo": art,
        "comma": None,
        "lettera": None,
        "numero": None,
        "uri_ufficiale": article.get("uri_ufficiale_articolo") or source_document.get("uri_ufficiale", ""),
        "stato_vigenza": article.get("stato_vigenza", "VIGENTE_VERIFICATA"),
        "citation_text": citation_text,
        "citation_status": "READY",
        "created_at": created_at,
        "updated_at": created_at,
        "schema_version": SCHEMA_VERSION,
        "record_version": RECORD_VERSION,
        "source_layer": "B",
        "trace_id": article.get("trace_id"),
        "active_flag": True,
    }


def build_records(articles: List[Dict[str, Any]], expected_count: int, domain_code: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    created_at = now_iso()
    corpus_text = "\n\n".join(a.get("testo_plain", "") for a in articles)
    corpus_hash = sha256_text(corpus_text)

    records: List[Dict[str, Any]] = []
    corpus_domain = build_corpus_domain(created_at, len(articles), corpus_hash, expected_count, domain_code)
    source_document = build_source_document(articles, created_at, domain_code)
    source_id = source_document["source_id"]
    records.append(corpus_domain)
    records.append(source_document)

    for article in articles:
        records.append(build_norm_unit(article, source_id, created_at, domain_code))
        records.append(build_chunk_record(article, source_id, created_at, domain_code))
        records.append(build_vigenza_record(article, source_id, created_at, domain_code))
        records.append(build_citation_record(article, source_document, created_at, domain_code))

    manifest = {
        "status": "OK" if len(articles) == expected_count else "INCOMPLETE",
        "domain_code": domain_code,
        "article_count": len(articles),
        "expected_articles": expected_count,
        "generated_at": created_at,
        "source_id": source_id,
        "corpus_hash": corpus_hash,
    }
    return records, manifest


def write_build_output(records: List[Dict[str, Any]], manifest: Dict[str, Any], output_dir: Path, domain_code: str) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{domain_code}_rag_ready.json"
    ndjson_path = output_dir / f"{domain_code}_rag_ready.ndjson"
    manifest_path = output_dir / f"{domain_code}_build_manifest.json"

    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    with ndjson_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "json": str(json_path),
        "ndjson": str(ndjson_path),
        "manifest": str(manifest_path),
    }


def load_records(input_path: Path) -> List[Dict[str, Any]]:
    if not input_path.exists():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    if input_path.suffix.lower() == ".ndjson":
        out = []
        with input_path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception as exc:
                    raise ValueError(f"NDJSON non valido alla riga {line_no}: {exc}") from exc
        return out
    data = json.loads(input_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("records"), list):
        return data["records"]
    if isinstance(data, dict):
        return [data]
    raise ValueError("Formato input non supportato")


def build_index(records: Iterable[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
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
    return source_document, norm_units, chunks


def get_embedding_function(model_name: str):
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except Exception as exc:
        raise RuntimeError(
            "Impossibile importare SentenceTransformerEmbeddingFunction. Verifica chromadb e sentence-transformers."
        ) from exc
    return SentenceTransformerEmbeddingFunction(model_name=model_name)


def make_chunk_metadata(chunk: Dict[str, Any], norm_unit: Dict[str, Any], source_document: Dict[str, Any], domain_code: str) -> Dict[str, Any]:
    articolo = clean_spaces(norm_unit.get("articolo"))
    comma = clean_spaces(norm_unit.get("comma"))
    rubrica = clean_spaces(norm_unit.get("rubrica"))
    metadata: Dict[str, Any] = {
        "domain_code": domain_code,
        "source_id": clean_spaces(chunk.get("source_id")),
        "norm_unit_id": clean_spaces(chunk.get("norm_unit_id")),
        "chunk_id": clean_spaces(chunk.get("chunk_id")),
        "record_type": "ChunkRecord",
        "atto_tipo": clean_spaces(source_document.get("atto_tipo")),
        "atto_numero": clean_spaces(source_document.get("atto_numero")),
        "atto_anno": clean_spaces(source_document.get("atto_anno")),
        "titolo": clean_spaces(source_document.get("titolo")),
        "uri_ufficiale": clean_spaces(source_document.get("uri_ufficiale")),
        "stato_vigenza": clean_spaces(source_document.get("stato_vigenza")),
        "articolo": articolo,
        "comma": comma,
        "rubrica": rubrica,
        "hierarchy_path": stringify_hierarchy_path(norm_unit.get("hierarchy_path")),
        "chunk_sequence": int(chunk.get("chunk_sequence", 0) or 0),
        "retrievable_flag": bool(chunk.get("retrievable_flag", False)),
        "orphan_flag": bool(chunk.get("orphan_flag", False)),
        "quality_flag": clean_spaces(chunk.get("quality_flag")),
        "parse_confidence": float(chunk.get("parse_confidence", 0.0) or 0.0),
        "trace_id": clean_spaces(chunk.get("trace_id")),
    }
    prefix = citation_prefix(metadata["atto_tipo"], metadata["atto_numero"], metadata["atto_anno"])
    citation = f"{prefix}, art. {articolo}" if articolo else prefix
    if comma:
        citation += f", comma {comma}"
    metadata["citation_text"] = citation
    return metadata


def batched(items: List[Any], batch_size: int) -> Iterable[List[Any]]:
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def print_query_result(query: str, result: Dict[str, Any]) -> None:
    print(f"\nQuery: {query}")
    ids = result.get("ids", [[]])[0]
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    for idx, cid in enumerate(ids, start=1):
        meta = metas[idx - 1] if idx - 1 < len(metas) else {}
        doc = docs[idx - 1] if idx - 1 < len(docs) else ""
        dist = distances[idx - 1] if idx - 1 < len(distances) else None
        print(f"  [{idx}] chunk_id={cid}")
        print(f"      citazione={meta.get('citation_text', '')}")
        print(f"      rubrica={meta.get('rubrica', '')}")
        print(f"      distanza={dist}")
        print(f"      uri={meta.get('uri_ufficiale', '')}")
        print(f"      testo={clean_spaces(doc)[:300]}...")


def ingest_rag_ready(input_path: Path, persist_dir: str, collection_name: str, embedding_model: str, batch_size: int,
                     upsert: bool, reset_collection: bool, domain_code: str,
                     manifest_path: Optional[Path] = None, test_queries: Optional[List[str]] = None, top_k: int = 5) -> Dict[str, Any]:
    try:
        import chromadb
    except Exception as exc:
        raise RuntimeError("chromadb non installato o non importabile") from exc

    records = load_records(input_path)
    source_document, norm_units, chunks = build_index(records)
    client = chromadb.PersistentClient(path=persist_dir)
    embedding_fn = get_embedding_function(embedding_model)

    if reset_collection:
        try:
            client.delete_collection(collection_name)
            print(f"Collection eliminata: {collection_name}")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={
            "domain_code": domain_code,
            "source_layer": "B",
            "schema_version": "v2",
            "source_document_id": clean_spaces(source_document.get("record_id")),
            "atto_tipo": clean_spaces(source_document.get("atto_tipo")),
            "atto_numero": clean_spaces(source_document.get("atto_numero")),
            "atto_anno": clean_spaces(source_document.get("atto_anno")),
        },
        embedding_function=embedding_fn,
    )

    chunk_records: List[Tuple[str, str, Dict[str, Any]]] = []
    skipped: List[str] = []
    for chunk in chunks:
        if not chunk.get("retrievable_flag", True) or chunk.get("orphan_flag", False):
            skipped.append(clean_spaces(chunk.get("chunk_id")))
            continue
        chunk_text = clean_spaces(chunk.get("chunk_text"))
        if not chunk_text:
            skipped.append(clean_spaces(chunk.get("chunk_id")))
            continue
        norm_unit = norm_units.get(clean_spaces(chunk.get("norm_unit_id")))
        if not norm_unit:
            skipped.append(clean_spaces(chunk.get("chunk_id")))
            continue
        chunk_id = clean_spaces(chunk.get("chunk_id") or chunk.get("record_id"))
        if not chunk_id:
            skipped.append("<missing_chunk_id>")
            continue
        metadata = make_chunk_metadata(chunk, norm_unit, source_document, domain_code)
        chunk_records.append((chunk_id, chunk_text, metadata))

    if not chunk_records:
        raise RuntimeError("Nessun ChunkRecord ingestibile trovato")

    for batch_no, batch in enumerate(batched(chunk_records, batch_size), start=1):
        ids = [x[0] for x in batch]
        docs = [x[1] for x in batch]
        metas = [x[2] for x in batch]
        if upsert:
            collection.upsert(ids=ids, documents=docs, metadatas=metas)
        else:
            collection.add(ids=ids, documents=docs, metadatas=metas)
        print(f"Batch {batch_no}: ingestiti {len(batch)} chunk")

    manifest = {
        "status": "OK",
        "collection": collection_name,
        "persist_dir": persist_dir,
        "embedding_model": embedding_model,
        "ingested_chunks": len(chunk_records),
        "collection_count": collection.count(),
        "skipped_chunks": len(skipped),
        "domain_code": domain_code,
        "source_document": {
            "atto_tipo": clean_spaces(source_document.get("atto_tipo")),
            "atto_numero": clean_spaces(source_document.get("atto_numero")),
            "atto_anno": clean_spaces(source_document.get("atto_anno")),
            "titolo": clean_spaces(source_document.get("titolo")),
            "uri_ufficiale": clean_spaces(source_document.get("uri_ufficiale")),
        },
    }

    if manifest_path:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))

    if test_queries:
        print("\n=== TEST QUERY ===")
        for q in test_queries:
            result = collection.query(query_texts=[q], n_results=top_k, include=["documents", "metadatas", "distances"])
            print_query_result(q, result)

    return manifest


def cmd_build(args: argparse.Namespace) -> int:
    articles = load_raw_articles(Path(args.raw_dir))
    records, manifest = build_records(articles, args.expected_count, args.domain_code)
    outputs = write_build_output(records, manifest, Path(args.output_dir), args.domain_code)
    summary = {"status": manifest["status"], "outputs": outputs, "article_count": manifest["article_count"]}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest) if args.manifest else None
    ingest_rag_ready(
        input_path=Path(args.input),
        persist_dir=args.persist_dir,
        collection_name=args.collection,
        embedding_model=args.embedding_model,
        batch_size=args.batch_size,
        upsert=args.upsert,
        reset_collection=args.reset_collection,
        domain_code=args.domain_code,
        manifest_path=manifest_path,
        test_queries=args.test_query,
        top_k=args.top_k,
    )
    return 0


def cmd_rebuild_ingest(args: argparse.Namespace) -> int:
    articles = load_raw_articles(Path(args.raw_dir))
    records, manifest = build_records(articles, args.expected_count, args.domain_code)
    outputs = write_build_output(records, manifest, Path(args.output_dir), args.domain_code)
    print(json.dumps({"build_status": manifest["status"], "build_outputs": outputs}, ensure_ascii=False, indent=2))

    ingest_manifest = Path(args.ingest_manifest) if args.ingest_manifest else (Path(args.output_dir) / f"{args.domain_code}_chroma_manifest.json")
    ingest_rag_ready(
        input_path=Path(outputs["ndjson"]),
        persist_dir=args.persist_dir,
        collection_name=args.collection,
        embedding_model=args.embedding_model,
        batch_size=args.batch_size,
        upsert=args.upsert,
        reset_collection=args.reset_collection,
        domain_code=args.domain_code,
        manifest_path=ingest_manifest,
        test_queries=args.test_query,
        top_k=args.top_k,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rebuild + ingest armonizzato del TUEL verso una nuova collection coerente con la 241.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Ricostruisce il rag_ready armonizzato TUEL a partire dai JSON raw articolo-per-articolo.")
    p_build.add_argument("--raw-dir", required=True, help="Directory contenente art_*.json del TUEL")
    p_build.add_argument("--output-dir", required=True, help="Directory di output per rag_ready e manifest")
    p_build.add_argument("--expected-count", type=int, default=DEFAULT_EXPECTED_COUNT)
    p_build.add_argument("--domain-code", default=DEFAULT_DOMAIN_CODE)
    p_build.set_defaults(func=cmd_build)

    p_ingest = sub.add_parser("ingest", help="Ingerisce un rag_ready armonizzato TUEL in una nuova collection Chroma.")
    p_ingest.add_argument("--input", required=True, help="File .ndjson o .json rag_ready armonizzato")
    p_ingest.add_argument("--persist-dir", required=True)
    p_ingest.add_argument("--collection", default=DEFAULT_COLLECTION)
    p_ingest.add_argument("--domain-code", default=DEFAULT_DOMAIN_CODE)
    p_ingest.add_argument("--embedding-model", default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    p_ingest.add_argument("--batch-size", type=int, default=32)
    p_ingest.add_argument("--upsert", action="store_true")
    p_ingest.add_argument("--reset-collection", action="store_true")
    p_ingest.add_argument("--manifest")
    p_ingest.add_argument("--test-query", action="append", default=[])
    p_ingest.add_argument("--top-k", type=int, default=5)
    p_ingest.set_defaults(func=cmd_ingest)

    p_all = sub.add_parser("rebuild-ingest", help="Esegue build armonizzata TUEL e ingestione in una nuova collection, senza toccare la storica 'norme' salvo reset esplicito della nuova collection.")
    p_all.add_argument("--raw-dir", required=True)
    p_all.add_argument("--output-dir", required=True)
    p_all.add_argument("--persist-dir", required=True)
    p_all.add_argument("--collection", default=DEFAULT_COLLECTION)
    p_all.add_argument("--expected-count", type=int, default=DEFAULT_EXPECTED_COUNT)
    p_all.add_argument("--domain-code", default=DEFAULT_DOMAIN_CODE)
    p_all.add_argument("--embedding-model", default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    p_all.add_argument("--batch-size", type=int, default=32)
    p_all.add_argument("--upsert", action="store_true")
    p_all.add_argument("--reset-collection", action="store_true")
    p_all.add_argument("--ingest-manifest")
    p_all.add_argument("--test-query", action="append", default=[])
    p_all.add_argument("--top-k", type=int, default=5)
    p_all.set_defaults(func=cmd_rebuild_ingest)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        eprint(f"Errore fatale: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
