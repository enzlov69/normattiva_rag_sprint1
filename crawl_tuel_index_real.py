from playwright.sync_api import sync_playwright
import json
import os
import re

ROOT_URL = (
    "https://www.normattiva.it/atto/caricaDettaglioAtto"
    "?atto.codiceRedazionale=000G0304"
    "&atto.dataPubblicazioneGazzetta=2000-09-28"
)

OUTPUT_DIR = "data/raw/tuel_playwright_index"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "tuel_index_real.json")
DEBUG_HTML = os.path.join(OUTPUT_DIR, "root_loaded.html")

ONCLICK_RE = re.compile(r"showArticle\('([^']+)'")

def normalize_label(text: str) -> str:
    return " ".join((text or "").strip().split())

def parse_article_label(label: str):
    parts = label.lower().split()
    if not parts:
        return None, None
    try:
        base = int(parts[0])
    except ValueError:
        return None, None
    suffix = parts[1] if len(parts) > 1 else None
    return base, suffix

def suffix_rank(suffix: str | None) -> int:
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
    return order.get(suffix, 99)

def crawl_index():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=250)
        page = browser.new_page()

        print("Apro ROOT_URL...")
        page.goto(ROOT_URL, wait_until="domcontentloaded", timeout=60000)

        page.wait_for_timeout(4000)
        page.wait_for_selector("#albero", timeout=30000)

        html = page.content()
        with open(DEBUG_HTML, "w", encoding="utf-8") as f:
            f.write(html)

        print("Indice individuato.")

        links = page.query_selector_all("#albero a.numero_articolo")

        articoli = []
        seen = set()

        for link in links:
            try:
                label = normalize_label(link.inner_text())
                onclick = link.get_attribute("onclick") or ""
                match = ONCLICK_RE.search(onclick)

                if not label or not match:
                    continue

                relative_url = match.group(1)
                full_url = "https://www.normattiva.it" + relative_url

                article_number_base, article_suffix = parse_article_label(label)

                key = (label, full_url)
                if key in seen:
                    continue
                seen.add(key)

                articoli.append({
                    "article_label_raw": label,
                    "article_number_base": article_number_base,
                    "article_suffix": article_suffix,
                    "url": full_url,
                    "onclick": onclick,
                })

            except Exception:
                pass

        articoli.sort(
            key=lambda x: (
                x["article_number_base"] if x["article_number_base"] is not None else 999999,
                suffix_rank(x["article_suffix"]),
                x["article_label_raw"],
            )
        )

        for idx, item in enumerate(articoli, start=1):
            item["index_order"] = idx

        print("Articoli trovati:", len(articoli))

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "norma": "D.Lgs. 267/2000 - TUEL",
                    "root_url": ROOT_URL,
                    "article_count_detected": len(articoli),
                    "articles": articoli,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print("File salvato in:", OUTPUT_FILE)
        print("HTML debug salvato in:", DEBUG_HTML)

        for item in articoli[:20]:
            print(item["index_order"], item["article_label_raw"], "->", item["url"])

        browser.close()

if __name__ == "__main__":
    crawl_index()