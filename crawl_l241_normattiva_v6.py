from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

ENTRY_URL = (
    "https://www.normattiva.it/atto/caricaDettaglioAtto"
    "?atto.codiceRedazionale=090G0294"
    "&atto.dataPubblicazioneGazzetta=1990-08-18"
    "&bloccoAggiornamentoBreadCrumb=true"
    "&classica=true"
    "&dataVigenza="
    "&generaTabId=true"
    "&tabID="
    "&tipoDettaglio=multivigenza"
    "&title=lbl.dettaglioAtto"
)

ATTO_META = {
    "source_id": "source_norm_241_1990",
    "source_type": "norma",
    "atto_tipo": "Legge",
    "atto_numero": "241",
    "atto_anno": "1990",
    "titolo": "Nuove norme in materia di procedimento amministrativo e di diritto di accesso ai documenti amministrativi",
    "ente_emittente": "Stato",
    "pubblicazione": "Gazzetta Ufficiale",
    "data_pubblicazione": "1990-08-18",
    "gazzetta_numero": "192",
    "gazzetta_anno": "1990",
    "codice_redazionale": "090G0294",
    "uri_ufficiale": ENTRY_URL,
    "stato_verifica_fonte": "VERIFIED",
    "stato_vigenza": "VIGENTE_VERIFICATA",
    "versione_documento": "vigente",
    "document_status": "VERIFIED",
    "authoritative_flag": True,
    "parse_ready_flag": True,
    "index_ready_flag": True,
    "annex_presence_flag": False,
    "multivigente_flag": True,
    "schema_version": "2.0",
    "record_version": 1,
    "source_layer": "B",
    "active_flag": True,
}

ARTICLE_SUFFIXES = r"(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|nonies|decies)"
ARTICLE_LABEL_RE = re.compile(rf"^\d+(?:\s+{ARTICLE_SUFFIXES})?$", re.IGNORECASE)
IMAGE_ARTICLE_RE = re.compile(
    rf"^(?:image(?::\s*elemento\s+grafico)?\s*)?(\d+(?:\s+{ARTICLE_SUFFIXES})?)$",
    re.IGNORECASE,
)
CAPO_LINE_RE = re.compile(r"^\(*\s*(CAPO\s+[IVXLCDM]+(?:-[A-Z]+)?)\s*(.*?)\)*$", re.IGNORECASE)
ARTICLE_HEADING_RE = re.compile(
    rf"^Art\.\s*(\d+(?:[-\s](?:{ARTICLE_SUFFIXES[3:-1]}))?)\.?$",
    re.IGNORECASE,
)
VIGORE_RE = re.compile(r"Testo in vigore dal:\s*([0-9]{1,2}-[0-9]{1,2}-[0-9]{4})")

SESSION_ERROR_MARKERS_FATAL = (
    "Sessione scaduta",
    "Errore nel caricamento delle informazioni",
)

PAGE_READY_MARKERS = (
    "LEGGE 7 agosto 1990, n. 241",
    "Nuove norme in materia di procedimento amministrativo",
    "Articoli",
)

STOP_MARKERS = {
    "articolo successivo",
    "articolo precedente",
    "Approfondimenti",
    "Funzioni",
    "aggiornamenti all'articolo",
}

SUFFIX_SORT = {
    "": "00",
    "bis": "01",
    "ter": "02",
    "quater": "03",
    "quinquies": "04",
    "sexies": "05",
    "septies": "06",
    "octies": "07",
    "novies": "08",
    "nonies": "08",
    "decies": "09",
}


@dataclass
class IndexArticle:
    label_index: str
    label_slug: str
    sort_key: str
    ordine_indice: int
    capo: str | None
    capo_rubrica: str | None


class CrawlError(RuntimeError):
    pass


class SessionExpiredError(CrawlError):
    pass


class ArticleClickError(CrawlError):
    pass


class ArticleParseError(CrawlError):
    pass


