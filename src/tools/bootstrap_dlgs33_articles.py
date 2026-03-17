from pathlib import Path
import json
import re
from datetime import datetime, UTC
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "data" / "normalized" / "norm_units" / "dlgs33_2013_originario_articles"
RAW_DIR = BASE_DIR / "data" / "raw" / "dlgs33_2013" / "article_fetch"
LOG_DIR = BASE_DIR / "data" / "logs"

FAIL_LOG = LOG_DIR / "dlgs33_bootstrap_failures.json"
SUMMARY_LOG = LOG_DIR / "dlgs33_bootstrap_summary.json"

MAIN_URL = "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2013-03-14;33!vig="
ARTICLE_URL = "https://www.normattiva.it/atto/caricaArticolo"

ATTO_TIPO = "Decreto legislativo"
ATTO_NUMERO = "33"
ATTO_ANNO = "2013"
CODICE_REDAZIONALE = "13G00076"
DATA_GAZZETTA = "2013-04-05"
MAX_ARTICLES = 53

COMMON_PARAMS = {
    "art.versione": "1",
    "art.flagTipoArticolo": "0",
    "art.codiceRedazionale": CODICE_REDAZIONALE,
    "art.idSottoArticolo": "1",
    "art.idSottoArticolo1": "10",
    "art.dataPubblicazioneGazzetta": DATA_GAZZETTA,
    "art.progressivo": "0",
}

NOISE_EXACT = {
    "Articoli",
    "Approfondimenti e Funzioni",
    "articolo precedente",
    "articolo successivo",
    "Torna su",
    "Aggiornamenti all'articolo",
    "visualizza atto intero",
    "nascondi",
}

GROUP_CANDIDATES = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]


def now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\r", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/145.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": MAIN_URL,
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
    })
    return s


def warmup_session(session: requests.Session) -> None:
    for url in ("https://www.normattiva.it/", MAIN_URL):
        r = session.get(url, timeout=30, allow_redirects=True)
        print(f"[WARMUP] {url} -> {r.status_code}")
        r.raise_for_status()


def fetch_article_html(session: requests.Session, art_num: int) -> tuple[str, str]:
    last_error = None

    for group_id in GROUP_CANDIDATES:
        params = dict(COMMON_PARAMS)
        params["art.idArticolo"] = str(art_num)
        params["art.idGruppo"] = group_id

        try:
            r = session.get(ARTICLE_URL, params=params, timeout=60, allow_redirects=True)
            print(f"[FETCH] art. {art_num:03d} group={group_id} -> {r.status_code}")
            r.raise_for_status()

            html = r.text
            if not html.strip():
                continue

            if "Normattiva - Errore" in html:
                continue

            return html, group_id

        except Exception as e:
            last_error = e

    raise RuntimeError(
        f"FETCH_FAILED: art. {art_num} non recuperato su nessun idGruppo. Last error: {last_error}"
    )


def normalize_lines(text: str) -> list[str]:
    lines = [clean_text(x) for x in text.splitlines()]
    lines = [x for x in lines if x]
    out = []

    skip_next_after_vigore = False
    for line in lines:
        if line in NOISE_EXACT:
            continue

        low = line.lower()

        if low == "testo in vigore dal:":
            skip_next_after_vigore = True
            continue

        if skip_next_after_vigore:
            skip_next_after_vigore = False
            continue

        if low in {"articolo precedente", "articolo successivo"}:
            continue

        out.append(line)

    return out


