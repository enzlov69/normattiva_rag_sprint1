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


def try_fix_mojibake_cp1252(text: str) -> str:
    try:
        return text.encode("cp1252").decode("utf-8")
    except Exception:
        return text


def try_fix_mojibake_latin1(text: str) -> str:
    try:
        return text.encode("latin1").decode("utf-8")
    except Exception:
        return text


def has_suspect_mojibake(text: str) -> bool:
    suspects = ("Ã", "Â", "â€", "â€™", "â€œ", "â€\x9d", "â€“", "â€”")
    return any(s in text for s in suspects)


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def fix_text(text: str) -> str:
    if not isinstance(text, str):
        return text

    original = text
    text = clean_text(text)

    if has_suspect_mojibake(text):
        fixed_cp1252 = try_fix_mojibake_cp1252(text)
        if fixed_cp1252 != text and fixed_cp1252.count("Ã") < text.count("Ã"):
            text = fixed_cp1252

        if has_suspect_mojibake(text):
            fixed_latin1 = try_fix_mojibake_latin1(text)
            if fixed_latin1 != text and fixed_latin1.count("Ã") < text.count("Ã"):
                text = fixed_latin1

    return text if text else original


def fix_json_obj(obj):
    if isinstance(obj, dict):
        return {k: fix_json_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [fix_json_obj(v) for v in obj]
    if isinstance(obj, str):
        return fix_text(obj)
    return obj


def process_json_dir(target_dir: Path) -> tuple[int, int]:
    processed = 0
    changed = 0

    if not target_dir.exists():
        return processed, changed

    for json_file in sorted(target_dir.glob("*.json")):
        try:
            original_text = json_file.read_text(encoding="utf-8", errors="replace")
            payload = json.loads(original_text)
            fixed_payload = fix_json_obj(payload)
            new_text = json.dumps(fixed_payload, ensure_ascii=False, indent=2)

            processed += 1
            if new_text != original_text:
                json_file.write_text(new_text, encoding="utf-8")
                changed += 1
                print(f"[FIX] {json_file}")
            else:
                print(f"[OK] {json_file}")
        except Exception as e:
            print(f"[WARN] {json_file}: {e}")

    return processed, changed


def main() -> None:
    cfg = load_config()
    articles_dir = BASE_DIR / cfg["articles_out_dir"]
    commi_dir = BASE_DIR / cfg["commi_out_dir"]
    logs_dir = BASE_DIR / cfg["logs_dir"]

    logs_dir.mkdir(parents=True, exist_ok=True)

    ts = now_utc()

    print(f"[INFO] fix encoding dataset: {cfg['dataset_id']} {cfg['versione']}")
    print(f"[INFO] directory articoli: {articles_dir}")
    print(f"[INFO] directory commi: {commi_dir}")

    art_processed, art_changed = process_json_dir(articles_dir)
    com_processed, com_changed = process_json_dir(commi_dir)

    summary = {
        "timestamp": ts,
        "dataset_id": cfg["dataset_id"],
        "versione": cfg["versione"],
        "articles_dir": str(articles_dir),
        "commi_dir": str(commi_dir),
        "articles_processed": art_processed,
        "articles_changed": art_changed,
        "commi_processed": com_processed,
        "commi_changed": com_changed,
        "total_processed": art_processed + com_processed,
        "total_changed": art_changed + com_changed
    }

    summary_file = logs_dir / f"{cfg['dataset_id']}_{cfg['versione']}_encoding_fix_summary.json"
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] file processati: {summary['total_processed']}")
    print(f"[OK] file modificati: {summary['total_changed']}")
    print(f"[INFO] log riepilogo: {summary_file}")


if __name__ == "__main__":
    main()