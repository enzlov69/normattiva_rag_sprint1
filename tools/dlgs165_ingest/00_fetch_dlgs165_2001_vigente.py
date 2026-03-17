#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlsplit, urlunsplit

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]

ACT_CODE = "dlgs165_2001_vigente"
ATTO_TIPO_NIR = "decreto.legislativo"
ATTO_TIPO_LABEL = "D.Lgs."
ATTO_NUMERO = "165"
ATTO_ANNO = "2001"
ATTO_DATA = "2001-03-30"
ATTO_TITOLO_ATTESO = (
    "Norme generali sull'ordinamento del lavoro alle dipendenze "
    "delle amministrazioni pubbliche"
)

NORMATTIVA_URL = (
    "https://www.normattiva.it/uri-res/N2Ls?"
    "urn%3Anir%3Astato%3Adecreto.legislativo%3A2001-03-30%3B165%21vig="
)

RAW_DIR = ROOT / "data" / "raw" / "normattiva" / ACT_CODE

LANDING_HTML_PATH = RAW_DIR / f"{ACT_CODE}_landing.html"
LANDING_TEXT_PATH = RAW_DIR / f"{ACT_CODE}_landing.txt"
ARTICLE_INDEX_PATH = RAW_DIR / f"{ACT_CODE}_article_index.json"
COOKIES_PATH = RAW_DIR / f"{ACT_CODE}_session_cookies.json"
MANIFEST_PATH = RAW_DIR / f"{ACT_CODE}_source_manifest_initial.json"

ERROR_MARKERS = [
    "errore nel caricamento delle informazioni",
    "torna alla home",
    "torna a ricerca avanzata",
]

POSITIVE_MARKERS = [
    ATTO_TITOLO_ATTESO.lower(),
    "decreto legislativo 30 marzo 2001, n. 165",
    "lavoro alle dipendenze delle amministrazioni pubbliche",
    "articoli",
]


