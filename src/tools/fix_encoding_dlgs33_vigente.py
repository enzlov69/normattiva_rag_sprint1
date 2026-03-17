from pathlib import Path
import json
import re
from datetime import datetime, UTC

BASE_DIR = Path(__file__).resolve().parents[2]

TARGET_DIRS = [
    BASE_DIR / "data" / "normalized" / "norm_units" / "dlgs33_2013_vigente_articles",
    BASE_DIR / "data" / "normalized" / "norm_units" / "dlgs33_2013_vigente_commi",
]

LOG_DIR = BASE_DIR / "data" / "logs"
SUMMARY_LOG = LOG_DIR / "dlgs33_vigente_encoding_fix_summary.json"


def now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def mojibake_score(text: str) -> int:
    bad = ["Ã", "Â", "â€", "â€™", "â€œ", "â€\x9d", "â€“", "â€”", "â€¦", " "]
    return sum(text.count(x) for x in bad)


def force_repair(text: str) -> str:
    if not isinstance(text, str) or not text:
        return text

    current = text

    # fino a 3 passaggi, ma solo se migliora
    for _ in range(3):
        candidates = [current]

        for enc in ("latin1", "cp1252"):
            try:
                repaired = current.encode(enc, errors="ignore").decode("utf-8", errors="ignore")
                candidates.append(repaired)
            except Exception:
                pass

        best = min(candidates, key=mojibake_score)

        if best == current:
            break
        if mojibake_score(best) >= mojibake_score(current):
            break

        current = best

    # pulizie residue tipiche
    current = current.replace("â€™", "'")
    current = current.replace("â€œ", '"')
    current = current.replace("â€\x9d", '"')
    current = current.replace("â€“", "-")
    current = current.replace("â€”", "-")
    current = current.replace("â€¦", "...")
    current = current.replace("\ufeff", "")
    current = current.replace("\xa0", " ")

    current = re.sub(r"[ \t]+", " ", current)
    current = re.sub(r"\r", "", current)
    current = re.sub(r"\n{3,}", "\n\n", current)
    return current.strip()


def repair_obj(obj):
    if isinstance(obj, dict):
        return {k: repair_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [repair_obj(x) for x in obj]
    if isinstance(obj, str):
        return force_repair(obj)
    return obj


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    files = []
    for d in TARGET_DIRS:
        if not d.exists():
            raise FileNotFoundError(f"Directory non trovata: {d}")
        files.extend(sorted(d.glob("*.json")))

    processed = 0
    changed = 0

    print(f"[INFO] file da controllare: {len(files)}")

    for file_path in files:
        processed += 1

        original_text = file_path.read_text(encoding="utf-8", errors="replace")
        original_obj = json.loads(original_text)

        repaired_obj = repair_obj(original_obj)
        new_text = json.dumps(repaired_obj, ensure_ascii=False, indent=2)

        if new_text != original_text:
            file_path.write_text(new_text, encoding="utf-8")
            changed += 1
            print(f"[FIX] {file_path.name}")
        else:
            print(f"[OK] {file_path.name}")

    summary = {
        "timestamp": now_utc(),
        "target_dirs": [str(p) for p in TARGET_DIRS],
        "files_processed": processed,
        "files_changed": changed,
        "files_unchanged": processed - changed,
    }

    SUMMARY_LOG.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] file processati: {processed}")
    print(f"[OK] file modificati: {changed}")
    print(f"[INFO] log riepilogo: {SUMMARY_LOG}")


if __name__ == "__main__":
    main()