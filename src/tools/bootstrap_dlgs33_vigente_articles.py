from pathlib import Path
import json
import re
from datetime import datetime, UTC
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_HTML = BASE_DIR / "data" / "raw" / "dlgs33_2013" / "vigente" / "dlgs33_2013_vigente_normattiva.html"
INDEX_TXT = BASE_DIR / "data" / "processed" / "dlgs33_2013_vigente_article_index.txt"

OUT_DIR = BASE_DIR / "data" / "normalized" / "norm_units" / "dlgs33_2013_vigente_articles"
LOG_DIR = BASE_DIR / "data" / "logs"

FAIL_LOG = LOG_DIR / "dlgs33_vigente_bootstrap_failures.json"
SUMMARY_LOG = LOG_DIR / "dlgs33_vigente_bootstrap_summary.json"

ATTO_TIPO = "Decreto legislativo"
ATTO_NUMERO = "33"
ATTO_ANNO = "2013"


def now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def fix_mojibake(text: str) -> str:
    """
    Ripara il caso tipico UTF-8 letto come latin-1/cp1252.
    Applica il fix solo se trova segnali chiari di mojibake.
    """
    if not text:
        return text

    suspicious = ("Ã", "Â", "â€", "â€™", "â€œ", "â€\x9d")
    if not any(s in text for s in suspicious):
        return text

    for enc in ("latin1", "cp1252"):
        try:
            repaired = text.encode(enc, errors="ignore").decode("utf-8", errors="ignore")
            if repaired and repaired.count("Ã") < text.count("Ã"):
                return repaired
        except Exception:
            pass

    return text


def clean_text(text: str) -> str:
    text = fix_mojibake(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\r", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_article_token(token: str) -> str:
    token = token.strip().lower()
    token = token.replace("art.", "").replace("articolo", "").strip()
    token = token.replace(" ", "")
    return token


def article_token_to_file_stem(article_token: str) -> str:
    m = re.fullmatch(r"(\d+)(?:-([a-z]+))?", article_token)
    if not m:
        raise ValueError(f"Token articolo non valido: {article_token}")

    num = int(m.group(1))
    suffix = m.group(2)

    if suffix:
        return f"art_{num:03d}_{suffix}"
    return f"art_{num:03d}"


def article_token_to_record_id(article_token: str) -> str:
    return article_token_to_file_stem(article_token).replace("art_", "dlgs33_2013_art_")


def load_article_index() -> list[str]:
    if not INDEX_TXT.exists():
        raise FileNotFoundError(f"Indice non trovato: {INDEX_TXT}")

    lines = INDEX_TXT.read_text(encoding="utf-8").splitlines()
    lines = [normalize_article_token(x) for x in lines if x.strip()]
    return lines


def remove_editorial_blocks(text: str) -> str:
    """
    Rimuove rumore redazionale non opponibile:
    - numeri isolati
    - linee di separazione
    - blocchi AGGIORNAMENTO
    - residui tipici di note normative/giurisprudenziali
    """
    text = clean_text(text)

    # numeri isolati / marcatori tipo 9, 15
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)

    # separatori
    text = re.sub(r"(?m)^-+\s*$", "", text)

    # doppie parentesi editoriali: mantiene il contenuto
    text = text.replace("((", "").replace("))", "")

    # blocchi espliciti AGGIORNAMENTO
    text = re.sub(
        r"(?ims)^AGGIORNAMENTO\s*\(\d+\).*?(?=^(?:Art\.|Articolo)\s+[0-9]+(?:-[a-z]+)?|\Z)",
        "",
        text,
    )
    text = re.sub(
        r"(?ims)^AGGIORNAMENTO\b.*?(?=^(?:Art\.|Articolo)\s+[0-9]+(?:-[a-z]+)?|\Z)",
        "",
        text,
    )

    # linee che segnalano note redazionali / giurisprudenziali in coda
    editorial_starts = [
        r"^\s*Il\s+D\.Lgs\..*ha disposto.*$",
        r"^\s*Il\s+decreto\s+legislativo.*ha disposto.*$",
        r"^\s*La\s+Corte\s+Costituzionale.*$",
        r"^\s*La\s+Corte.*ha dichiarato.*$",
        r"^\s*sentenza.*$",
        r"^\s*in\s+G\.U\..*$",
    ]
    for pat in editorial_starts:
        text = re.sub(rf"(?ims){pat}.*\Z", "", text)

    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def looks_like_annex(text: str) -> bool:
    upper = text.upper()
    markers = [
        "\nALLEGATO\n",
        "\nALLEGATO A",
        "\nALLEGATO B",
        "TABELLA 1",
        "NOME DELLA BANCA DATI",
    ]
    return any(m in upper for m in markers)

