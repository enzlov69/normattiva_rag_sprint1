
"""
crawl_tuel_normattiva_stable.py

Versione stabile del crawler TUEL per Normattiva.
Strategia:
1. apre la pagina del TUEL;
2. estrae le etichette reali dell'indice;
3. per ogni etichetta, ritrova il link corrente nel DOM;
4. clicca il link fresco;
5. aspetta l'aggiornamento del contenuto;
6. salva il testo solo se valido.

Requisiti:
    pip install playwright
    playwright install
"""

import json
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

ROOT_URL = "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2000-08-18;267!vig="

BASE_DIR = Path("data/raw/tuel_stable_crawler")
ARTICLES_DIR = BASE_DIR / "articles"
DEBUG_DIR = BASE_DIR / "_debug"
INDEX_FILE = BASE_DIR / "tuel_index_labels.json"
FULL_FILE = BASE_DIR / "tuel_complete_stable.json"

BASE_DIR.mkdir(parents=True, exist_ok=True)
ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

ARTICLE_PATTERN = re.compile(
    r"^\d+(?:\s+(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|undecies|duodecies|terdecies|quaterdecies|quinquiesdecies))?$",
    re.IGNORECASE
)


def clean_text(txt: str) -> str:
    txt = txt.replace("\xa0", " ")
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()


def is_valid_article_label(label: str) -> bool:
    if not label:
        return False
    if label.lower() == "orig.":
        return False
    return bool(ARTICLE_PATTERN.match(label))


def get_article_text(page) -> str:
    selectors = [
        ".bodyTesto",
        ".art-just-text-akn",
        "#testo_atto",
        "#content",
        "main",
    ]
    for selector in selectors:
        try:
            loc = page.locator(selector)
            if loc.count() > 0:
                txt = clean_text(loc.first.inner_text(timeout=3000))
                if txt:
                    return txt
        except Exception:
            pass
    return ""


def get_article_page_label(page) -> str:
    selectors = ["h2.article-num-akn", "h2", "h1"]
    for selector in selectors:
        try:
            loc = page.locator(selector)
            count = min(loc.count(), 5)
            for i in range(count):
                txt = clean_text(loc.nth(i).inner_text(timeout=1000))
                if txt:
                    return txt
        except Exception:
            pass
    return ""


def save_debug(page, name: str) -> None:
    (DEBUG_DIR / f"{name}.html").write_text(page.content(), encoding="utf-8")
    page.screenshot(path=str(DEBUG_DIR / f"{name}.png"), full_page=True)


def extract_index_labels(page) -> list[str]:
    raw_links = page.query_selector_all("#albero a.numero_articolo")
    labels = []
    seen = set()

    for link in raw_links:
        try:
            label = clean_text(link.inner_text())
            if not is_valid_article_label(label):
                continue
            if label in seen:
                continue
            seen.add(label)
            labels.append(label)
        except Exception:
            pass

    def sort_key(label: str):
        parts = label.lower().split()
        num = int(parts[0])
        suffix = parts[1] if len(parts) > 1 else None
        order = {
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
        return (num, order.get(suffix, 99), label)

    labels.sort(key=sort_key)
    return labels


def find_fresh_link(page, label: str):
    candidates = page.query_selector_all("#albero a.numero_articolo")
    for link in candidates:
        try:
            current = clean_text(link.inner_text())
            if current == label:
                return link
        except Exception:
            pass
    return None


def wait_for_content_change(page, previous_text: str, timeout_ms: int = 8000) -> str:
    start = time.time()
    while (time.time() - start) * 1000 < timeout_ms:
        current = get_article_text(page)
        if current and current != previous_text and "Sessione scaduta" not in current:
            return current
        page.wait_for_timeout(300)
    return get_article_text(page)


def main():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=150)
        page = browser.new_page()

        print("Apro pagina TUEL...")
        page.goto(ROOT_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("#albero", timeout=30000)
        page.wait_for_timeout(4000)

        labels = extract_index_labels(page)
        INDEX_FILE.write_text(json.dumps(labels, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"Articoli validi trovati nell'indice: {len(labels)}")

        previous_text = ""

        for i, label in enumerate(labels, start=1):
            safe_label = re.sub(r"[^0-9A-Za-z]+", "_", label).strip("_").lower()
            print(f"[{i}/{len(labels)}] click su {label}")

            try:
                # ritrova sempre il link fresco nel DOM corrente
                link = find_fresh_link(page, label)
                if link is None:
                    print("   link non trovato, ricarico la pagina e riprovo")
                    page.goto(ROOT_URL, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_selector("#albero", timeout=30000)
                    page.wait_for_timeout(3000)
                    link = find_fresh_link(page, label)

                if link is None:
                    print("   errore: link ancora non trovato")
                    save_debug(page, f"missing_{i:03d}_{safe_label}")
                    continue

                try:
                    link.scroll_into_view_if_needed(timeout=3000)
                except Exception:
                    pass

                try:
                    link.click(timeout=3000)
                except Exception:
                    handle = link
                    page.evaluate("(el) => el.click()", handle)

                page.wait_for_timeout(1200)

                text = wait_for_content_change(page, previous_text, timeout_ms=9000)
                page_label = get_article_page_label(page)

                if not text:
                    print("   testo vuoto")
                    save_debug(page, f"empty_{i:03d}_{safe_label}")
                    continue

                if "Sessione scaduta" in text:
                    print("   sessione scaduta, ricarico e riprovo una volta")
                    page.goto(ROOT_URL, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_selector("#albero", timeout=30000)
                    page.wait_for_timeout(3000)

                    link = find_fresh_link(page, label)
                    if link is None:
                        save_debug(page, f"expired_missing_{i:03d}_{safe_label}")
                        continue

                    try:
                        link.scroll_into_view_if_needed(timeout=3000)
                    except Exception:
                        pass
                    try:
                        link.click(timeout=3000)
                    except Exception:
                        page.evaluate("(el) => el.click()", link)

                    page.wait_for_timeout(1500)
                    text = wait_for_content_change(page, "", timeout_ms=9000)
                    page_label = get_article_page_label(page)

                if not text or "Sessione scaduta" in text:
                    print("   testo non valido")
                    save_debug(page, f"invalid_{i:03d}_{safe_label}")
                    continue

                record = {
                    "index_order": i,
                    "article_label_raw": label,
                    "article_label_page": page_label,
                    "source_url": page.url,
                    "text": text,
                }

                out_file = ARTICLES_DIR / f"{i:03d}_{safe_label}.json"
                out_file.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                results.append(record)
                previous_text = text

                print(f"   salvato {out_file.name}")

                time.sleep(0.8)

            except PlaywrightTimeoutError as exc:
                print(f"   timeout: {exc}")
                save_debug(page, f"timeout_{i:03d}_{safe_label}")
            except Exception as exc:
                print(f"   errore: {exc}")
                save_debug(page, f"error_{i:03d}_{safe_label}")

        browser.close()

    FULL_FILE.write_text(
        json.dumps(
            {
                "norma": "D.Lgs. 267/2000 - TUEL",
                "articles_saved": len(results),
                "articles": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\nCorpus finale salvato: {FULL_FILE}")


if __name__ == "__main__":
    main()
