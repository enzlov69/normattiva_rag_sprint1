#!/usr/bin/env python3
"""
D.Lgs. 33/2013 — Parser skeleton v1

Skeleton operativo agganciato al contract:
- DLGS33_2013_parser_contract_v1.json
- DLGS33_2013_parser_mapping_rules_v1.json
- DLGS33_2013_parser_error_catalog_v1.json

Obiettivo:
- validare gli input raw Normattiva;
- costruire il response package del parser;
- fornire hook/stub già collegati per:
  - articles.json
  - commi.json
  - *_chunks.jsonl
- bloccare il flusso in caso di errori critici del Livello B.

Nota:
Questo script è uno skeleton tecnico. I punti marcati TODO devono essere sostituiti con
la logica DOM reale di Normattiva. La struttura, i guardrail e i path sono già coerenti
con il cantiere D.Lgs. 33/2013.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


LOGGER = logging.getLogger("dlgs33_parser")


# ============================================================================
# Exceptions
# ============================================================================

class ParserContractError(Exception):
    """Errore tecnico del contract/parser."""


class ParserBlockedError(ParserContractError):
    """Errore bloccante coerente con il catalogo del contract."""


# ============================================================================
# Data classes
# ============================================================================

@dataclass
class ValidationIssue:
    code: str
    severity: str
    message: str
    path: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "path": self.path,
            "details": self.details,
        }


@dataclass
class ParserContext:
    request_id: str
    case_id: str
    trace_id: str
    api_version: str
    caller_module: str
    target_module: str
    timestamp: str
    project_root: Path
    contract_path: Path
    contract: Dict[str, Any]
    error_catalog: Dict[str, Any]
    mapping_rules: Dict[str, Any]
    dry_run: bool = False
    allow_placeholder_inputs: bool = False


# ============================================================================
# Utility
# ============================================================================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def sha_placeholder(content: str) -> str:
    """
    Hash placeholder minimale, volutamente semplice per lo skeleton.
    Da sostituire con SHA-256 reale nella versione implementata.
    """
    return f"LEN_{len(content)}"


def resolve_project_root(start: Path) -> Path:
    for current in [start, *start.parents]:
        if current.name == "normattiva_rag_sprint1":
            return current
    raise ParserContractError("Impossibile risolvere la project root normattiva_rag_sprint1")


def resolve_relpath(project_root: Path, rel: str) -> Path:
    return project_root / rel.replace("/", str(Path("/").anchor or "/")).lstrip("/")


def normalize_relpath(rel: str) -> Path:
    return Path(*rel.split("/"))


def is_placeholder_content(text: str) -> bool:
    markers = [
        "PLACEHOLDER TECNICO",
        "TO_REPLACE_WITH_OFFICIAL_CONTENT",
        "TESTO_ARTICOLO_COMPLETO_DA_SOSTITUIRE",
        "TESTO_COMMA_COMPLETO_DA_SOSTITUIRE",
        "TESTO_BLOCCO_ALLEGATO_DA_SOSTITUIRE",
    ]
    return any(marker in text for marker in markers)


def require(condition: bool, code: str, message: str, *, path: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
    if not condition:
        raise ParserBlockedError(json.dumps({
            "code": code,
            "severity": "CRITICAL",
            "message": message,
            "path": path,
            "details": details or {},
        }, ensure_ascii=False))


def blocked_issue_from_exception(exc: ParserBlockedError) -> ValidationIssue:
    try:
        payload = json.loads(str(exc))
        return ValidationIssue(
            code=payload.get("code", "BLOCK_UNKNOWN"),
            severity=payload.get("severity", "CRITICAL"),
            message=payload.get("message", "Errore bloccante"),
            path=payload.get("path"),
            details=payload.get("details", {}),
        )
    except Exception:
        return ValidationIssue(
            code="BLOCK_UNKNOWN",
            severity="CRITICAL",
            message=str(exc),
        )


# ============================================================================
# Contract loading
# ============================================================================

def load_contract_bundle(project_root: Path) -> Tuple[Path, Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    cantiere_dir = project_root / "data" / "cantieri" / "dlgs33_2013"
    contract_path = cantiere_dir / "DLGS33_2013_parser_contract_v1.json"
    mapping_path = cantiere_dir / "DLGS33_2013_parser_mapping_rules_v1.json"
    error_catalog_path = cantiere_dir / "DLGS33_2013_parser_error_catalog_v1.json"

    require(contract_path.exists(), "BLOCK_AUDIT_TRACE_INCOMPLETE", "Parser contract mancante", path=str(contract_path))
    require(mapping_path.exists(), "BLOCK_AUDIT_TRACE_INCOMPLETE", "Mapping rules mancanti", path=str(mapping_path))
    require(error_catalog_path.exists(), "BLOCK_AUDIT_TRACE_INCOMPLETE", "Error catalog mancante", path=str(error_catalog_path))

    return contract_path, load_json(contract_path), load_json(mapping_path), load_json(error_catalog_path)


def build_context(args: argparse.Namespace) -> ParserContext:
    project_root = resolve_project_root(Path(args.project_root).resolve() if args.project_root else Path(__file__).resolve())
    contract_path, contract, mapping_rules, error_catalog = load_contract_bundle(project_root)

    return ParserContext(
        request_id=args.request_id,
        case_id=args.case_id,
        trace_id=args.trace_id,
        api_version=contract["api_version"],
        caller_module=args.caller_module,
        target_module=contract["request_contract"]["target_module"],
        timestamp=utc_now_iso(),
        project_root=project_root,
        contract_path=contract_path,
        contract=contract,
        error_catalog=error_catalog,
        mapping_rules=mapping_rules,
        dry_run=args.dry_run,
        allow_placeholder_inputs=args.allow_placeholder_inputs,
    )


# ============================================================================
# Validation
# ============================================================================

def validate_contract_shape(contract: Dict[str, Any]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    required_top = [
        "contract_id", "api_version", "schema_version", "request_contract",
        "input_contract", "output_contract", "field_requirements",
        "blocking_errors", "response_package"
    ]
    for key in required_top:
        if key not in contract:
            issues.append(ValidationIssue(
                code="BLOCK_MISSING_MANDATORY_FIELDS",
                severity="CRITICAL",
                message=f"Campo contract mancante: {key}"
            ))
    return issues


def validate_input_files(ctx: ParserContext) -> Tuple[List[ValidationIssue], Dict[str, Path]]:
    issues: List[ValidationIssue] = []
    resolved_inputs: Dict[str, Path] = {}

    for spec in ctx.contract["input_contract"]["accepted_inputs"]:
        rel_path = spec["path"]
        path = ctx.project_root / normalize_relpath(rel_path)
        resolved_inputs[spec["input_id"]] = path

        if spec.get("required", False) and not path.exists():
            issues.append(ValidationIssue(
                code="BLOCK_INPUT_EMPTY",
                severity="CRITICAL",
                message="File input richiesto non presente",
                path=str(path),
                details={"input_id": spec["input_id"], "source_ref": spec["source_ref"]},
            ))
            continue

        if path.exists():
            content = read_text(path)
            if not content.strip():
                issues.append(ValidationIssue(
                    code="BLOCK_INPUT_EMPTY",
                    severity="CRITICAL",
                    message="File input vuoto",
                    path=str(path),
                    details={"input_id": spec["input_id"]},
                ))

            if (not ctx.allow_placeholder_inputs) and is_placeholder_content(content):
                issues.append(ValidationIssue(
                    code="BLOCK_INPUT_EMPTY",
                    severity="CRITICAL",
                    message="Input placeholder rilevato: sostituire con contenuto ufficiale prima del parsing",
                    path=str(path),
                    details={"input_id": spec["input_id"], "placeholder_detected": True},
                ))

            if spec["mime"] == "text/html" and "normattiva" not in content.lower() and (not ctx.allow_placeholder_inputs):
                issues.append(ValidationIssue(
                    code="BLOCK_SOURCE_NOT_OFFICIAL",
                    severity="CRITICAL",
                    message="Il file HTML non sembra riconducibile a Normattiva",
                    path=str(path),
                    details={"input_id": spec["input_id"]},
                ))

    return issues, resolved_inputs


def validate_no_forbidden_level_b_fields(payload: Dict[str, Any], forbidden_fields: List[str], path_prefix: str = "") -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    def walk(node: Any, current_path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                joined = f"{current_path}.{key}" if current_path else key
                if key in forbidden_fields:
                    issues.append(ValidationIssue(
                        code="BLOCK_FORBIDDEN_LEVEL_B_FIELD",
                        severity="CRITICAL",
                        message=f"Campo vietato nel payload del Livello B: {key}",
                        path=joined,
                    ))
                walk(value, joined)
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                walk(item, f"{current_path}[{idx}]")

    walk(payload, path_prefix)
    return issues


# ============================================================================
# Parsing stubs
# ============================================================================

def source_meta_from_input_id(input_id: str) -> Dict[str, str]:
    if input_id == "raw_main_html":
        return {
            "source_id": "dlgs33_2013_vigente_normattiva",
            "source_type": "normative_primary",
            "atto_tipo": "Decreto legislativo",
            "atto_numero": "33",
            "atto_anno": "2013",
            "titolo": "Riordino della disciplina riguardante il diritto di accesso civico e gli obblighi di pubblicità, trasparenza e diffusione di informazioni da parte delle pubbliche amministrazioni",
            "uri_ufficiale": "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2013-03-14;33!vig=",
            "data_pubblicazione": "2013-04-05",
            "data_vigenza_inizio": "2013-04-20",
            "versione_documento": "vigente",
        }
    if input_id == "raw_linked_html":
        return {
            "source_id": "dlgs97_2016_normattiva",
            "source_type": "normative_linked_essential",
            "atto_tipo": "Decreto legislativo",
            "atto_numero": "97",
            "atto_anno": "2016",
            "titolo": "Revisione e semplificazione delle disposizioni in materia di prevenzione della corruzione, pubblicita' e trasparenza",
            "uri_ufficiale": "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2016-05-25;97=",
            "data_pubblicazione": "2016-06-08",
            "data_vigenza_inizio": "2016-06-23",
            "versione_documento": "originario_collegato",
        }
    raise ParserContractError(f"input_id non gestito: {input_id}")


def build_source_document(ctx: ParserContext, input_id: str, content: str) -> Dict[str, Any]:
    meta = source_meta_from_input_id(input_id)
    return {
        "source_id": meta["source_id"],
        "source_type": meta["source_type"],
        "atto_tipo": meta["atto_tipo"],
        "atto_numero": meta["atto_numero"],
        "atto_anno": meta["atto_anno"],
        "titolo": meta["titolo"],
        "ente_emittente": "Stato",
        "pubblicazione": "Normattiva",
        "data_pubblicazione": meta["data_pubblicazione"],
        "uri_ufficiale": meta["uri_ufficiale"],
        "stato_verifica_fonte": "VERIFIED_OFFICIAL_SOURCE",
        "stato_vigenza": "VIGENTE_VERIFICATA",
        "versione_documento": meta["versione_documento"],
        "hash_contenuto": sha_placeholder(content),
        "record_id": f"srcdoc_{meta['source_id']}",
        "record_type": "SourceDocument",
        "corpus_domain_id": "corpus_trasparenza_amministrativa",
        "data_vigenza_inizio": meta["data_vigenza_inizio"],
        "data_vigenza_fine": None,
        "lingua": "it",
        "dominio_ppav": "trasparenza_amministrativa",
        "authoritative_flag": True,
        "last_verified_at": ctx.timestamp,
        "human_verified_flag": False,
        "document_status": "PARSED_STUB",
        "parse_ready_flag": True,
        "index_ready_flag": False,
        "annex_presence_flag": True,
        "multivigente_flag": False,
        "created_at": ctx.timestamp,
        "updated_at": ctx.timestamp,
        "schema_version": ctx.contract["schema_version"],
        "record_version": ctx.contract["record_version"],
        "source_layer": "B",
        "trace_id": ctx.trace_id,
        "active_flag": True,
    }


def strip_html_tags(text: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_articles_stub(html: str) -> List[Dict[str, Any]]:
    """
    TODO DOM reale Normattiva:
    - usare selettori strutturali veri;
    - preservare titoli/capi/articoli/commi;
    - gestire bis/ter/quater.
    """
    clean = strip_html_tags(html)
    # Tentativo minimale: cerca pattern "Art." o "Articolo"
    matches = list(re.finditer(r"\b(?:Art\.?|Articolo)\s+(\d+[a-zA-Z\-]*)", clean))
    if not matches:
        # Fallback stub minimo
        return [{
            "articolo": "1",
            "rubrica": "RUBRICA_DA_ESTRARRE",
            "testo_unita": clean[:4000] if clean else "TESTO_ARTICOLO_DA_ESTRARRE",
            "hierarchy_path": ["Titolo DA ESTRARRE", "articolo 1"],
            "position_index": 1,
        }]

    articles: List[Dict[str, Any]] = []
    for idx, match in enumerate(matches, start=1):
        start = match.start()
        end = matches[idx].start() if idx < len(matches) else len(clean)
        articolo = match.group(1)
        block = clean[start:end].strip()
        articles.append({
            "articolo": articolo,
            "rubrica": "RUBRICA_DA_ESTRARRE",
            "testo_unita": block,
            "hierarchy_path": [f"Titolo DA ESTRARRE", f"articolo {articolo}"],
            "position_index": idx,
        })
    return articles


def split_commi_stub(article_text: str) -> List[Tuple[str, str]]:
    """
    TODO DOM reale Normattiva:
    - ricavare i commi dal DOM, non da regex.
    """
    parts = re.split(r"\s(?=(\d+)\.\s)", article_text)
    results: List[Tuple[str, str]] = []
    if len(parts) >= 3:
        i = 1
        while i < len(parts):
            comma_num = parts[i]
            comma_text = (parts[i] + ". " + parts[i+1]).strip()
            results.append((comma_num, comma_text))
            i += 2
    else:
        # fallback: tutto il testo come comma 1
        results.append(("1", article_text))
    return results


def extract_annex_blocks_stub(html: str, annex_label: str) -> List[Dict[str, Any]]:
    """
    TODO DOM reale Normattiva:
    - segmentazione allegati per tabelle/sezioni/logical blocks.
    """
    clean = strip_html_tags(html)
    max_len = 1500
    blocks = []
    for i, offset in enumerate(range(0, len(clean), max_len), start=1):
        blocks.append({
            "annex_label": annex_label,
            "section_label": f"Sezione {i}",
            "chunk_text": clean[offset:offset + max_len] or f"TESTO_{annex_label}_DA_ESTRARRE",
            "chunk_sequence": i,
            "position_index": i,
            "hierarchy_path": [annex_label, f"Sezione {i}"],
        })
    if not blocks:
        blocks.append({
            "annex_label": annex_label,
            "section_label": "Sezione 1",
            "chunk_text": f"TESTO_{annex_label}_DA_ESTRARRE",
            "chunk_sequence": 1,
            "position_index": 1,
            "hierarchy_path": [annex_label, "Sezione 1"],
        })
    return blocks


# ============================================================================
# Mapping
# ============================================================================

def map_article_to_normunit(ctx: ParserContext, source_document: Dict[str, Any], item: Dict[str, Any]) -> Dict[str, Any]:
    art = str(item["articolo"])
    return {
        "record_id": f"normunit_{source_document['source_id']}_art_{art}",
        "record_type": "NormUnit",
        "norm_unit_id": f"{source_document['source_id']}_art_{art}",
        "source_id": source_document["source_id"],
        "unit_type": "articolo",
        "articolo": art,
        "comma": None,
        "lettera": None,
        "numero": None,
        "allegato": None,
        "rubrica": item.get("rubrica"),
        "testo_unita": item["testo_unita"],
        "position_index": item["position_index"],
        "hierarchy_path": item["hierarchy_path"],
        "cross_reference_ids": [],
        "vigenza_ref_id": f"vigenza_{source_document['source_id']}_art_{art}",
        "norm_unit_status": "PARSED_STUB",
        "created_at": ctx.timestamp,
        "updated_at": ctx.timestamp,
        "schema_version": ctx.contract["schema_version"],
        "record_version": ctx.contract["record_version"],
        "source_layer": "B",
        "trace_id": ctx.trace_id,
        "active_flag": True,
    }


def map_comma_to_normunit(ctx: ParserContext, source_document: Dict[str, Any], articolo: str, rubrica: str, position_index: int, comma_num: str, comma_text: str) -> Dict[str, Any]:
    return {
        "record_id": f"normunit_{source_document['source_id']}_art_{articolo}_com_{comma_num}",
        "record_type": "NormUnit",
        "norm_unit_id": f"{source_document['source_id']}_art_{articolo}_com_{comma_num}",
        "source_id": source_document["source_id"],
        "unit_type": "comma",
        "articolo": articolo,
        "comma": comma_num,
        "lettera": None,
        "numero": None,
        "allegato": None,
        "rubrica": rubrica,
        "testo_unita": comma_text,
        "position_index": position_index,
        "hierarchy_path": [f"Titolo DA ESTRARRE", f"articolo {articolo}", f"comma {comma_num}"],
        "cross_reference_ids": [],
        "vigenza_ref_id": f"vigenza_{source_document['source_id']}_art_{articolo}_com_{comma_num}",
        "norm_unit_status": "PARSED_STUB",
        "created_at": ctx.timestamp,
        "updated_at": ctx.timestamp,
        "schema_version": ctx.contract["schema_version"],
        "record_version": ctx.contract["record_version"],
        "source_layer": "B",
        "trace_id": ctx.trace_id,
        "active_flag": True,
    }


def map_annex_block_to_chunk(ctx: ParserContext, source_document: Dict[str, Any], annex_label: str, idx: int, block: Dict[str, Any]) -> Dict[str, Any]:
    norm_unit_id = f"{source_document['source_id']}_{annex_label.lower().replace(' ', '_')}_section_{idx}"
    return {
        "record_id": f"chunkrec_{source_document['source_id']}_{annex_label.lower().replace(' ', '_')}_{idx}",
        "record_type": "ChunkRecord",
        "chunk_id": f"{source_document['source_id']}_{annex_label.lower().replace(' ', '_')}_chunk_{idx}",
        "source_id": source_document["source_id"],
        "norm_unit_id": norm_unit_id,
        "chunk_text": block["chunk_text"],
        "chunk_sequence": block["chunk_sequence"],
        "chunk_context_before": "",
        "chunk_context_after": "",
        "embedding_vector_ref": None,
        "lexical_index_ref": None,
        "quality_flag": "STUB",
        "parse_confidence": 0.25,
        "retrievable_flag": True,
        "orphan_flag": False,
        "chunk_status": "PARSED_STUB",
        "created_at": ctx.timestamp,
        "updated_at": ctx.timestamp,
        "schema_version": ctx.contract["schema_version"],
        "record_version": ctx.contract["record_version"],
        "source_layer": "B",
        "trace_id": ctx.trace_id,
        "active_flag": True,
        "allegato": annex_label,
        "rubrica": block.get("section_label"),
        "hierarchy_path": block["hierarchy_path"],
        "position_index": block["position_index"],
        "source_uri": source_document["uri_ufficiale"],
    }


# ============================================================================
# Build outputs
# ============================================================================

def build_articles_file(ctx: ParserContext, source_document: Dict[str, Any], html: str) -> Dict[str, Any]:
    records = [map_article_to_normunit(ctx, source_document, item) for item in extract_articles_stub(html)]
    return {
        "file_type": "norm_units",
        "unit_scope": "articles",
        "template_flag": False,
        "parser_contract_version": ctx.contract["api_version"],
        "source_document": source_document,
        "records": records,
    }


def build_commi_file(ctx: ParserContext, source_document: Dict[str, Any], articles_file: Dict[str, Any]) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    position_index = 1
    for article in articles_file["records"]:
        articolo = str(article["articolo"])
        rubrica = article.get("rubrica") or ""
        for comma_num, comma_text in split_commi_stub(article["testo_unita"]):
            records.append(
                map_comma_to_normunit(ctx, source_document, articolo, rubrica, position_index, comma_num, comma_text)
            )
            position_index += 1

    return {
        "file_type": "norm_units",
        "unit_scope": "commi",
        "template_flag": False,
        "parser_contract_version": ctx.contract["api_version"],
        "source_document": source_document,
        "records": records,
    }


def build_annex_chunks(ctx: ParserContext, source_document: Dict[str, Any], html: str, annex_label: str) -> List[Dict[str, Any]]:
    blocks = extract_annex_blocks_stub(html, annex_label)
    return [map_annex_block_to_chunk(ctx, source_document, annex_label, idx, block) for idx, block in enumerate(blocks, start=1)]


# ============================================================================
# Output validation
# ============================================================================

def validate_output_wrapper(wrapper: Dict[str, Any], required_source_fields: List[str], required_record_fields: List[str]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    source_doc = wrapper.get("source_document", {})
    for field_name in required_source_fields:
        if field_name not in source_doc:
            issues.append(ValidationIssue(
                code="BLOCK_MISSING_MANDATORY_FIELDS",
                severity="CRITICAL",
                message=f"Campo SourceDocument mancante: {field_name}",
                path=f"source_document.{field_name}",
            ))

    for idx, record in enumerate(wrapper.get("records", [])):
        for field_name in required_record_fields:
            if field_name not in record:
                issues.append(ValidationIssue(
                    code="BLOCK_MISSING_MANDATORY_FIELDS",
                    severity="CRITICAL",
                    message=f"Campo record mancante: {field_name}",
                    path=f"records[{idx}].{field_name}",
                ))
        if not record.get("hierarchy_path"):
            issues.append(ValidationIssue(
                code="ERR_HIERARCHY_PATH_EMPTY",
                severity="HIGH",
                message="hierarchy_path mancante o vuoto",
                path=f"records[{idx}].hierarchy_path",
            ))

    return issues


def validate_chunk_records(records: List[Dict[str, Any]], required_fields: List[str]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    for idx, record in enumerate(records):
        for field_name in required_fields:
            if field_name not in record:
                issues.append(ValidationIssue(
                    code="BLOCK_MISSING_MANDATORY_FIELDS",
                    severity="CRITICAL",
                    message=f"Campo ChunkRecord mancante: {field_name}",
                    path=f"[{idx}].{field_name}",
                ))
        if record.get("orphan_flag") is True:
            issues.append(ValidationIssue(
                code="BLOCK_ORPHAN_SEGMENT",
                severity="CRITICAL",
                message="Chunk orfano non ammesso",
                path=f"[{idx}]",
            ))
    return issues


# ============================================================================
# Response package
# ============================================================================

def build_response_package(
    ctx: ParserContext,
    *,
    status: str,
    payload: Dict[str, Any],
    warnings: List[ValidationIssue],
    errors: List[ValidationIssue],
    blocks: List[ValidationIssue],
) -> Dict[str, Any]:
    return {
        "request_id": ctx.request_id,
        "case_id": ctx.case_id,
        "trace_id": ctx.trace_id,
        "api_version": ctx.api_version,
        "responder_module": "B.parser.normattiva.dlgs33",
        "status": status,
        "payload": payload,
        "warnings": [w.to_dict() for w in warnings],
        "errors": [e.to_dict() for e in errors],
        "blocks": [b.to_dict() for b in blocks],
        "timestamp": ctx.timestamp,
    }


# ============================================================================
# Main pipeline
# ============================================================================

def parse_pipeline(ctx: ParserContext) -> Dict[str, Any]:
    warnings: List[ValidationIssue] = []
    errors: List[ValidationIssue] = []
    blocks: List[ValidationIssue] = []

    contract_issues = validate_contract_shape(ctx.contract)
    for issue in contract_issues:
        if issue.severity == "CRITICAL":
            blocks.append(issue)
        else:
            errors.append(issue)

    input_issues, input_paths = validate_input_files(ctx)
    for issue in input_issues:
        if issue.severity == "CRITICAL":
            blocks.append(issue)
        else:
            errors.append(issue)

    if blocks:
        return build_response_package(
            ctx,
            status="BLOCKED",
            payload={},
            warnings=warnings,
            errors=errors,
            blocks=blocks,
        )

    # Main source
    main_html = read_text(input_paths["raw_main_html"])
    main_source_document = build_source_document(ctx, "raw_main_html", main_html)
    articles_file = build_articles_file(ctx, main_source_document, main_html)
    commi_file = build_commi_file(ctx, main_source_document, articles_file)

    # Annex main
    annex_html = read_text(input_paths["raw_annex_html"])
    annex_chunks = build_annex_chunks(ctx, main_source_document, annex_html, "Allegato")

    # Linked source
    linked_html = read_text(input_paths["raw_linked_html"])
    linked_source_document = build_source_document(ctx, "raw_linked_html", linked_html)
    linked_articles_file = build_articles_file(ctx, linked_source_document, linked_html)

    # Linked annex
    linked_annex_html = read_text(input_paths["raw_linked_annex_html"])
    linked_annex_chunks = build_annex_chunks(ctx, linked_source_document, linked_annex_html, "Allegato B")

    # Output validation
    source_required = ctx.contract["field_requirements"]["SourceDocument_required"]
    norm_required = ctx.contract["field_requirements"]["NormUnit_required"]
    chunk_required = ctx.contract["field_requirements"]["ChunkRecord_required"]

    errors.extend(validate_output_wrapper(articles_file, source_required, norm_required))
    errors.extend(validate_output_wrapper(commi_file, source_required, norm_required))
    errors.extend(validate_output_wrapper(linked_articles_file, source_required, norm_required))
    errors.extend(validate_chunk_records(annex_chunks, chunk_required))
    errors.extend(validate_chunk_records(linked_annex_chunks, chunk_required))

    # Forbidden field guardrail
    forbidden_fields = ctx.contract["non_delegation"]["forbidden_output_fields"]
    for payload_obj in [articles_file, commi_file, linked_articles_file, {"records": annex_chunks}, {"records": linked_annex_chunks}]:
        forb = validate_no_forbidden_level_b_fields(payload_obj, forbidden_fields)
        for issue in forb:
            if issue.severity == "CRITICAL":
                blocks.append(issue)
            else:
                errors.append(issue)

    if blocks:
        return build_response_package(
            ctx,
            status="BLOCKED",
            payload={},
            warnings=warnings,
            errors=errors,
            blocks=blocks,
        )

    payload = {
        "source_documents": [
            main_source_document,
            linked_source_document,
        ],
        "norm_units_articles": {
            "dlgs33_2013": articles_file,
            "dlgs97_2016": linked_articles_file,
        },
        "norm_units_commi": {
            "dlgs33_2013": commi_file,
        },
        "chunk_records_annexes": {
            "dlgs33_2013_allegato": annex_chunks,
            "dlgs97_2016_allegato_b": linked_annex_chunks,
        },
        "validation_report": {
            "warnings_count": len(warnings),
            "errors_count": len(errors),
            "blocks_count": len(blocks),
        },
        "coverage_report": {
            "main_source_parsed": True,
            "linked_source_parsed": True,
            "main_annex_parsed": True,
            "linked_annex_parsed": True,
        },
        "trace_technical": {
            "contract_id": ctx.contract["contract_id"],
            "mapping_id": ctx.mapping_rules["mapping_id"],
            "parser_mode": "STUB",
        },
    }

    return build_response_package(
        ctx,
        status="SUCCESS_WITH_WARNINGS" if errors or warnings else "SUCCESS",
        payload=payload,
        warnings=warnings,
        errors=errors,
        blocks=blocks,
    )


def write_contract_outputs(ctx: ParserContext, response_package: Dict[str, Any]) -> None:
    """
    Scrive gli output previsti dal contract.
    In dry-run scrive solo il response package tecnico.
    """
    output_map = {item["output_id"]: ctx.project_root / normalize_relpath(item["path"]) for item in ctx.contract["output_contract"]["main_outputs"]}

    response_path = ctx.project_root / "data" / "cantieri" / "dlgs33_2013" / "DLGS33_2013_parser_response_package.json"
    write_json(response_path, response_package)

    if ctx.dry_run:
        LOGGER.info("Dry-run attivo: output strutturati non scritti.")
        return

    payload = response_package["payload"]
    write_json(output_map["articles_json"], payload["norm_units_articles"]["dlgs33_2013"])
    write_json(output_map["commi_json"], payload["norm_units_commi"]["dlgs33_2013"])
    write_json(output_map["linked_articles_json"], payload["norm_units_articles"]["dlgs97_2016"])
    write_jsonl(output_map["annex_chunks_jsonl"], payload["chunk_records_annexes"]["dlgs33_2013_allegato"])
    write_jsonl(output_map["linked_annex_chunks_jsonl"], payload["chunk_records_annexes"]["dlgs97_2016_allegato_b"])


# ============================================================================
# CLI
# ============================================================================

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="D.Lgs. 33/2013 parser skeleton agganciato al contract v1")
    parser.add_argument("--project-root", default="", help="Root del progetto normattiva_rag_sprint1")
    parser.add_argument("--request-id", default="req_dlgs33_parser_001")
    parser.add_argument("--case-id", default="case_dlgs33_2013")
    parser.add_argument("--trace-id", default="trace_dlgs33_parser_001")
    parser.add_argument("--caller-module", default="manual.cli")
    parser.add_argument("--dry-run", action="store_true", help="Valida e genera il response package senza scrivere gli output strutturati")
    parser.add_argument("--allow-placeholder-inputs", action="store_true", help="Consente il parsing anche su file placeholder tecnici")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s | %(name)s | %(message)s"
    )

    try:
        ctx = build_context(args)
        response_package = parse_pipeline(ctx)
        write_contract_outputs(ctx, response_package)

        status = response_package["status"]
        print(json.dumps({
            "status": status,
            "response_package": "data/cantieri/dlgs33_2013/DLGS33_2013_parser_response_package.json",
            "warnings": len(response_package["warnings"]),
            "errors": len(response_package["errors"]),
            "blocks": len(response_package["blocks"]),
        }, ensure_ascii=False, indent=2))

        return 0 if status in {"SUCCESS", "SUCCESS_WITH_WARNINGS"} else 2

    except ParserBlockedError as exc:
        issue = blocked_issue_from_exception(exc)
        print(json.dumps({
            "status": "BLOCKED",
            "blocks": [issue.to_dict()],
        }, ensure_ascii=False, indent=2))
        return 2

    except Exception as exc:
        print(json.dumps({
            "status": "ERROR",
            "message": str(exc),
        }, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