@dataclass(slots=True)
class ArticleIndexEntry:
    label: str
    href: str
    kind: str
    article_key: str | None = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def relpath_str(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_normattiva_href(href: str) -> str:
    absolute = urljoin(NORMATTIVA_URL, href)
    parts = urlsplit(absolute)

    cleaned_query = re.sub(r"(^|&)CSRF=[^&]*", "", parts.query).strip("&")
    cleaned_query = re.sub(r"&&+", "&", cleaned_query)

    return urlunsplit((parts.scheme, parts.netloc, parts.path, cleaned_query, ""))


def keep_same_act(href: str) -> bool:
    low = href.lower()
    return (
        "uri-res/n2ls" in low
        and "decreto.legislativo:2001-03-30;165" in low
    )


def is_article_href(href: str) -> bool:
    return "~art" in (href or "").lower()


def extract_article_key(href: str) -> str | None:
    """
    Gestisce forme tipo:
    ~art4
    ~art35quater
    ~art55septies
    """
    match = re.search(r"~art([0-9]+[a-z]*)", href.lower())
    if not match:
        return None
    return match.group(1)


def collect_unique_article_entries(
    raw_links: Iterable[dict[str, str]],
) -> list[ArticleIndexEntry]:
    seen: set[tuple[str, str]] = set()
    article_entries: list[ArticleIndexEntry] = []

    for link in raw_links:
        label = normalize_ws(link.get("text", ""))
        href_raw = (link.get("href") or "").strip()

        if not href_raw:
            continue

        href = sanitize_normattiva_href(href_raw)

        if not keep_same_act(href):
            continue

        if not is_article_href(href):
            continue

        key = (label, href)
        if key in seen:
            continue
        seen.add(key)

        article_entries.append(
            ArticleIndexEntry(
                label=label,
                href=href,
                kind="article",
                article_key=extract_article_key(href),
            )
        )

    return article_entries


def detect_error_markers(text: str) -> list[str]:
    low = normalize_ws(text).lower()
    return [marker for marker in ERROR_MARKERS if marker in low]


def detect_positive_markers(text: str, title_page: str) -> list[str]:
    haystack = f"{normalize_ws(title_page)} {normalize_ws(text)}".lower()
    return [marker for marker in POSITIVE_MARKERS if marker in haystack]


def is_fetch_acceptable(
    body_text: str,
    title_page: str,
    article_entries: list[ArticleIndexEntry],
) -> tuple[bool, dict]:
    error_hits = detect_error_markers(body_text)
    positive_hits = detect_positive_markers(body_text, title_page)

    diagnostics = {
        "error_markers_detected": error_hits,
        "positive_markers_detected": positive_hits,
        "article_link_count": len(article_entries),
        "page_title": normalize_ws(title_page),
    }

    # Caso sicuramente non valido: pagina d'errore Normattiva + nessun articolo
    if error_hits and len(article_entries) == 0:
        diagnostics["acceptance_reason"] = (
            "REJECTED_ERROR_PAGE_WITH_ZERO_ARTICLE_LINKS"
        )
        return False, diagnostics

    # Caso valido principale: presenti link articolo coerenti con l'atto
    if len(article_entries) > 0:
        diagnostics["acceptance_reason"] = (
            "ACCEPTED_ARTICLE_LINKS_PRESENT"
        )
        return True, diagnostics

    # Caso residuale: niente articoli ma testo fortemente riconoscibile
    if len(positive_hits) >= 2 and not error_hits:
        diagnostics["acceptance_reason"] = (
            "ACCEPTED_BY_POSITIVE_MARKERS_ONLY"
        )
        return True, diagnostics

    diagnostics["acceptance_reason"] = "REJECTED_INSUFFICIENT_EVIDENCE"
    return False, diagnostics


def build_manifest(
    title_page: str,
    body_text: str,
    final_url: str,
    article_entries: list[ArticleIndexEntry],
    diagnostics: dict,
    attempt_count: int,
) -> dict:
    expected_title_match_flag = (
        ATTO_TITOLO_ATTESO.lower() in normalize_ws(body_text).lower()
    )

    manifest = {
        "corpus_code": ACT_CODE,
        "atto_tipo": ATTO_TIPO_LABEL,
        "atto_tipo_nir": ATTO_TIPO_NIR,
        "atto_numero": ATTO_NUMERO,
        "atto_anno": ATTO_ANNO,
        "atto_data": ATTO_DATA,
        "titolo_atteso": ATTO_TITOLO_ATTESO,
        "titolo_pagina": normalize_ws(title_page),
        "url_ufficiale_normattiva": NORMATTIVA_URL,
        "final_url": final_url,
        "fetched_at_utc": utc_now_iso(),
        "attempt_count": attempt_count,
        "source_authority": "Normattiva",
        "stato_verifica_fonte": "VERIFIED_FROM_OFFICIAL_PORTAL",
        "collection_targets": {
            "main": "normattiva_dlgs165_2001_vigente_main",
            "articles": "normattiva_dlgs165_2001_vigente_articles",
            "commi": "normattiva_dlgs165_2001_vigente_commi",
        },
        "landing_html_path": relpath_str(LANDING_HTML_PATH),
        "landing_text_path": relpath_str(LANDING_TEXT_PATH),
        "article_index_path": relpath_str(ARTICLE_INDEX_PATH),
        "cookies_path": relpath_str(COOKIES_PATH),
        "hash_html_sha256": sha256_text(LANDING_HTML_PATH.read_text(encoding="utf-8")),
        "hash_text_sha256": sha256_text(body_text),
        "article_link_count": len(article_entries),
        "article_keys_preview": [e.article_key for e in article_entries[:20]],
        "expected_title_match_flag": expected_title_match_flag,
        "diagnostics": diagnostics,
        "notes": [
            "Acquisizione del testo vigente eseguita da portale ufficiale Normattiva.",
            "Indice articoli estratto dal DOM della stessa sessione browser.",
            "Gli allegati sono esclusi dal cantiere per scelta progettuale.",
            "La validazione del fetch è basata su segnali documentali e non solo sul titolo nel body.",
            "Nessuna interpretazione normativa: solo cattura documentale e metadati iniziali.",
        ],
    }
    return manifest


def fetch_once(headless: bool, timeout_ms: int) -> tuple[str, str, str, list[dict], list[dict]]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(
            locale="it-IT",
            viewport={"width": 1600, "height": 1200},
        )
        page = context.new_page()

        try:
            page.goto(
                NORMATTIVA_URL,
                wait_until="domcontentloaded",
                timeout=timeout_ms,
            )
            page.wait_for_load_state("networkidle", timeout=timeout_ms)
            page.locator("body").wait_for(timeout=timeout_ms)
        except PlaywrightTimeoutError as exc:
            browser.close()
            raise RuntimeError(
                f"Timeout nel caricamento della pagina Normattiva: {exc}"
            ) from exc

        html = page.content()
        body_text = page.locator("body").inner_text(timeout=timeout_ms)
        title_page = page.title()
        final_url = page.url

        raw_links = page.locator("a[href]").evaluate_all(
            """
            elements => elements.map(a => ({
                text: (a.textContent || "").trim(),
                href: a.getAttribute("href") || ""
            }))
            """
        )
        cookies = context.cookies()

        browser.close()
        return html, body_text, title_page, raw_links, cookies, final_url


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Acquisizione corpus vigente del D.Lgs. 165/2001 da Normattiva, "
            "con salvataggio landing page, testo, indice articoli e manifest iniziale."
        )
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Lancia Chromium in modalità visibile.",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=60000,
        help="Timeout Playwright in millisecondi.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Numero massimo di tentativi di fetch.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=2.5,
        help="Pausa tra i tentativi falliti.",
    )
    args = parser.parse_args()

    ensure_dirs()

    last_html = ""
    last_body_text = ""
    last_title_page = ""
    last_raw_links: list[dict] = []
    last_cookies: list[dict] = []
    last_final_url = ""
    last_diagnostics: dict = {}
    last_article_entries: list[ArticleIndexEntry] = []

    for attempt in range(1, args.max_attempts + 1):
        try:
            html, body_text, title_page, raw_links, cookies, final_url = fetch_once(
                headless=not args.headful,
                timeout_ms=args.timeout_ms,
            )
        except RuntimeError as exc:
            if attempt == args.max_attempts:
                raise SystemExit(f"[ERRORE] {exc}") from exc
            time.sleep(args.sleep_seconds)
            continue

        article_entries = collect_unique_article_entries(raw_links)
        accepted, diagnostics = is_fetch_acceptable(
            body_text=body_text,
            title_page=title_page,
            article_entries=article_entries,
        )

        last_html = html
        last_body_text = body_text
        last_title_page = title_page
        last_raw_links = raw_links
        last_cookies = cookies
        last_final_url = final_url
        last_diagnostics = diagnostics
        last_article_entries = article_entries

        if accepted:
            break

        if attempt < args.max_attempts:
            time.sleep(args.sleep_seconds)

    # Salvataggio sempre dell'ultimo tentativo utile ai fini diagnostici
    LANDING_HTML_PATH.write_text(last_html, encoding="utf-8")
    LANDING_TEXT_PATH.write_text(last_body_text, encoding="utf-8")
    COOKIES_PATH.write_text(
        json.dumps(last_cookies, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    ARTICLE_INDEX_PATH.write_text(
        json.dumps([asdict(item) for item in last_article_entries], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    manifest = build_manifest(
        title_page=last_title_page,
        body_text=last_body_text,
        final_url=last_final_url,
        article_entries=last_article_entries,
        diagnostics=last_diagnostics,
        attempt_count=args.max_attempts,
    )
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    accepted_final, _ = is_fetch_acceptable(
        body_text=last_body_text,
        title_page=last_title_page,
        article_entries=last_article_entries,
    )

    if not accepted_final:
        raise SystemExit(
            "[ERRORE] Fetch non affidabile: Normattiva ha restituito una pagina "
            "priva di evidenze sufficienti dell'atto. Controllare i file salvati:\n"
            f" - {relpath_str(LANDING_TEXT_PATH)}\n"
            f" - {relpath_str(ARTICLE_INDEX_PATH)}\n"
            f" - {relpath_str(MANIFEST_PATH)}"
        )

    print("=== ACQUISIZIONE D.LGS. 165/2001 VIGENTE COMPLETATA ===")
    print(f"URL ufficiale : {NORMATTIVA_URL}")
    print(f"Final URL     : {last_final_url}")
    print(f"Landing HTML  : {relpath_str(LANDING_HTML_PATH)}")
    print(f"Landing TXT   : {relpath_str(LANDING_TEXT_PATH)}")
    print(f"Indice art.   : {relpath_str(ARTICLE_INDEX_PATH)}")
    print(f"Manifest      : {relpath_str(MANIFEST_PATH)}")
    print(f"Articoli trovati       : {len(last_article_entries)}")
    print(f"Marker positivi        : {last_diagnostics.get('positive_markers_detected', [])}")
    print(f"Marker errore          : {last_diagnostics.get('error_markers_detected', [])}")
    print(f"Acceptance reason      : {last_diagnostics.get('acceptance_reason')}")
    print(f"Title match nel body   : {manifest['expected_title_match_flag']}")


if __name__ == "__main__":
    main()