# -------------------------
# Utility
# -------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").replace("\xa0", " ")).strip()


def sleep_ms(ms: int) -> None:
    time.sleep(max(ms, 0) / 1000.0)


def is_closed_target_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "target page, context or browser has been closed" in msg or "has been closed" in msg


NORMALIZE_ARTICLE_ALIAS = {
    "nonies": "novies",
}


def normalize_article_token(value: str) -> str:
    text = clean_spaces(value).lower().replace("_", " ").replace("-", " ")
    text = re.sub(r"^image:\s*", "", text)
    text = re.sub(r"^elemento\s+grafico\s*", "", text)
    parts = text.split()
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    base = parts[0]
    suffix = NORMALIZE_ARTICLE_ALIAS.get(parts[1], parts[1])
    return f"{base} {suffix}"


def split_article_label(value: str) -> tuple[int, str]:
    norm = normalize_article_token(value)
    parts = norm.split()
    if not parts or not parts[0].isdigit():
        raise ValueError(f"Etichetta articolo non valida: {value!r}")
    number = int(parts[0])
    suffix = parts[1] if len(parts) > 1 else ""
    return number, suffix


def article_label_to_slug(value: str) -> str:
    norm = normalize_article_token(value)
    return norm.replace(" ", "_")


def article_sort_key(value: str) -> str:
    number, suffix = split_article_label(value)
    suffix_code = SUFFIX_SORT.get(suffix, "99")
    suffix_text = suffix or "base"
    return f"{number:03d}_{suffix_code}_{suffix_text}"


def sha256_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(f"[{now_iso()}] {message}\n")


def has_fatal_session_error(text: str) -> bool:
    body = text or ""
    return any(marker.lower() in body.lower() for marker in SESSION_ERROR_MARKERS_FATAL)


def page_looks_ready(text: str) -> bool:
    body = text or ""
    lowered = body.lower()
    return all(marker.lower() in lowered for marker in PAGE_READY_MARKERS)


def index_looks_ready(text: str) -> bool:
    body = text or ""
    lowered = body.lower()
    return (
        "articoli" in lowered
        and (
            "parole cercate" in lowered
            or "articolo successivo" in lowered
            or "testo in vigore dal" in lowered
            or "art. 1" in lowered
        )
    )


def normalize_index_article_line(line: str) -> str | None:
    line = clean_spaces(line)
    line = re.sub(r'^[-*•]+\s*', '', line, flags=re.IGNORECASE)
    if ARTICLE_LABEL_RE.match(line):
        return normalize_article_token(line)
    match = IMAGE_ARTICLE_RE.match(line)
    if match:
        return normalize_article_token(match.group(1))
    return None


def parse_capo_line(line: str) -> tuple[str, str | None] | None:
    candidate = clean_spaces(line).strip("() ")
    match = CAPO_LINE_RE.match(candidate)
    if not match:
        return None
    capo = clean_spaces(match.group(1)).upper()
    rubrica_inline = clean_spaces(match.group(2)) or None
    return capo, rubrica_inline


# -------------------------
# Parsing indice
# -------------------------

def extract_index_lines(body_text: str) -> list[str]:
    lines = [clean_spaces(line) for line in body_text.splitlines()]
    start_idx = None
    end_idx = None

    for idx, line in enumerate(lines):
        if line == "Articoli":
            start_idx = idx
            break

    if start_idx is None:
        raise CrawlError("Indice dell'atto non trovato nel body text.")

    for idx in range(start_idx + 1, len(lines)):
        line = lines[idx]
        lower = line.lower()
        if (
            lower.startswith("parole cercate")
            or line == "Presente nei seguenti articoli"
            or line == "chiudi"
            or lower == "articolo successivo"
            or lower.startswith("testo in vigore dal:")
            or ARTICLE_HEADING_RE.match(line)
            or ("Approfondimenti" in line and "Funzioni" in line)
        ):
            end_idx = idx
            break

    if end_idx is None:
        # fallback: taglia appena prima del primo heading articolo utile, se presente
        for idx in range(start_idx + 1, len(lines)):
            if ARTICLE_HEADING_RE.match(lines[idx]):
                end_idx = idx
                break

    if end_idx is None:
        raise CrawlError("Fine indice dell'atto non trovata nel body text.")

    return [line for line in lines[start_idx:end_idx] if line]


