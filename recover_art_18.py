from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

# Importa le utility già validate nel crawler v6.
from crawl_l241_normattiva_v6 import (
    safe_bootstrap_page,
    click_article_in_session,
    wait_until_article_loaded,
    extract_current_article,
    build_article_record,
    article_json_path,
    article_html_path,
    IndexArticle,
    write_json,
    append_log,
)


def recover_art_18(output_dir: Path, headless: bool, timeout_ms: int) -> int:
    base_dir = output_dir
    (base_dir / "articles").mkdir(parents=True, exist_ok=True)
    (base_dir / "source").mkdir(parents=True, exist_ok=True)
    (base_dir / "logs").mkdir(parents=True, exist_ok=True)

    log_path = base_dir / "logs" / "crawl.log"
    trace_id = f"trace_l241_recover18_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    item = IndexArticle(
        label_index="18",
        label_slug="18",
        sort_key="018_00_base",
        ordine_indice=27,
        capo="CAPO IV",
        capo_rubrica="SEMPLIFICAZIONE DELL'AZIONE AMMINISTRATIVA",
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(locale="it-IT")
        page = context.new_page()
        try:
            page, _ = safe_bootstrap_page(page, context, timeout_ms=timeout_ms, log_path=log_path)
            append_log(log_path, "RECOVER18 bootstrap completato")

            # 1) Entra su 18-bis: nel corpus principale questo click ha già dimostrato di funzionare.
            body = click_article_in_session(page, "18 bis", timeout_ms=timeout_ms)
            parsed = extract_current_article(body)
            if parsed["article_label_heading"].replace("-", " ").strip().lower() != "18 bis":
                raise RuntimeError(f"Articolo ponte non corretto: atteso 18-bis, trovato {parsed['article_label_heading']!r}")
            append_log(log_path, "RECOVER18 ponte su art. 18-bis riuscito")

            # 2) Da 18-bis vai all'articolo precedente.
            previous = page.get_by_role("link", name=re.compile(r"articolo precedente", re.I)).first
            previous.scroll_into_view_if_needed(timeout=timeout_ms)
            previous.click(timeout=timeout_ms)
            body = wait_until_article_loaded(page, expected_label="18", timeout_ms=timeout_ms)
            parsed = extract_current_article(body)
            if parsed["article_label_heading"].replace("-", " ").strip().lower() != "18":
                raise RuntimeError(f"Recupero non coerente: atteso art. 18, trovato {parsed['article_label_heading']!r}")
            append_log(log_path, "RECOVER18 navigazione da 18-bis a 18 riuscita")

            html_path = article_html_path(base_dir, item)
            html_path.write_text(page.content(), encoding="utf-8")

            payload = build_article_record(
                item=item,
                page_url=page.url,
                html_snapshot_rel=str(html_path.relative_to(base_dir)),
                parsed_article=parsed,
                trace_id=trace_id,
            )
            json_path = article_json_path(base_dir, item)
            write_json(json_path, payload)
            append_log(log_path, f"RECOVER18 OK file={json_path.name}")

            print(json.dumps({
                "status": "OK",
                "article": "18",
                "json": str(json_path),
                "html": str(html_path),
                "url": page.url,
            }, ensure_ascii=False, indent=2))
            return 0
        finally:
            try:
                context.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recupero mirato dell'art. 18 L. 241/1990 partendo da art. 18-bis.")
    parser.add_argument("--output-dir", default="data/raw/l241_1990", help="Directory del corpus grezzo L. 241/1990")
    parser.add_argument("--headful", action="store_true", help="Esegue Chromium in modalità visibile")
    parser.add_argument("--timeout-ms", type=int, default=30000, help="Timeout Playwright")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        sys.exit(recover_art_18(Path(args.output_dir), headless=not args.headful, timeout_ms=args.timeout_ms))
    except KeyboardInterrupt:
        print("Interrotto dall'utente.", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(f"Errore fatale: {exc}", file=sys.stderr)
        sys.exit(1)
