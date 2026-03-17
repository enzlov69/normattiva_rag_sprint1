import json
import re
from pathlib import Path

INPUT_FILE = Path("data/normalized/main_text/dlgs33_2013_clean.txt")
OUTPUT_FILE = Path("data/processed/dlgs33_articles.json")


def load_text() -> str:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file non trovato: {INPUT_FILE}")
    return INPUT_FILE.read_text(encoding="utf-8", errors="replace")


def fix_mojibake(text: str) -> str:
    """
    Ripara il caso tipico:
    UTF-8 interpretato come cp1252.
    """
    try:
        return text.encode("cp1252").decode("utf-8")
    except Exception:
        return text


def remove_editorial_blocks(text: str) -> str:
    """
    Rimuove blocchi redazionali che non fanno parte del testo normativo:
    - righe con solo (5), (12), ecc.
    - separatori ------
    - blocchi AGGIORNAMENTO fino al prossimo articolo o fine testo
    """
    text = re.sub(r"(?m)^\(\d+\)\s*$", "", text)
    text = re.sub(r"(?m)^-+\s*$", "", text)

    text = re.sub(
        r"(?ims)^AGGIORNAMENTO\s*\(\d+\).*?(?=^(?:Art\.|Articolo)\s+\d+|\Z)",
        "",
        text,
    )

    text = re.sub(
        r"(?ims)^AGGIORNAMENTO\b.*?(?=^(?:Art\.|Articolo)\s+\d+|\Z)",
        "",
        text,
    )

    return text


def strip_annexes(text: str) -> str:
    """
    Tronca il testo prima dell'inizio degli allegati.
    Serve a evitare che l'ultimo articolo inglobi:
    - Allegato
    - ALLEGATO A
    - ALLEGATO B
    """
    match = re.search(
        r"(?im)^(Allegato|ALLEGATO(?:\s+[A-Z])?(?:\s*\(.*\))?)\b",
        text
    )
    if match:
        return text[:match.start()].rstrip()
    return text


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = fix_mojibake(text)
    text = remove_editorial_blocks(text)

    # Mantiene il contenuto delle doppie parentesi ma rimuove i marcatori
    text = text.replace("((", "").replace("))", "")

    # Tronca prima degli allegati
    text = strip_annexes(text)

    # Compatta spazi multipli
    text = re.sub(r"[ \t]+", " ", text)

    # Compatta linee vuote multiple
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_articles(text: str) -> list[dict]:
    """
    Intercetta intestazioni del tipo:
    - Art. 1
    - Art. 2-bis
    - Articolo 1
    - Articolo 14-ter
    """
    text = normalize_text(text)

    pattern = r"(?im)^(Art\.|Articolo)\s+(\d+(?:-[a-z]+)?)\s*$"
    matches = list(re.finditer(pattern, text))

    articles = []

    if not matches:
        return articles

    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)

        block = text[start:end].strip()
        header = match.group(0).strip()
        article_number = match.group(2).strip()

        body_lines = block.splitlines()
        body = "\n".join(body_lines[1:]).strip() if len(body_lines) > 1 else ""

        articles.append({
            "record_type": "NormUnit",
            "unit_type": "articolo",
            "articolo": article_number,
            "header": header,
            "text": body,
            "source_id": "dlgs33_2013_vigente",
            "norma": {
                "tipo": "Decreto legislativo",
                "numero": "33",
                "anno": "2013"
            }
        })

    return articles


def build_output(records: list[dict]) -> dict:
    return {
        "file_type": "norm_units",
        "unit_scope": "articles",
        "source_document": {
            "atto": "D.Lgs. 33/2013",
            "versione": "vigente"
        },
        "records": records
    }


def main() -> None:
    print("Caricamento testo...")
    text = load_text()

    print("Segmentazione articoli...")
    articles = split_articles(text)

    print(f"Articoli trovati: {len(articles)}")

    output = build_output(articles)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"File scritto: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()