def is_live_tag(tag) -> bool:
    return getattr(tag, "name", None) is not None and getattr(tag, "attrs", None) is not None

def is_protected_structural_tag(tag) -> bool:
    if not is_live_tag(tag):
        return False

    classes = set(tag.get("class") or [])
    if tag.name in {"h2", "h3"}:
        return True
    if "article-num-akn" in classes:
        return True
    if "comma-num-akn" in classes:
        return True
    if "art_text_in_comma" in classes:
        return True
    return False

def prune_non_normative_nodes(soup: BeautifulSoup) -> None:
    """
    Elimina nodi non normativi che contaminano il testo:
    - note di aggiornamento
    - note giurisprudenziali
    - marcatori numerici isolati
    """
    note_patterns = [
        r"\bha disposto\b",
        r"\bha dichiarato\b",
        r"\bCorte Costituzionale\b",
        r"\bsentenza\b",
        r"\bin G\.U\.\b",
        r"\bacquistano efficacia\b",
    ]

    for tag in list(soup.find_all(True)):
        if not is_live_tag(tag):
            continue

        if is_protected_structural_tag(tag):
            continue

        txt = clean_text(tag.get_text(" ", strip=True))
        if not txt:
            continue

        # footnote isolate tipo 9, 15
        if re.fullmatch(r"\d+", txt):
            tag.decompose()
            continue

        # note redazionali / giurisprudenziali
        if any(re.search(pat, txt, flags=re.IGNORECASE) for pat in note_patterns):
            tag.decompose()
            continue


def build_article_boundaries(soup: BeautifulSoup):
    headers = soup.find_all("h2", class_="article-num-akn")
    boundaries = []

    for h in headers:
        text = clean_text(h.get_text(" ", strip=True))
        m = re.match(r"(?i)^Art\.\s*([0-9]+(?:-[a-z]+)?)$", text)
        if not m:
            continue
        token = normalize_article_token(m.group(1))
        boundaries.append((token, h))

    return boundaries


def extract_article_block_html(header_tag) -> str:
    parts = [str(header_tag)]
    current = header_tag.next_sibling

    while current is not None:
        if getattr(current, "name", None) == "h2" and "article-num-akn" in (current.get("class") or []):
            break
        parts.append(str(current))
        current = current.next_sibling

    return "".join(parts)


def extract_body_from_full_text(soup: BeautifulSoup, article_token: str, rubrica: str) -> str:
    raw_text = clean_text(soup.get_text("\n", strip=True))
    lines = [clean_text(x) for x in raw_text.splitlines() if clean_text(x)]

    if not lines:
        return ""

    header_pattern = rf"(?i)^Art\.\s*{re.escape(article_token)}$"
    if lines and re.match(header_pattern, lines[0]):
        lines = lines[1:]

    if rubrica and lines and lines[0].strip("() .") == rubrica.strip("() ."):
        lines = lines[1:]

    body = "\n".join(lines).strip()
    body = remove_editorial_blocks(body)
    return clean_text(body)