def parse_index_from_body_text(body_text: str) -> list[IndexArticle]:
    lines = extract_index_lines(body_text)
    items: list[IndexArticle] = []
    current_capo: str | None = None
    current_capo_rubrica: str | None = None

    i = 0
    while i < len(lines):
        line = lines[i]

        if line == "Articoli":
            i += 1
            continue

        capo_info = parse_capo_line(line)
        if capo_info:
            current_capo, inline_rubrica = capo_info
            rubrica_parts: list[str] = []
            if inline_rubrica:
                rubrica_parts.append(inline_rubrica)
            j = i + 1
            while j < len(lines):
                candidate = lines[j]
                if parse_capo_line(candidate) or normalize_index_article_line(candidate):
                    break
                rubrica_parts.append(candidate)
                j += 1
            current_capo_rubrica = clean_spaces(" ".join(rubrica_parts)) or None
            i += 1
            continue

        normalized_article = normalize_index_article_line(line)
        if normalized_article:
            items.append(
                IndexArticle(
                    label_index=normalized_article,
                    label_slug=article_label_to_slug(normalized_article),
                    sort_key=article_sort_key(normalized_article),
                    ordine_indice=len(items) + 1,
                    capo=current_capo,
                    capo_rubrica=current_capo_rubrica,
                )
            )

        i += 1

    if not items:
        raise CrawlError("Indice letto ma nessun articolo riconosciuto.")

    return items


# -------------------------
# Click e parsing articolo corrente
# -------------------------

def bootstrap_page(page, timeout_ms: int, log_path: Path) -> str:
    if page is None or page.is_closed():
        raise CrawlError("Pagina chiusa prima del bootstrap.")
    page.goto(ENTRY_URL, wait_until="domcontentloaded", timeout=timeout_ms)
    sleep_ms(2500)

    try:
        page.get_by_role("link", name=re.compile(r"^multivigente$", re.I)).click(timeout=3000)
        sleep_ms(1000)
    except Exception:
        append_log(log_path, "Tab 'multivigente' non cliccato: si prosegue con la vista corrente.")

    body_text = page.locator("body").inner_text(timeout=timeout_ms)

    if has_fatal_session_error(body_text):
        raise SessionExpiredError("Sessione Normattiva non valida o pagina articolo non caricata correttamente.")

    if not page_looks_ready(body_text):
        append_log(log_path, "Pagina non ancora pronta al primo controllo: attendo e riprovo una volta.")
        sleep_ms(2500)
        body_text = page.locator("body").inner_text(timeout=timeout_ms)

    if has_fatal_session_error(body_text):
        raise SessionExpiredError("Sessione Normattiva non valida o pagina articolo non caricata correttamente.")

    if not page_looks_ready(body_text):
        raise CrawlError("Pagina Normattiva caricata ma markers attesi dell'atto non rilevati.")

    if not index_looks_ready(body_text):
        append_log(log_path, "Indice non ancora completo al primo passaggio: attendo e riprovo.")
        sleep_ms(2500)
        body_text = page.locator("body").inner_text(timeout=timeout_ms)

    if not index_looks_ready(body_text):
        append_log(log_path, "Indice non completo ma proseguo con parser tollerante.")

    return body_text


