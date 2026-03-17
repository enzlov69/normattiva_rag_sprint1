from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

DEFAULT_ATTO_TIPO = "Decreto legislativo"
DEFAULT_ATTO_NUMERO = "33"
DEFAULT_ATTO_ANNO = "2013"
DEFAULT_TITOLO = (
    "Riordino della disciplina riguardante il diritto di accesso civico e gli obblighi di "
    "pubblicità, trasparenza e diffusione di informazioni da parte delle pubbliche amministrazioni"
)
DEFAULT_URI = "https://www.normattiva.it/"
DEFAULT_COLLECTION_ARTICLES = "normattiva_dlgs33_2013_vigente_articles"
DEFAULT_COLLECTION_COMMI = "normattiva_dlgs33_2013_vigente_commi"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_PERSIST_DIR = "data/chroma"
DEFAULT_ARTICLES_DIR = "data/normalized/norm_units/dlgs33_2013_vigente_articles"
DEFAULT_COMMI_DIR = "data/normalized/norm_units/dlgs33_2013_vigente_commi"
DEFAULT_MANIFEST_PATH = "data/manifests/dlgs33_2013/dlgs33_2013_vigente_ingest_manifest.json"
DEFAULT_LOG_DIR = "data/logs"
EXPECTED_ARTICLES = 62
EXPECTED_COMMI = 190


@dataclass(frozen=True)
class ManifestInfo:
    manifest_path: Path
    articles_dir: Path
    commi_dir: Path
    log_dir: Path
    persist_dir: Path
    collection_articles: str
    collection_commi: str
    embedding_model: str


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def iter_json_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(p for p in folder.glob("*.json") if p.is_file())


def first_nonempty(*values: Any, default: str = "") -> str:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip():
            return value.strip()
        if not isinstance(value, str):
            text = str(value).strip()
            if text:
                return text
    return default


def safe_meta_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return " | ".join(str(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def normalize_record(raw: dict[str, Any], *, source_kind: str, fallback_id: str) -> tuple[str, str, dict[str, Any]]:
    unit_id = first_nonempty(
        raw.get("norm_unit_id"),
        raw.get("record_id"),
        raw.get("id"),
        fallback_id,
    )
    articolo = first_nonempty(raw.get("articolo"), raw.get("art"), default="")
    comma = first_nonempty(raw.get("comma"), raw.get("co"), default="")
    lettera = first_nonempty(raw.get("lettera"), default="")
    numero = first_nonempty(raw.get("numero"), default="")
    allegato = first_nonempty(raw.get("allegato"), default="")
    rubrica = first_nonempty(raw.get("rubrica"), raw.get("titolo_articolo"), default="")
    testo = first_nonempty(raw.get("testo_unita"), raw.get("testo"), raw.get("chunk_text"), default="")
    unit_type = first_nonempty(raw.get("unit_type"), default=("articolo" if source_kind == "articles" else "comma"))
    uri_ufficiale = first_nonempty(raw.get("uri_ufficiale"), raw.get("uri_normattiva"), default=DEFAULT_URI)
    stato_vigenza = first_nonempty(raw.get("stato_vigenza"), raw.get("vigore_status"), default="VIGENTE_VERIFICATA")
    stato_verifica_fonte = first_nonempty(raw.get("stato_verifica_fonte"), default="VERIFIED")
    hierarchy_path = first_nonempty(raw.get("hierarchy_path"), default="")
    position_index = first_nonempty(raw.get("position_index"), default="")

    header_parts = []
    if articolo:
        header_parts.append(f"Articolo {articolo}")
    if comma:
        header_parts.append(f"comma {comma}")
    if rubrica:
        header_parts.append(rubrica)
    header = " — ".join(header_parts)
    document = f"{header}\n\n{testo}" if header else testo

    metadata = {
        "source_kind": source_kind,
        "record_type": "NormUnit",
        "unit_type": unit_type,
        "atto_tipo": first_nonempty(raw.get("atto_tipo"), default=DEFAULT_ATTO_TIPO),
        "atto_numero": first_nonempty(raw.get("atto_numero"), default=DEFAULT_ATTO_NUMERO),
        "atto_anno": first_nonempty(raw.get("atto_anno"), default=DEFAULT_ATTO_ANNO),
        "titolo_atto": first_nonempty(raw.get("titolo"), raw.get("titolo_atto"), default=DEFAULT_TITOLO),
        "fonte": first_nonempty(raw.get("fonte"), raw.get("fonte_ufficiale"), default="Normattiva"),
        "uri_ufficiale": uri_ufficiale,
        "stato_vigenza": stato_vigenza,
        "stato_verifica_fonte": stato_verifica_fonte,
        "norm_unit_id": unit_id,
        "articolo": articolo,
        "comma": comma,
        "lettera": lettera,
        "numero": numero,
        "allegato": allegato,
        "rubrica": rubrica,
        "hierarchy_path": hierarchy_path,
        "position_index": position_index,
        "source_layer": "B",
        "collection_source": (
            DEFAULT_COLLECTION_ARTICLES if source_kind == "articles" else DEFAULT_COLLECTION_COMMI
        ),
    }
    metadata = {k: safe_meta_value(v) for k, v in metadata.items()}
    return unit_id, document, metadata


def load_manifest_info(manifest_path: str | Path = DEFAULT_MANIFEST_PATH) -> tuple[dict[str, Any], ManifestInfo]:
    manifest_file = Path(manifest_path)
    manifest = load_json(manifest_file)
    info = ManifestInfo(
        manifest_path=manifest_file,
        articles_dir=Path(manifest["input"]["articles_dir"]),
        commi_dir=Path(manifest["input"]["commi_dir"]),
        log_dir=Path(DEFAULT_LOG_DIR),
        persist_dir=Path(manifest["vectorstore"]["persist_dir"]),
        collection_articles=manifest["collections"]["articles"],
        collection_commi=manifest["collections"]["commi"],
        embedding_model=manifest["vectorstore"]["embedding_model"],
    )
    return manifest, info


def summarize_folder(folder: Path) -> dict[str, Any]:
    files = iter_json_files(folder)
    total = len(files)
    missing_text = 0
    missing_uri = 0
    sample_ids: list[str] = []
    for idx, path in enumerate(files):
        raw = load_json(path)
        _, document, metadata = normalize_record(raw, source_kind="articles", fallback_id=path.stem)
        if not document.strip():
            missing_text += 1
        if not str(metadata.get("uri_ufficiale", "")).strip():
            missing_uri += 1
        if idx < 5:
            sample_ids.append(str(metadata.get("norm_unit_id") or path.stem))
    return {
        "folder": str(folder),
        "files": total,
        "missing_text": missing_text,
        "missing_uri": missing_uri,
        "sample_ids": sample_ids,
    }


def chunks(items: list[Any], size: int) -> Iterable[list[Any]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]