def count_comma_markers(text: str) -> int:
    return len(re.findall(r"(?m)^\s*\d+(?:-[a-z]+)?\.", text))


def split_leading_rubrica(text: str) -> tuple[str, str]:
    """
    Se il testo parte con una riga di rubrica seguita dal primo comma,
    estrae la rubrica dal corpo articolo.
    """
    lines = [clean_text(x) for x in text.splitlines() if clean_text(x)]
    if len(lines) >= 2:
        first = lines[0]
        second = lines[1]
        if not re.match(r"^\d+(?:-[a-z]+)?\.", first) and re.match(r"^\d+(?:-[a-z]+)?\.", second):
            rubrica = first.strip("() .")
            body = "\n".join(lines[1:])
            return rubrica, body
    return "", text


def parse_article_block(article_token: str, block_html: str) -> tuple[str, str]:
    soup = BeautifulSoup(block_html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    prune_non_normative_nodes(soup)

    header = soup.find("h2", class_="article-num-akn")
    if header is None:
        raise ValueError(f"PARSE_INCONSISTENT: header mancante per art. {article_token}")

    header_text = clean_text(header.get_text(" ", strip=True))
    expected_header_pattern = rf"(?i)^Art\.\s*{re.escape(article_token)}$"
    if not re.match(expected_header_pattern, header_text):
        raise ValueError(
            f"PARSE_INCONSISTENT: header inatteso per art. {article_token}: {header_text}"
        )

    rubrica = ""
    rubric_tag = header.find_next_sibling()
    while rubric_tag is not None and getattr(rubric_tag, "name", None) is None:
        rubric_tag = rubric_tag.next_sibling

    if rubric_tag is not None and getattr(rubric_tag, "name", None) == "h3":
        rubrica = clean_text(rubric_tag.get_text(" ", strip=True)).strip("() .")

    # Estrazione strutturata dai commi
    body_lines = []
    comma_spans = soup.find_all("span", class_="comma-num-akn")

    if comma_spans:
        for comma_num in comma_spans:
            num_text = clean_text(comma_num.get_text(" ", strip=True))

            container = comma_num.find_next_sibling("span", class_="art_text_in_comma")

            if container is None:
                parent = comma_num.parent
                if parent is not None:
                    for child in parent.children:
                        if getattr(child, "name", None) == "span" and "art_text_in_comma" in (child.get("class") or []):
                            container = child
                            break

            if container is None:
                continue

            comma_body = clean_text(container.get_text("\n", strip=True))

            if num_text:
                body_lines.append(num_text)
            if comma_body:
                body_lines.append(comma_body)

    structured_text = clean_text("\n".join(body_lines))
    structured_text = remove_editorial_blocks(structured_text)

    # Fallback robusto full-text
    full_text = extract_body_from_full_text(soup, article_token, rubrica)
    full_text = remove_editorial_blocks(full_text)

    # Sceglie la versione più completa
    structured_markers = count_comma_markers(structured_text) if structured_text else 0
    full_markers = count_comma_markers(full_text) if full_text else 0

    if full_markers > structured_markers:
        testo_unita = full_text
    elif full_markers == structured_markers and len(full_text) > len(structured_text):
        testo_unita = full_text
    else:
        testo_unita = structured_text or full_text

    testo_unita = clean_text(testo_unita)

    # Se la rubrica è finita nel corpo, la estrae
    extracted_rubrica, testo_unita_stripped = split_leading_rubrica(testo_unita)
    if extracted_rubrica and not rubrica:
        rubrica = extracted_rubrica
        testo_unita = testo_unita_stripped
    elif rubrica:
        # Se la rubrica è già valorizzata, la toglie dal corpo se compare in testa
        lines = [clean_text(x) for x in testo_unita.splitlines() if clean_text(x)]
        if lines and lines[0].strip("() .") == rubrica.strip("() ."):
            testo_unita = "\n".join(lines[1:]).strip()

    testo_unita = remove_editorial_blocks(testo_unita)

    if not testo_unita:
        raise ValueError(f"PARSE_INCONSISTENT: testo vuoto per art. {article_token}")

    if looks_like_annex("\n" + testo_unita + "\n"):
        raise ValueError(f"WRONG_SCOPE: art. {article_token} contiene porzioni di allegato")

    return rubrica, testo_unita


def save_article_json(article_token: str, rubrica: str, testo_unita: str, ts: str, position_index: int):
    file_stem = article_token_to_file_stem(article_token)
    norm_unit_id = article_token_to_record_id(article_token)

    payload = {
        "record_id": f"nu_{norm_unit_id}",
        "record_type": "NormUnit",
        "norm_unit_id": norm_unit_id,
        "source_id": "normattiva_dlgs33_2013_vigente",
        "unit_type": "articolo",
        "articolo": article_token,
        "comma": "",
        "lettera": "",
        "numero": "",
        "allegato": "",
        "rubrica": rubrica,
        "testo_unita": testo_unita,
        "position_index": position_index,
        "hierarchy_path": f"D.Lgs. 33/2013 vigente > Art. {article_token}",
        "cross_reference_ids": [],
        "vigenza_ref_id": "",
        "norm_unit_status": "ACTIVE_STRUCTURED",
        "created_at": ts,
        "updated_at": ts,
        "schema_version": "2.0",
        "record_version": 1,
        "source_layer": "B",
        "trace_id": "trace_dlgs33_vigente_bootstrap_v2",
        "active_flag": True,
    }

    out_file = OUT_DIR / f"{file_stem}.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    print("[INFO] avvio bootstrap vigente D.Lgs. 33/2013")

    if not INPUT_HTML.exists():
        raise FileNotFoundError(f"HTML vigente non trovato: {INPUT_HTML}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    ts = now_utc()
    article_index = load_article_index()

    print(f"[INFO] html input: {INPUT_HTML}")
    print(f"[INFO] indice articoli: {len(article_index)}")

    html = INPUT_HTML.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    boundaries = build_article_boundaries(soup)
    boundary_map = {token: tag for token, tag in boundaries}

    print(f"[INFO] boundaries lette dal DOM: {len(boundaries)}")

    failures = []
    found_articles = []

    for position_index, article_token in enumerate(article_index, start=1):
        try:
            header_tag = boundary_map.get(article_token)
            if header_tag is None:
                raise ValueError(f"HEADER_NOT_FOUND: art. {article_token}")

            block_html = extract_article_block_html(header_tag)
            rubrica, testo_unita = parse_article_block(article_token, block_html)
            save_article_json(article_token, rubrica, testo_unita, ts, position_index)

            found_articles.append(article_token)
            print(f"[OK] art. {article_token}")

        except Exception as e:
            failures.append({
                "articolo": article_token,
                "error": str(e),
            })
            print(f"[WARN] art. {article_token}: {e}")

    missing = [a for a in article_index if a not in found_articles]

    FAIL_LOG.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_LOG.write_text(json.dumps({
        "timestamp": ts,
        "source_html": str(INPUT_HTML),
        "index_file": str(INDEX_TXT),
        "articles_expected_count": len(article_index),
        "articles_expected": article_index,
        "articles_found_count": len(found_articles),
        "articles_found": found_articles,
        "missing_articles": missing,
        "failures_count": len(failures),
        "atto_tipo": ATTO_TIPO,
        "atto_numero": ATTO_NUMERO,
        "atto_anno": ATTO_ANNO,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] articoli estratti correttamente: {len(found_articles)}")
    print(f"[INFO] articoli mancanti: {len(missing)}")
    print(f"[INFO] articoli con errore: {len(failures)}")
    print(f"[INFO] log riepilogo: {SUMMARY_LOG}")
    print(f"[INFO] log errori: {FAIL_LOG}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] {type(e).__name__}: {e}")
        raise