def find_clickable_anchor_index(page, label: str) -> int:
    script = r"""
(label) => {
  const normalizeArticle = (s) => (s || "")
    .replace(/\u00A0/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase()
    .replace(/-/g, " ")
    .replace(/_/g, " ")
    .replace(/nonies/g, "novies");

  const articleRe = /(?:^|\s)(\d+(?:\s+(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies))?)(?=$|\s)/i;

  const extractArticleToken = (s) => {
    const norm = normalizeArticle(s)
      .replace(/image:\s*elemento\s+grafico\s*/g, " ")
      .replace(/image:\s*/g, " ")
      .replace(/image\s*/g, " ")
      .replace(/elemento\s+grafico\s*/g, " ")
      .replace(/agg\.\d+/g, " ")
      .replace(/orig\./g, " ");
    const m = norm.match(articleRe);
    return m ? normalizeArticle(m[1]) : "";
  };

  const target = extractArticleToken(label);
  if (!target) return -1;

  const anchors = Array.from(document.querySelectorAll('a'));
  const candidates = anchors.map((a, index) => {
      const rect = a.getBoundingClientRect();
      const bundle = [a.innerText, a.textContent, a.getAttribute('title'), a.getAttribute('aria-label')]
        .filter(Boolean)
        .join(' ') + ' ' + Array.from(a.querySelectorAll('img'))
          .map(img => img.getAttribute('alt') || img.getAttribute('aria-label') || img.getAttribute('title') || '')
          .filter(Boolean)
          .join(' ');
      const token = extractArticleToken(bundle);
      return {
        index,
        token,
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height,
        visible: rect.width > 0 && rect.height > 0
      };
    })
    .filter(x => x.visible && x.token === target)
    .sort((a, b) => (a.top - b.top) || (a.left - b.left));

  return candidates.length ? candidates[0].index : -1;
}
"""
    return int(page.evaluate(script, label))

def wait_until_article_loaded(page, expected_label: str, timeout_ms: int) -> str:
    deadline = datetime.now().timestamp() + (timeout_ms / 1000.0)
    expected_norm = normalize_article_token(expected_label)
    last_body = ""

    while datetime.now().timestamp() < deadline:
        if page is None or page.is_closed():
            raise ArticleParseError(f"Pagina chiusa durante il caricamento dell'articolo {expected_label}.")
        try:
            body = page.locator("body").inner_text(timeout=timeout_ms)
        except Exception as exc:
            if is_closed_target_error(exc):
                raise ArticleParseError(f"Pagina/contesto chiuso durante il caricamento dell'articolo {expected_label}.") from exc
            raise
        last_body = body
        if has_fatal_session_error(body):
            raise SessionExpiredError(f"Sessione scaduta durante il caricamento dell'articolo {expected_label}.")

        parsed = try_extract_current_article(body)
        if parsed:
            current_norm = normalize_article_token(parsed["article_label_heading"])
            if current_norm == expected_norm:
                return body
        sleep_ms(350)

    raise ArticleParseError(
        f"Timeout nel caricamento dell'articolo {expected_label}. Ultimo heading utile: {try_extract_current_article(last_body)}"
    )


def click_article_in_session(page, label: str, timeout_ms: int) -> str:
    if page is None or page.is_closed():
        raise ArticleClickError(f"Pagina chiusa prima del click sull'articolo {label}.")
    try:
        anchor_index = find_clickable_anchor_index(page, label)
    except Exception as exc:
        if is_closed_target_error(exc):
            raise ArticleClickError(f"Pagina/contesto chiuso prima della ricerca del link articolo {label}.") from exc
        raise
    if anchor_index < 0:
        raise ArticleClickError(f"Link DOM non trovato per l'articolo {label}.")

    locator = page.locator("a").nth(anchor_index)
    try:
        locator.scroll_into_view_if_needed(timeout=timeout_ms)
        locator.click(timeout=timeout_ms)
    except Exception as exc:
        if is_closed_target_error(exc):
            raise ArticleClickError(f"Pagina/contesto chiuso durante il click sull'articolo {label}.") from exc
        raise

    try:
        page.wait_for_load_state("networkidle", timeout=2000)
    except Exception:
        pass

    sleep_ms(600)
    return wait_until_article_loaded(page, expected_label=label, timeout_ms=timeout_ms)


