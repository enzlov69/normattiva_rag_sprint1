from pathlib import Path
import json
import re
from datetime import datetime, UTC

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = BASE_DIR / "src" / "tools" / "normattiva_bootstrap_config.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def article_file_stem(path: Path) -> str:
    return path.stem


def split_commi(testo_unita: str) -> list[dict]:
    text = clean_text(testo_unita)
    if not text:
        return []
    pattern = re.compile(r"(?ms)^\s*(\d+(?:-[a-z]+)?)\.\s*(.*?)(?=^\s*\d+(?:-[a-z]+)?\.|\Z)")
    commi = []
    for m in pattern.finditer(text):
        comma_num = m.group(1).strip()
        comma_body = clean_text(m.group(2))
        if comma_body:
            commi.append({"comma": comma_num, "testo": comma_body})
    if not commi and text:
        commi.append({"comma": "1", "testo": text})
    return commi


def save_comma_json(cfg: dict, source_article_file: Path, article_payload: dict, article_token: str, comma_num: str, testo_comma: str, ts: str, position_index: int, out_dir: Path):
    article_stem = article_file_stem(source_article_file)
    comma_file_token = comma_num.replace("-", "_")
    norm_unit_id = f"{cfg['dataset_id']}_{article_stem}_com_{comma_file_token}"
    payload = {
        "record_id": f"nu_{norm_unit_id}",
        "record_type": "NormUnit",
        "norm_unit_id": norm_unit_id,
        "source_id": f"normattiva_{cfg['dataset_id']}_{cfg['versione']}",
        "unit_type": "comma",
        "articolo": article_token,
        "comma": comma_num,
        "lettera": "",
        "numero": "",
        "allegato": "",
        "rubrica": article_payload.get("rubrica", ""),
        "testo_unita": testo_comma,
        "position_index": position_index,
        "hierarchy_path": f"{cfg['atto_tipo']} {cfg['atto_numero']}/{cfg['atto_anno']} {cfg['versione']} > Art. {article_token} > Comma {comma_num}",
        "cross_reference_ids": [],
        "vigenza_ref_id": "",
        "norm_unit_status": "ACTIVE_STRUCTURED",
        "created_at": ts,
        "updated_at": ts,
        "schema_version": "2.0",
        "record_version": 1,
        "source_layer": "B",
        "trace_id": f"trace_{cfg['dataset_id']}_{cfg['versione']}_commi_v1",
        "active_flag": True,
    }
    out_file = out_dir / f"{article_stem}_com_{comma_file_token}.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    cfg = load_config()
    articles_dir = BASE_DIR / cfg["articles_out_dir"]
    out_dir = BASE_DIR / cfg["commi_out_dir"]
    logs_dir = BASE_DIR / cfg["logs_dir"]
    summary_log = logs_dir / f"{cfg['dataset_id']}_{cfg['versione']}_commi_summary.json"
    fail_log = logs_dir / f"{cfg['dataset_id']}_{cfg['versione']}_commi_failures.json"

    out_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    for old in out_dir.glob("*.json"):
        old.unlink()

    article_files = sorted(articles_dir.glob("art_*.json"))
    if not article_files:
        raise FileNotFoundError(f"Nessun file articolo trovato in: {articles_dir}")

    ts = now_utc()
    failures = []
    total_articles = 0
    total_commi = 0
    global_position_index = 1

    print(f"[INFO] directory articoli input: {articles_dir}")
    print(f"[INFO] directory commi output: {out_dir}")
    print(f"[INFO] file articoli trovati: {len(article_files)}")

    for article_file in article_files:
        try:
            article_payload = json.loads(article_file.read_text(encoding="utf-8"))
            article_token = article_payload.get("articolo")
            testo_unita = article_payload.get("testo_unita", "")
            commi = split_commi(testo_unita)
            if not commi:
                raise ValueError(f"Nessun comma rilevato in {article_file.name}")
            total_articles += 1
            for comma in commi:
                save_comma_json(cfg, article_file, article_payload, article_token, comma["comma"], comma["testo"], ts, global_position_index, out_dir)
                global_position_index += 1
                total_commi += 1
            print(f"[OK] {article_file.name} -> art. {article_token} -> commi: {len(commi)}")
        except Exception as e:
            failures.append({"file": article_file.name, "error": str(e)})
            print(f"[WARN] {article_file.name}: {e}")

    summary_log.write_text(json.dumps({
        "timestamp": ts,
        "articles_input_dir": str(articles_dir),
        "commi_output_dir": str(out_dir),
        "articles_processed": total_articles,
        "commi_generated": total_commi,
        "failures_count": len(failures),
        "dataset_id": cfg["dataset_id"],
        "versione": cfg["versione"]
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    fail_log.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] articoli processati: {total_articles}")
    print(f"[OK] commi generati: {total_commi}")
    print(f"[INFO] log riepilogo: {summary_log}")
    print(f"[INFO] log errori: {fail_log}")


if __name__ == "__main__":
    main()
