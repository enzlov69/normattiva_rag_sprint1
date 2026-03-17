from pathlib import Path
import json
import re
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_HTML = BASE_DIR / "data" / "raw" / "dlgs33_2013" / "vigente" / "dlgs33_2013_vigente_normattiva.html"
OUTPUT_JSON = BASE_DIR / "data" / "processed" / "dlgs33_2013_vigente_article_index.json"
OUTPUT_TXT = BASE_DIR / "data" / "processed" / "dlgs33_2013_vigente_article_index.txt"


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_article_id(raw: str) -> str:
    raw = raw.strip().lower()
    raw = raw.replace("art.", "").replace("articolo", "").strip()
    raw = raw.replace(" ", "")
    return raw


def extract_article_headers(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")

    headers = soup.find_all("h2", class_="article-num-akn")

    articles = []
    for h in headers:
        text = clean_text(h.get_text(" ", strip=True))
        if not text:
            continue

        # Esempi:
        # Art. 1
        # Art. 15-bis
        # Art. 5-ter
        m = re.match(r"(?i)^Art\.\s*([0-9]+(?:-[a-z]+)?)$", text)
        if not m:
            continue

        article_id = normalize_article_id(m.group(1))
        articles.append(article_id)

    # deduplica preservando ordine
    seen = set()
    ordered = []
    for a in articles:
        if a not in seen:
            seen.add(a)
            ordered.append(a)

    return ordered


def main() -> None:
    if not INPUT_HTML.exists():
        raise FileNotFoundError(f"File non trovato: {INPUT_HTML}")

    html = INPUT_HTML.read_text(encoding="utf-8", errors="replace")
    articles = extract_article_headers(html)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "source_file": str(INPUT_HTML),
        "record_type": "ArticleIndex",
        "atto": "D.Lgs. 33/2013",
        "versione": "vigente",
        "articles_count": len(articles),
        "articles": articles,
    }

    OUTPUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    OUTPUT_TXT.write_text("\n".join(articles), encoding="utf-8")

    print(f"Articoli trovati: {len(articles)}")
    print(f"JSON scritto: {OUTPUT_JSON}")
    print(f"TXT scritto:  {OUTPUT_TXT}")


if __name__ == "__main__":
    main()