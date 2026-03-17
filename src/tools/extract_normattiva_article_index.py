from pathlib import Path
import json
import re
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = BASE_DIR / "src" / "tools" / "normattiva_bootstrap_config.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_article_id(raw: str) -> str:
    raw = raw.strip().lower()
    raw = raw.replace("art.", "").replace("articolo", "").strip()
    return raw.replace(" ", "")


def main() -> None:
    cfg = load_config()
    input_html = BASE_DIR / cfg["raw_html_path"]
    output_txt = BASE_DIR / cfg["article_index_txt"]
    output_json = output_txt.with_suffix(".json")

    if not input_html.exists():
        raise FileNotFoundError(f"HTML non trovato: {input_html}")

    html = input_html.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    headers = soup.find_all("h2", class_="article-num-akn")

    articles = []
    for h in headers:
        text = clean_text(h.get_text(" ", strip=True))
        m = re.match(r"(?i)^Art\.\s*([0-9]+(?:-[a-z]+)?)$", text)
        if m:
            articles.append(normalize_article_id(m.group(1)))

    seen = set()
    ordered = []
    for a in articles:
        if a not in seen:
            seen.add(a)
            ordered.append(a)

    output_txt.parent.mkdir(parents=True, exist_ok=True)
    output_txt.write_text("\n".join(ordered), encoding="utf-8")
    output_json.write_text(
        json.dumps({
            "dataset_id": cfg["dataset_id"],
            "articles_count": len(ordered),
            "articles": ordered
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"[OK] articoli trovati: {len(ordered)}")
    print(f"[INFO] index txt: {output_txt}")
    print(f"[INFO] index json: {output_json}")


if __name__ == "__main__":
    main()
