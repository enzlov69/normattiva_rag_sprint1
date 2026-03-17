
"""
recover_missing_tuel_articles.py

Script di recupero mirato degli articoli TUEL mancanti dal corpus.
"""

import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT_URL = "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2000-08-18;267!vig="

BASE_DIR = Path("data/raw/tuel_stable_crawler")
ARTICLES_DIR = BASE_DIR / "articles"
ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

MISSING = [
    "113",
    "113 bis",
    "114",
    "115",
    "116",
    "117",
    "118",
    "119",
    "120",
    "121",
    "122",
    "123",
    "124",
    "243 quinquies"
]

def clean_text(txt: str) -> str:
    txt = txt.replace("\xa0", " ")
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()

def get_article_text(page):
    selectors = [
        ".bodyTesto",
        ".art-just-text-akn",
        "#testo_atto",
        "#content",
        "main"
    ]
    for selector in selectors:
        try:
            loc = page.locator(selector)
            if loc.count() > 0:
                txt = clean_text(loc.first.inner_text(timeout=4000))
                if txt:
                    return txt
        except:
            pass
    return ""

def find_link(page, label):
    links = page.query_selector_all("#albero a.numero_articolo")
    for link in links:
        try:
            txt = clean_text(link.inner_text())
            if txt == label:
                return link
        except:
            pass
    return None

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("Apro TUEL...")
        page.goto(ROOT_URL, timeout=60000)
        page.wait_for_selector("#albero")

        for label in MISSING:

            safe_label = re.sub(r"[^0-9A-Za-z]+", "_", label).strip("_").lower()
            print("Recupero:", label)

            link = find_link(page, label)

            if link is None:
                print("  link non trovato")
                continue

            try:
                link.scroll_into_view_if_needed()
                link.click()
                page.wait_for_timeout(1500)

                text = get_article_text(page)

                if not text:
                    print("  testo ancora vuoto")
                    continue

                data = {
                    "article_label": label,
                    "source_url": page.url,
                    "text": text
                }

                out = ARTICLES_DIR / f"recovered_{safe_label}.json"
                out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

                print("  salvato:", out.name)

            except Exception as e:
                print("  errore:", e)

        browser.close()

if __name__ == "__main__":
    main()
