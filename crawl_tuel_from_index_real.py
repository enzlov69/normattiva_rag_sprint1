import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from playwright.sync_api import sync_playwright

INPUT_FILE = Path("data/raw/tuel_playwright_index/tuel_index_real.json")
OUTPUT_DIR = Path("data/raw/tuel_playwright_full")
ARTICLES_DIR = OUTPUT_DIR / "articles"
DEBUG_DIR = OUTPUT_DIR / "_debug"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_query_values(url: str) -> dict:
    qs = parse_qs(urlparse(url).query)
    def one(name):
        vals = qs.get(name, [])
        return vals[0] if vals else None
    return {
        "versione": one("art.versione"),
        "id_gruppo": one("art.idGruppo"),
        "flag_tipo_articolo": one("art.flagTipoArticolo"),
        "codice_redazionale": one("art.codiceRedazionale"),
        "id_articolo": one("art.idArticolo"),
        "id_sotto_articolo": one("art.idSottoArticolo"),
        "id_sotto_articolo1": one("art.idSottoArticolo1"),
        "data_gu": one("art.dataPubblicazioneGazzetta"),
        "progressivo": one("art.progressivo"),
    }


def article_identity(item: dict) -> tuple:
    return (
        item.get("article_number_base"),
        item.get("article_suffix"),
        item.get("id_articolo"),
        item.get("id_sotto_articolo"),
        item.get("id_sotto_articolo1"),
    )


def dedupe_index_articles(items: list[dict]) -> list[dict]:
    seen = {}
    for item in items:
        ident = article_identity(item)
        current = seen.get(ident)
        if current is None:
            seen[ident] = item
            continue

        # preferisci idGruppo diverso da 1 per evitare wrapper/articolo contenitore
        cur_group = str(current.get("id_gruppo") or "")
        new_group = str(item.get("id_gruppo") or "")
        if cur_group == "1" and new_group != "1":
            seen[ident] = item
            continue

        # preferisci index_order minore, a parità tieni il primo
        try:
            cur_order = int(current.get("index_order") or 999999)
        except Exception:
            cur_order = 999999
        try:
            new_order = int(item.get("index_order") or 999999)
        except Exception:
            new_order = 999999
        if new_order < cur_order:
            seen[ident] = item

    result = list(seen.values())
    result.sort(key=lambda x: int(x.get("index_order") or 999999))
    return result


def get_article_text(page) -> str:
    selectors = [
        ".bodyTesto",
        ".art-just-text-akn",
        "#testo_atto",
        "#content",
        "main",
        "body",
    ]
    for selector in selectors:
        loc = page.locator(selector)
        try:
            if loc.count() > 0:
                txt = normalize_text(loc.first.inner_text(timeout=2500))
                if txt:
                    return txt
        except Exception:
            pass
    return ""


def get_article_label(page, fallback: str) -> str:
    selectors = ["h2.article-num-akn", "h2", "h1"]
    for selector in selectors:
        loc = page.locator(selector)
        try:
            cnt = min(loc.count(), 5)
        except Exception:
            cnt = 0
        for i in range(cnt):
            try:
                txt = normalize_text(loc.nth(i).inner_text(timeout=1000))
                if txt:
                    return txt
            except Exception:
                pass
    return fallback


def save_debug(page, name: str):
    (DEBUG_DIR / f"{name}.html").write_text(page.content(), encoding="utf-8")
    page.screenshot(path=str(DEBUG_DIR / f"{name}.png"), full_page=True)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"File indice non trovato: {INPUT_FILE}")

    payload = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    raw_articles = payload.get("articles", [])

    enriched = []
    for item in raw_articles:
        new_item = dict(item)
        new_item.update(parse_query_values(item.get("url", "")))
        enriched.append(new_item)

    articles = dedupe_index_articles(enriched)

    print(f"Voci indice originali: {len(raw_articles)}")
    print(f"Voci dopo deduplicazione: {len(articles)}")

    aggregated = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=150)
        page = browser.new_page()

        for idx, item in enumerate(articles, start=1):
            label = item.get("article_label_raw") or f"art_{idx}"
            url = item.get("url")
            safe_label = re.sub(r"[^0-9A-Za-z_\-]+", "_", label).strip("_").lower()

            print(f"[{idx}/{len(articles)}] Apro {label} ...")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(1800)

                article_label = get_article_label(page, label)
                article_text = get_article_text(page)

                if not article_text:
                    print(f"  -> testo vuoto, salvo debug")
                    save_debug(page, f"empty_{idx:03d}_{safe_label}")

                record = {
                    "index_order": item.get("index_order"),
                    "article_label_raw": item.get("article_label_raw"),
                    "article_label_page": article_label,
                    "article_number_base": item.get("article_number_base"),
                    "article_suffix": item.get("article_suffix"),
                    "source_url": url,
                    "text": article_text,
                    "versione": item.get("versione"),
                    "id_gruppo": item.get("id_gruppo"),
                    "flag_tipo_articolo": item.get("flag_tipo_articolo"),
                    "codice_redazionale": item.get("codice_redazionale"),
                    "id_articolo": item.get("id_articolo"),
                    "id_sotto_articolo": item.get("id_sotto_articolo"),
                    "id_sotto_articolo1": item.get("id_sotto_articolo1"),
                    "data_gu": item.get("data_gu"),
                    "progressivo": item.get("progressivo"),
                }

                out_file = ARTICLES_DIR / f"{idx:03d}_{safe_label}.json"
                out_file.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                aggregated.append(record)
                print(f"  -> salvato {out_file.name}")

            except Exception as exc:
                print(f"  -> errore: {exc}")
                save_debug(page, f"error_{idx:03d}_{safe_label}")

        browser.close()

    final_payload = {
        "norma": "D.Lgs. 267/2000 - TUEL",
        "source_index_file": str(INPUT_FILE),
        "article_count_saved": len(aggregated),
        "articles": aggregated,
    }
    final_file = OUTPUT_DIR / "tuel_full_from_index_real.json"
    final_file.write_text(json.dumps(final_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"File aggregato salvato in: {final_file}")


if __name__ == "__main__":
    main()