def remove_editorial_blocks(text: str) -> str:
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

    text = text.replace("((", "").replace("))", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def looks_like_annex(text: str) -> bool:
    upper = text.upper()
    annex_markers = [
        "\nALLEGATO\n",
        "\nALLEGATO A",
        "\nALLEGATO B",
        "TABELLA 1",
        "NOME DELLA BANCA DATI",
    ]
    return any(marker in upper for marker in annex_markers)


def parse_article_html(html: str, expected_art_num: int) -> tuple[str, str, str]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = clean_text(soup.get_text("\n", strip=True))
    lines = normalize_lines(text)

    if not lines:
        raise ValueError(f"PARSE_INCONSISTENT: pagina vuota per art. {expected_art_num}")

    if looks_like_annex("\n" + "\n".join(lines) + "\n"):
        raise ValueError(
            f"WRONG_SCOPE: art. {expected_art_num} appartiene a un allegato o contiene materiale allegato"
        )

    art_idx = None
    art_patterns = [
        rf"^Articolo\s+{expected_art_num}\.?$",
        rf"^Art\.\s*{expected_art_num}\.?$",
    ]

    for i, line in enumerate(lines):
        if any(re.fullmatch(p, line, flags=re.IGNORECASE) for p in art_patterns):
            art_idx = i
            break

    if art_idx is None:
        for i, line in enumerate(lines):
            if re.search(rf"\b{expected_art_num}\b", line) and (
                "articolo" in line.lower() or line.lower().startswith("art.")
            ):
                art_idx = i
                break

    if art_idx is None:
        preview = "\n".join(lines[:12])
        raise ValueError(
            f"PARSE_INCONSISTENT: intestazione non trovata per art. {expected_art_num}. Preview: {preview}"
        )

    rubrica = ""
    body_start = art_idx + 1

    if body_start < len(lines):
        candidate = lines[body_start]
        if not re.match(r"^\d+\.", candidate):
            rubrica = candidate.strip("() ")
            body_start += 1

    body_lines = lines[body_start:]

    cleaned_body = []
    for line in body_lines:
        low = line.lower()
        if low in {"articolo precedente", "articolo successivo"}:
            continue
        cleaned_body.append(line)

    testo_unita = clean_text("\n".join(cleaned_body))
    testo_unita = remove_editorial_blocks(testo_unita)

    if not testo_unita:
        raise ValueError(f"PARSE_INCONSISTENT: testo vuoto per art. {expected_art_num}")

    if looks_like_annex("\n" + testo_unita + "\n"):
        raise ValueError(f"WRONG_SCOPE: art. {expected_art_num} contiene porzioni di allegato")

    return rubrica, testo_unita, text


def save_article_json(
    art_num: int,
    rubrica: str,
    testo_unita: str,
    ts: str,
    group_id: str,
) -> None:
    payload = {
        "record_id": f"nu_dlgs33_2023_art_{art_num:03d}".replace("_2023_", "_2013_"),
        "record_type": "NormUnit",
        "norm_unit_id": f"dlgs33_2013_art_{art_num:03d}",
        "source_id": "normattiva_dlgs33_2013_originario",
        "unit_type": "articolo",
        "articolo": str(art_num),
        "comma": "",
        "lettera": "",
        "numero": "",
        "allegato": "",
        "rubrica": rubrica,
        "testo_unita": testo_unita,
        "position_index": art_num,
        "hierarchy_path": f"D.Lgs. 33/2013 > Art. {art_num}",
        "cross_reference_ids": [],
        "vigenza_ref_id": "",
        "norm_unit_status": "ACTIVE_STRUCTURED",
        "created_at": ts,
        "updated_at": ts,
        "schema_version": "2.0",
        "record_version": 1,
        "source_layer": "B",
        "trace_id": "trace_dlgs33_originario_bootstrap_v1",
        "active_flag": True,
        "technical_meta": {
            "fetch_group_id": group_id,
            "codice_redazionale": CODICE_REDAZIONALE,
            "data_gazzetta": DATA_GAZZETTA,
        },
    }

    out_file = OUT_DIR / f"art_{art_num:03d}.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    ts = now_utc()
    session = build_session()
    warmup_session(session)

    failures = []
    found_articles = []

    for art_num in range(1, MAX_ARTICLES + 1):
        try:
            html, group_id = fetch_article_html(session, art_num)

            if art_num <= 10:
                raw_file = RAW_DIR / f"dlgs33_art_{art_num:03d}_raw.html"
                raw_file.write_text(html, encoding="utf-8")

            rubrica, testo_unita, _ = parse_article_html(html, art_num)
            save_article_json(art_num, rubrica, testo_unita, ts, group_id)

            found_articles.append(art_num)
            print(f"[OK] art. {art_num:03d}")

        except Exception as e:
            failures.append({
                "articolo": art_num,
                "error": str(e),
            })
            print(f"[WARN] art. {art_num:03d}: {e}")

    missing = [n for n in range(1, MAX_ARTICLES + 1) if n not in found_articles]

    FAIL_LOG.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_LOG.write_text(json.dumps({
        "timestamp": ts,
        "main_url": MAIN_URL,
        "article_url": ARTICLE_URL,
        "articles_found_count": len(found_articles),
        "articles_found": found_articles,
        "missing_articles": missing,
        "failures_count": len(failures),
        "expected_articles": MAX_ARTICLES,
        "atto_tipo": ATTO_TIPO,
        "atto_numero": ATTO_NUMERO,
        "atto_anno": ATTO_ANNO,
        "codice_redazionale": CODICE_REDAZIONALE,
        "data_gazzetta": DATA_GAZZETTA,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] articoli estratti correttamente: {len(found_articles)}")
    print(f"[INFO] articoli mancanti: {len(missing)}")
    print(f"[INFO] articoli con errore: {len(failures)}")
    print(f"[INFO] log riepilogo: {SUMMARY_LOG}")
    print(f"[INFO] log errori: {FAIL_LOG}")

    if len(found_articles) < 30:
        print("[ALERT] Copertura troppo bassa.")
    elif len(found_articles) < 45:
        print("[ALERT] Copertura parziale.")
    else:
        print("[OK] Copertura iniziale soddisfacente per bootstrap.")


if __name__ == "__main__":
    main()