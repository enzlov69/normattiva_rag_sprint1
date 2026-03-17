from pathlib import Path
import json
import re
from datetime import datetime, UTC

BASE_DIR = Path(__file__).resolve().parents[2]

ARTICLES_DIR = BASE_DIR / "data" / "normalized" / "norm_units" / "dlgs33_2013_vigente_articles"
OUT_DIR = BASE_DIR / "data" / "normalized" / "norm_units" / "dlgs33_2013_vigente_commi"
LOG_DIR = BASE_DIR / "data" / "logs"

SUMMARY_LOG = LOG_DIR / "dlgs33_vigente_commi_summary.json"
FAIL_LOG = LOG_DIR / "dlgs33_vigente_commi_failures.json"


def now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_article_files() -> list[Path]:
    if not ARTICLES_DIR.exists():
        raise FileNotFoundError(f"Directory articoli non trovata: {ARTICLES_DIR}")
    files = sorted(ARTICLES_DIR.glob("art_*.json"))
    if not files:
        raise FileNotFoundError(f"Nessun file articolo trovato in: {ARTICLES_DIR}")
    return files


def parse_article_token_from_filename(path: Path) -> str:
    stem = path.stem  # es. art_005_bis
    m = re.fullmatch(r"art_(\d{3})(?:_([a-z]+))?", stem)
    if not m:
        raise ValueError(f"Nome file articolo non valido: {path.name}")

    num = str(int(m.group(1)))
    suffix = m.group(2)

    if suffix:
        return f"{num}-{suffix}"
    return num


def article_file_stem(path: Path) -> str:
    return path.stem  # es. art_005_bis


def split_commi(testo_unita: str) -> list[dict]:
    """
    Divide il testo dell'articolo in commi.
    Riconosce:
    1.
    1-bis.
    1-ter.
    2-bis.
    sia con testo sulla stessa riga che su righe successive.
    """
    text = clean_text(testo_unita)
    if not text:
        return []

    # Regex robusta:
    # prende un marker comma a inizio riga e tutto il testo fino al comma successivo
    pattern = re.compile(
        r"(?ms)^\s*(\d+(?:-[a-z]+)?)\.\s*(.*?)(?=^\s*\d+(?:-[a-z]+)?\.|\Z)"
    )

    commi = []
    for m in pattern.finditer(text):
        comma_num = m.group(1).strip()
        comma_body = clean_text(m.group(2))
        if comma_body:
            commi.append({
                "comma": comma_num,
                "testo": comma_body
            })

    # fallback prudenziale: se non trova marker, tratta tutto come comma 1
    if not commi and text:
        commi.append({
            "comma": "1",
            "testo": text
        })

    return commi


def save_comma_json(
    source_article_file: Path,
    article_payload: dict,
    article_token: str,
    comma_num: str,
    testo_comma: str,
    ts: str,
    position_index: int,
) -> None:
    article_stem = article_file_stem(source_article_file)  # es. art_005_bis
    comma_file_token = comma_num.replace("-", "_")         # es. 2-bis -> 2_bis

    norm_unit_id = f"dlgs33_2013_{article_stem}_com_{comma_file_token}".replace("art_", "art_")
    record_id = f"nu_{norm_unit_id}"

    payload = {
        "record_id": record_id,
        "record_type": "NormUnit",
        "norm_unit_id": norm_unit_id,
        "source_id": "normattiva_dlgs33_2013_vigente",
        "unit_type": "comma",
        "articolo": article_token,
        "comma": comma_num,
        "lettera": "",
        "numero": "",
        "allegato": "",
        "rubrica": article_payload.get("rubrica", ""),
        "testo_unita": testo_comma,
        "position_index": position_index,
        "hierarchy_path": f"D.Lgs. 33/2013 vigente > Art. {article_token} > Comma {comma_num}",
        "cross_reference_ids": [],
        "vigenza_ref_id": "",
        "norm_unit_status": "ACTIVE_STRUCTURED",
        "created_at": ts,
        "updated_at": ts,
        "schema_version": "2.0",
        "record_version": 1,
        "source_layer": "B",
        "trace_id": "trace_dlgs33_vigente_commi_v2",
        "active_flag": True,
    }

    out_file = OUT_DIR / f"{article_stem}_com_{comma_file_token}.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # pulizia output vecchio
    for old in OUT_DIR.glob("*.json"):
        old.unlink()

    ts = now_utc()
    failures = []
    article_files = load_article_files()

    total_articles = 0
    total_commi = 0
    global_position_index = 1

    print(f"[INFO] directory articoli input: {ARTICLES_DIR}")
    print(f"[INFO] directory commi output: {OUT_DIR}")
    print(f"[INFO] file articoli trovati: {len(article_files)}")

    for article_file in article_files:
        try:
            article_payload = json.loads(article_file.read_text(encoding="utf-8"))
            article_token = article_payload.get("articolo") or parse_article_token_from_filename(article_file)
            testo_unita = article_payload.get("testo_unita", "")

            commi = split_commi(testo_unita)
            if not commi:
                raise ValueError(f"Nessun comma rilevato in {article_file.name}")

            total_articles += 1

            for comma in commi:
                save_comma_json(
                    source_article_file=article_file,
                    article_payload=article_payload,
                    article_token=article_token,
                    comma_num=comma["comma"],
                    testo_comma=comma["testo"],
                    ts=ts,
                    position_index=global_position_index,
                )
                global_position_index += 1
                total_commi += 1

            print(f"[OK] {article_file.name} -> art. {article_token} -> commi: {len(commi)}")

        except Exception as e:
            failures.append({
                "file": article_file.name,
                "error": str(e),
            })
            print(f"[WARN] {article_file.name}: {e}")

    SUMMARY_LOG.write_text(json.dumps({
        "timestamp": ts,
        "articles_input_dir": str(ARTICLES_DIR),
        "commi_output_dir": str(OUT_DIR),
        "articles_processed": total_articles,
        "commi_generated": total_commi,
        "failures_count": len(failures),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    FAIL_LOG.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] articoli processati: {total_articles}")
    print(f"[OK] commi generati: {total_commi}")
    print(f"[INFO] log riepilogo: {SUMMARY_LOG}")
    print(f"[INFO] log errori: {FAIL_LOG}")


if __name__ == "__main__":
    main()