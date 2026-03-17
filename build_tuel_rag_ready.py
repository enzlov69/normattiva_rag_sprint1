
"""
build_tuel_rag_ready.py

Costruisce un file unico TUEL pronto per il RAG a partire dai JSON
presenti in data/raw/tuel_stable_crawler/articles/.

Funzioni:
- legge tutti i file .json degli articoli
- normalizza etichetta articolo e suffisso
- estrae una rubrica minima dal testo
- ordina gli articoli nel corretto ordine normativo
- produce:
    - data/processed/tuel/tuel_rag_ready.json
    - data/processed/tuel/tuel_rag_ready.ndjson

Uso:
    python build_tuel_rag_ready.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path


SOURCE_DIR = Path("data/raw/tuel_stable_crawler/articles")
OUT_DIR = Path("data/processed/tuel")
OUT_JSON = OUT_DIR / "tuel_rag_ready.json"
OUT_NDJSON = OUT_DIR / "tuel_rag_ready.ndjson"

OUT_DIR.mkdir(parents=True, exist_ok=True)

SUFFIX_ORDER = {
    None: 0,
    "bis": 1,
    "ter": 2,
    "quater": 3,
    "quinquies": 4,
    "sexies": 5,
    "septies": 6,
    "octies": 7,
    "novies": 8,
    "decies": 9,
    "undecies": 10,
    "duodecies": 11,
    "terdecies": 12,
    "quaterdecies": 13,
    "quinquiesdecies": 14,
}

ARTICLE_LABEL_RE = re.compile(
    r"^(?P<num>\d+)(?:\s+(?P<suf>bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|undecies|duodecies|terdecies|quaterdecies|quinquiesdecies))?$",
    flags=re.IGNORECASE,
)


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_article_label(label: str):
    label = clean_text(label)
    m = ARTICLE_LABEL_RE.match(label)
    if not m:
        return None, None
    num = int(m.group("num"))
    suf = m.group("suf").lower() if m.group("suf") else None
    return num, suf


def normalize_article_citation(label: str) -> str:
    num, suf = parse_article_label(label)
    if num is None:
        return label
    return f"{num}" if not suf else f"{num}-{suf}"


def extract_rubrica(text: str, raw_label: str) -> str:
    if not text:
        return ""

    lines = [clean_text(x) for x in text.splitlines()]
    lines = [x for x in lines if x]

    if not lines:
        return ""

    # caso tipico:
    # Articolo 2
    # Ambito di applicazione
    # 1. Ai fini...
    raw_label_clean = clean_text(raw_label).lower()
    article_variants = {
        raw_label_clean,
        f"articolo {raw_label_clean}",
        f"art. {raw_label_clean}",
    }

    for i, line in enumerate(lines[:6]):
        if line.lower() in article_variants:
            if i + 1 < len(lines):
                nxt = lines[i + 1]
                if not re.match(r"^\d+[.)]", nxt) and not re.match(r"^\d+\s", nxt):
                    return nxt

    # fallback: cerca la prima riga non numerata dopo le prime righe
    for line in lines[:8]:
        low = line.lower()
        if low in article_variants:
            continue
        if re.match(r"^\d+[.)]", line):
            continue
        if re.match(r"^\d+\s", line):
            continue
        if low.startswith("articolo "):
            continue
        return line

    return ""


def build_record(path: Path, payload: dict) -> dict | None:
    raw_label = payload.get("article_label_raw") or payload.get("article_label") or ""
    raw_label = clean_text(raw_label)

    article_number_base, article_suffix = parse_article_label(raw_label)
    if article_number_base is None:
        return None

    text = clean_text(payload.get("text", ""))
    rubrica = extract_rubrica(text, raw_label)

    source_url = payload.get("source_url", "")
    index_order = payload.get("index_order")

    return {
        "norma": "D.Lgs. 267/2000",
        "titolo_norma": "Testo unico delle leggi sull'ordinamento degli enti locali",
        "sigla_norma": "TUEL",
        "fonte_tipo": "Normattiva",
        "codice_redazionale": "000G0304",
        "data_gazzetta": "2000-09-28",
        "article_label_raw": raw_label,
        "article_number_base": article_number_base,
        "article_suffix": article_suffix,
        "articolo": normalize_article_citation(raw_label),
        "rubrica": rubrica,
        "testo": text,
        "source_url": source_url,
        "index_order": index_order,
        "source_file": str(path).replace("\\", "/"),
        "chunk_source": "TUEL",
    }


def dedupe_records(records: list[dict]) -> list[dict]:
    best = {}
    for rec in records:
        key = rec["articolo"]
        current = best.get(key)
        if current is None:
            best[key] = rec
            continue

        cur_len = len(current.get("testo", ""))
        new_len = len(rec.get("testo", ""))

        if new_len > cur_len:
            best[key] = rec
            continue

        cur_order = current.get("index_order")
        new_order = rec.get("index_order")
        try:
            cur_order = int(cur_order) if cur_order is not None else 999999
        except Exception:
            cur_order = 999999
        try:
            new_order = int(new_order) if new_order is not None else 999999
        except Exception:
            new_order = 999999

        if new_order < cur_order:
            best[key] = rec

    result = list(best.values())
    result.sort(
        key=lambda r: (
            r["article_number_base"],
            SUFFIX_ORDER.get(r["article_suffix"], 99),
            r["articolo"],
        )
    )
    return result


def main():
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"Cartella sorgente non trovata: {SOURCE_DIR}")

    files = sorted(SOURCE_DIR.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"Nessun file JSON trovato in: {SOURCE_DIR}")

    records = []
    skipped = []

    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            record = build_record(path, payload)
            if record is None:
                skipped.append(path.name)
                continue
            records.append(record)
        except Exception:
            skipped.append(path.name)

    records = dedupe_records(records)

    output = {
        "norma": "D.Lgs. 267/2000",
        "titolo_norma": "Testo unico delle leggi sull'ordinamento degli enti locali",
        "sigla_norma": "TUEL",
        "fonte_tipo": "Normattiva",
        "article_count": len(records),
        "articles": records,
        "skipped_files": skipped,
    }

    OUT_JSON.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with OUT_NDJSON.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"File letti: {len(files)}")
    print(f"Articoli utili: {len(records)}")
    print(f"File saltati: {len(skipped)}")
    print(f"JSON finale: {OUT_JSON}")
    print(f"NDJSON finale: {OUT_NDJSON}")

    for rec in records[:10]:
        print(f"{rec['articolo']} | {rec['rubrica']}")


if __name__ == "__main__":
    main()