def try_extract_current_article(body_text: str) -> dict[str, Any] | None:
    try:
        return extract_current_article(body_text)
    except ArticleParseError:
        return None


def extract_current_article(body_text: str) -> dict[str, Any]:
    lines = [clean_spaces(line) for line in body_text.splitlines()]
    lines = [line for line in lines if line]

    article_start_idx = None
    for idx, line in enumerate(lines):
        if ARTICLE_HEADING_RE.match(line):
            article_start_idx = idx
            break

    if article_start_idx is None:
        raise ArticleParseError("Heading articolo corrente non trovato.")

    article_lines: list[str] = []
    stop_markers_lower = {marker.lower() for marker in STOP_MARKERS}
    for idx in range(article_start_idx, len(lines)):
        line = lines[idx]
        lower = line.lower()
        if idx > article_start_idx and lower in stop_markers_lower:
            break
        article_lines.append(line)

    if not article_lines:
        raise ArticleParseError("Blocco articolo corrente vuoto.")

    heading = article_lines[0]
    match = ARTICLE_HEADING_RE.match(heading)
    if not match:
        raise ArticleParseError(f"Heading articolo non valido: {heading!r}")

    article_label_heading = clean_spaces(match.group(1))
    rubrica = None
    if len(article_lines) > 1 and article_lines[1].startswith("(") and article_lines[1].endswith(")"):
        rubrica = article_lines[1].strip("() ")

    vigore_match = VIGORE_RE.search(body_text)
    testo_in_vigore_dal = vigore_match.group(1) if vigore_match else None

    return {
        "article_label_heading": article_label_heading,
        "rubrica": rubrica,
        "testo_in_vigore_dal": testo_in_vigore_dal,
        "testo_unita": "\n".join(article_lines).strip(),
    }


# -------------------------
# Salvataggio
# -------------------------

def build_article_record(
    item: IndexArticle,
    page_url: str,
    html_snapshot_rel: str,
    parsed_article: dict[str, Any],
    trace_id: str,
) -> dict[str, Any]:
    article_heading = parsed_article["article_label_heading"]
    article_text = parsed_article["testo_unita"]
    record_id = f"srcdoc_l241_1990_art_{item.label_slug}"

    payload: dict[str, Any] = {
        "record_id": record_id,
        "record_type": "SourceDocument",
        "corpus_domain_id": "corpus_l241_1990",
        "trace_id": trace_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "last_verified_at": now_iso(),
        "human_verified_flag": False,
        "data_vigenza_inizio": parsed_article.get("testo_in_vigore_dal"),
        "data_vigenza_fine": None,
        "lingua": "it",
        "dominio_ppav": "procedimento_amministrativo",
        **ATTO_META,
        "uri_ufficiale_articolo": page_url,
        "article_label_index": item.label_index,
        "article_label_heading": article_heading,
        "article_label_slug": item.label_slug,
        "article_sort_key": item.sort_key,
        "ordine_indice": item.ordine_indice,
        "capo": item.capo,
        "capo_rubrica": item.capo_rubrica,
        "rubrica_articolo": parsed_article.get("rubrica"),
        "testo_plain": article_text,
        "hash_contenuto": sha256_text(article_text),
        "crawl_method": "dom_index_click_same_session",
        "crawl_timestamp": now_iso(),
        "session_error_flag": False,
        "missing_flag": False,
        "html_snapshot_rel": html_snapshot_rel,
    }
    return payload


def article_json_path(base_dir: Path, item: IndexArticle) -> Path:
    return base_dir / "articles" / f"art_{item.label_slug}.json"


def article_html_path(base_dir: Path, item: IndexArticle) -> Path:
    return base_dir / "source" / f"art_{item.label_slug}.html"


