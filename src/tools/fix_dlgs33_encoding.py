from pathlib import Path

INPUT_FILE = Path("data/normalized/main_text/dlgs33_2013_clean.txt")
OUTPUT_FILE = Path("data/normalized/main_text/dlgs33_2013_clean_fixed.txt")


def load_text() -> str:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file non trovato: {INPUT_FILE}")
    return INPUT_FILE.read_text(encoding="utf-8", errors="replace")


def try_fix_mojibake_cp1252(text: str) -> str:
    """
    Caso tipico:
    testo UTF-8 interpretato come cp1252.
    Esempio:
    Ã¨ -> è
    pubblicitÃ  -> pubblicità
    """
    try:
        return text.encode("cp1252").decode("utf-8")
    except Exception:
        return text


def cleanup(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\x00", "")
    return text


def main() -> None:
    text = load_text()
    fixed = try_fix_mojibake_cp1252(text)
    fixed = cleanup(fixed)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(fixed, encoding="utf-8")

    print(f"File scritto: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()