def ensure_live_page(page, context):
    if page is not None and not page.is_closed():
        return page
    new_page = context.new_page()
    return new_page


def dump_error_snapshot(base_dir: Path, item: IndexArticle, body_text: str | None, detail: str) -> None:
    err_dir = base_dir / "errors"
    err_dir.mkdir(parents=True, exist_ok=True)
    slug = item.label_slug
    (err_dir / f"err_{slug}.txt").write_text((body_text or "")[:50000], encoding="utf-8")
    (err_dir / f"err_{slug}.meta.json").write_text(
        json.dumps({"article": item.label_index, "detail": detail, "saved_at": now_iso()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def crawl_one_article(page, context, base_dir: Path, item: IndexArticle, timeout_ms: int, trace_id: str, log_path: Path):
    append_log(log_path, f"START articolo={item.label_index}")
    page = ensure_live_page(page, context)

    body = None
    try:
        body = click_article_in_session(page, item.label_index, timeout_ms=timeout_ms)
        parsed = extract_current_article(body)

        expected_norm = normalize_article_token(item.label_index)
        actual_norm = normalize_article_token(parsed["article_label_heading"])
        if expected_norm != actual_norm:
            raise ArticleParseError(
                f"Mismatch articolo atteso={item.label_index!r} trovato={parsed['article_label_heading']!r}"
            )

        html_path = article_html_path(base_dir, item)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        page_html = ""
        try:
            if page is not None and not page.is_closed():
                page_html = page.content()
        except Exception as exc:
            append_log(log_path, f"WARN impossibile leggere HTML articolo={item.label_index}: {exc}")
        html_path.write_text(page_html, encoding="utf-8")

        payload = build_article_record(
            item=item,
            page_url=page.url,
            html_snapshot_rel=str(html_path.relative_to(base_dir)),
            parsed_article=parsed,
            trace_id=trace_id,
        )
        json_path = article_json_path(base_dir, item)
        write_json(json_path, payload)
        append_log(log_path, f"OK articolo={item.label_index} file={json_path.name}")
        return page, True
    except Exception as exc:
        dump_error_snapshot(base_dir, item, body, str(exc))
        append_log(log_path, f"ERRORE articolo={item.label_index} dettaglio={exc}")
        return page, False


# -------------------------
# Pipeline
# -------------------------


def safe_bootstrap_page(page, context, timeout_ms: int, log_path: Path):
    page = ensure_live_page(page, context)
    try:
        body_text = bootstrap_page(page, timeout_ms=timeout_ms, log_path=log_path)
        return page, body_text
    except Exception as exc:
        append_log(log_path, f"BOOTSTRAP_RETRY motivo={exc}")
        try:
            if page is not None and not page.is_closed():
                page.close()
        except Exception:
            pass
        page = context.new_page()
        body_text = bootstrap_page(page, timeout_ms=timeout_ms, log_path=log_path)
        return page, body_text



def build_manifest(base_dir: Path, index_items: list[IndexArticle], log_path: Path) -> dict[str, Any]:
    found_files = sorted((base_dir / "articles").glob("art_*.json"))
    found_slugs = {path.stem.replace("art_", "", 1) for path in found_files}
    missing = [asdict(item) for item in index_items if item.label_slug not in found_slugs]

    manifest = {
        "source": "Normattiva",
        "entry_url": ENTRY_URL,
        "generated_at": now_iso(),
        "trace_id": f"trace_l241_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "expected_articles": len(index_items),
        "downloaded_articles": len(found_files),
        "missing_articles": missing,
        "session_error_occurrences": 0,
        "status": "COMPLETE" if not missing else "INCOMPLETE",
        "crawl_method": "dom_index_click_same_session",
        "log_rel": str(log_path.relative_to(base_dir)),
    }
    return manifest


def run_crawl(output_dir: Path, headless: bool, timeout_ms: int, retries_missing: int) -> int:
    base_dir = output_dir
    (base_dir / "articles").mkdir(parents=True, exist_ok=True)
    (base_dir / "source").mkdir(parents=True, exist_ok=True)
    (base_dir / "index").mkdir(parents=True, exist_ok=True)
    (base_dir / "logs").mkdir(parents=True, exist_ok=True)
    log_path = base_dir / "logs" / "crawl.log"
    trace_id = f"trace_l241_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(locale="it-IT")
        page = context.new_page()

        try:
            page, body_text = safe_bootstrap_page(page, context, timeout_ms=timeout_ms, log_path=log_path)
            landing_html_path = base_dir / "source" / "landing_page.html"
            
            try:
                landing_html_path.write_text(page.content(), encoding="utf-8")
            except Exception as exc:
                append_log(log_path, f"WARN impossibile salvare landing HTML: {exc}")

            index_items = parse_index_from_body_text(body_text)
            index_payload = {
                "generated_at": now_iso(),
                "trace_id": trace_id,
                "entry_url": ENTRY_URL,
                "article_count": len(index_items),
                "articles": [asdict(item) for item in index_items],
            }
            write_json(base_dir / "index" / "index.json", index_payload)
            append_log(log_path, f"INDICE letto correttamente: {len(index_items)} articoli")

            for item in index_items:
                page, _ = crawl_one_article(page, context, base_dir, item, timeout_ms=timeout_ms, trace_id=trace_id, log_path=log_path)
                if page.is_closed():
                    append_log(log_path, f"PAGE_CLOSED dopo articolo={item.label_index}: ricreo pagina e rifaccio bootstrap")
                    page, _ = safe_bootstrap_page(page, context, timeout_ms=timeout_ms, log_path=log_path)

            for attempt in range(1, retries_missing + 1):
                manifest = build_manifest(base_dir, index_items, log_path)
                if not manifest["missing_articles"]:
                    break
                append_log(log_path, f"RECOVERY tentativo={attempt} mancanti={len(manifest['missing_articles'])}")
                page, body_text = safe_bootstrap_page(page, context, timeout_ms=timeout_ms, log_path=log_path)
                _ = parse_index_from_body_text(body_text)
                for item_dict in manifest["missing_articles"]:
                    item = IndexArticle(**item_dict)
                    page, _ = crawl_one_article(page, context, base_dir, item, timeout_ms=timeout_ms, trace_id=trace_id, log_path=log_path)
                    if page.is_closed():
                        append_log(log_path, f"PAGE_CLOSED in recovery articolo={item.label_index}: ricreo pagina")
                        page, _ = safe_bootstrap_page(page, context, timeout_ms=timeout_ms, log_path=log_path)

            manifest = build_manifest(base_dir, index_items, log_path)
            write_json(base_dir / "index" / "crawl_manifest.json", manifest)
            append_log(log_path, f"MANIFEST status={manifest['status']} downloaded={manifest['downloaded_articles']}")

            print(json.dumps(manifest, ensure_ascii=False, indent=2))
            return 0 if manifest["status"] == "COMPLETE" else 2

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
    parser = argparse.ArgumentParser(
        description="Crawling Normattiva della L. 241/1990 con indice DOM reale + click in sessione attiva."
    )
    parser.add_argument(
        "--output-dir",
        default="data/raw/l241_1990",
        help="Directory di output del corpus grezzo L. 241/1990.",
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Esegue Chromium in modalità visibile (debug).",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=20000,
        help="Timeout Playwright per goto/click/estrazioni.",
    )
    parser.add_argument(
        "--retries-missing",
        type=int,
        default=2,
        help="Numero di tentativi recovery sui mancanti dopo il primo passaggio.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        exit_code = run_crawl(
            output_dir=Path(args.output_dir),
            headless=not args.headful,
            timeout_ms=args.timeout_ms,
            retries_missing=args.retries_missing,
        )
    except KeyboardInterrupt:
        print("Interrotto dall'utente.", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(f"Errore fatale: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(exit_code)
