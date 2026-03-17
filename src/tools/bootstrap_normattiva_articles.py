from pathlib import Path
import json
import re
from datetime import datetime, UTC
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = BASE_DIR / "src" / "tools" / "normattiva_bootstrap_config.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def fix_mojibake(text: str) -> str:
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
    return token.replace(" ", "")


def article_token_to_file_stem(article_token: str) -> str:
    m = re.fullmatch(r"(\d+)(?:-([a-z]+))?", article_token)
    if not m:
        raise ValueError(f"Token articolo non valido: {article_token}")
    num = int(m.group(1))
    suffix = m.group(2)
    return f"art_{num:03d}_{suffix}" if suffix else f"art_{num:03d}"


def article_token_to_record_id(article_token: str) -> str:
    return article_token_to_file_stem(article_token).replace("art_", "dataset_art_")


def load_article_index(index_path: Path) -> list[str]:
    lines = index_path.read_text(encoding="utf-8").splitlines()
    return [normalize_article_token(x) for x in lines if x.strip()]


def remove_editorial_blocks(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)
    text = re.sub(r"(?m)^-+\s*$", "", text)
    text = text.replace("((", "").replace("))", "")
    text = re.sub(r"(?ims)^AGGIORNAMENTO\s*\(\d+\).*?(?=^(?:Art\.|Articolo)\s+[0-9]+(?:-[a-z]+)?|\Z)", "", text)
    text = re.sub(r"(?ims)^AGGIORNAMENTO\b.*?(?=^(?:Art\.|Articolo)\s+[0-9]+(?:-[a-z]+)?|\Z)", "", text)
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
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def looks_like_annex(text: str) -> bool:
    upper = text.upper()
    markers = ["\nALLEGATO\n", "\nALLEGATO A", "\nALLEGATO B", "TABELLA 1", "NOME DELLA BANCA DATI"]
    return any(m in upper for m in markers)


def is_live_tag(tag) -> bool:
    return getattr(tag, "name", None) is not None and getattr(tag, "attrs", None) is not None


def is_protected_structural_tag(tag) -> bool:
    if not is_live_tag(tag):
        return False
    classes = set(tag.get("class") or [])
    if tag.name in {"h2", "h3"}:
        return True
    return bool({"article-num-akn", "comma-num-akn", "art_text_in_comma"} & classes)


def prune_non_normative_nodes(soup: BeautifulSoup) -> None:
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
        if re.fullmatch(r"\d+", txt):
            tag.decompose()
            continue
        if any(re.search(pat, txt, flags=re.IGNORECASE) for pat in note_patterns):
            tag.decompose()
            continue


def build_article_boundaries(soup: BeautifulSoup):
    headers = soup.find_all("h2", class_="article-num-akn")
    boundaries = []
    for h in headers:
        text = clean_text(h.get_text(" ", strip=True))
        m = re.match(r"(?i)^Art\.\s*([0-9]+(?:-[a-z]+)?)$", text)
        if m:
            boundaries.append((normalize_article_token(m.group(1)), h))
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
    return clean_text(remove_editorial_blocks("\n".join(lines).strip()))


def count_comma_markers(text: str) -> int:
    return len(re.findall(r"(?m)^\s*\d+(?:-[a-z]+)?\.", text))


def split_leading_rubrica(text: str) -> tuple[str, str]:
    lines = [clean_text(x) for x in text.splitlines() if clean_text(x)]
    if len(lines) >= 2:
        first, second = lines[0], lines[1]
        if not re.match(r"^\d+(?:-[a-z]+)?\.", first) and re.match(r"^\d+(?:-[a-z]+)?\.", second):
            return first.strip("() ."), "\n".join(lines[1:])
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
    if not re.match(rf"(?i)^Art\.\s*{re.escape(article_token)}$", header_text):
        raise ValueError(f"PARSE_INCONSISTENT: header inatteso per art. {article_token}: {header_text}")

    rubrica = ""
    rubric_tag = header.find_next_sibling()
    while rubric_tag is not None and getattr(rubric_tag, "name", None) is None:
        rubric_tag = rubric_tag.next_sibling
    if rubric_tag is not None and getattr(rubric_tag, "name", None) == "h3":
        rubrica = clean_text(rubric_tag.get_text(" ", strip=True)).strip("() .")

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

    structured_text = clean_text(remove_editorial_blocks("\n".join(body_lines)))
    full_text = clean_text(remove_editorial_blocks(extract_body_from_full_text(soup, article_token, rubrica)))

    structured_markers = count_comma_markers(structured_text) if structured_text else 0
    full_markers = count_comma_markers(full_text) if full_text else 0

    if full_markers > structured_markers:
        testo_unita = full_text
    elif full_markers == structured_markers and len(full_text) > len(structured_text):
        testo_unita = full_text
    else:
        testo_unita = structured_text or full_text

    testo_unita = clean_text(testo_unita)
    extracted_rubrica, testo_unita_stripped = split_leading_rubrica(testo_unita)
    if extracted_rubrica and not rubrica:
        rubrica = extracted_rubrica
        testo_unita = testo_unita_stripped
    elif rubrica:
        lines = [clean_text(x) for x in testo_unita.splitlines() if clean_text(x)]
        if lines and lines[0].strip("() .") == rubrica.strip("() ."):
            testo_unita = "\n".join(lines[1:]).strip()

    testo_unita = clean_text(remove_editorial_blocks(testo_unita))

    if not testo_unita:
        raise ValueError(f"PARSE_INCONSISTENT: testo vuoto per art. {article_token}")
    if looks_like_annex("\n" + testo_unita + "\n"):
        raise ValueError(f"WRONG_SCOPE: art. {article_token} contiene porzioni di allegato")

    return rubrica, testo_unita


def save_article_json(cfg: dict, article_token: str, rubrica: str, testo_unita: str, ts: str, position_index: int, out_dir: Path):
    file_stem = article_token_to_file_stem(article_token)
    norm_unit_id = article_token_to_record_id(article_token).replace("dataset", cfg["dataset_id"])
    payload = {
        "record_id": f"nu_{norm_unit_id}",
        "record_type": "NormUnit",
        "norm_unit_id": norm_unit_id,
        "source_id": f"normattiva_{cfg['dataset_id']}_{cfg['versione']}",
        "unit_type": "articolo",
        "articolo": article_token,
        "comma": "",
        "lettera": "",
        "numero": "",
        "allegato": "",
        "rubrica": rubrica,
        "testo_unita": testo_unita,
        "position_index": position_index,
        "hierarchy_path": f"{cfg['atto_tipo']} {cfg['atto_numero']}/{cfg['atto_anno']} {cfg['versione']} > Art. {article_token}",
        "cross_reference_ids": [],
        "vigenza_ref_id": "",
        "norm_unit_status": "ACTIVE_STRUCTURED",
        "created_at": ts,
        "updated_at": ts,
        "schema_version": "2.0",
        "record_version": 1,
        "source_layer": "B",
        "trace_id": f"trace_{cfg['dataset_id']}_{cfg['versione']}_bootstrap_v1",
        "active_flag": True,
    }
    out_file = out_dir / f"{file_stem}.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    cfg = load_config()
    input_html = BASE_DIR / cfg["raw_html_path"]
    index_txt = BASE_DIR / cfg["article_index_txt"]
    out_dir = BASE_DIR / cfg["articles_out_dir"]
    logs_dir = BASE_DIR / cfg["logs_dir"]
    fail_log = logs_dir / f"{cfg['dataset_id']}_{cfg['versione']}_bootstrap_failures.json"
    summary_log = logs_dir / f"{cfg['dataset_id']}_{cfg['versione']}_bootstrap_summary.json"

    print(f"[INFO] avvio bootstrap {cfg['dataset_id']} {cfg['versione']}")
    if not input_html.exists():
        raise FileNotFoundError(f"HTML vigente non trovato: {input_html}")

    out_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    ts = now_utc()
    article_index = load_article_index(index_txt)
    print(f"[INFO] html input: {input_html}")
    print(f"[INFO] indice articoli: {len(article_index)}")

    html = input_html.read_text(encoding="utf-8", errors="replace")
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
            save_article_json(cfg, article_token, rubrica, testo_unita, ts, position_index, out_dir)
            found_articles.append(article_token)
            print(f"[OK] art. {article_token}")
        except Exception as e:
            failures.append({"articolo": article_token, "error": str(e)})
            print(f"[WARN] art. {article_token}: {e}")

    missing = [a for a in article_index if a not in found_articles]
    fail_log.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_log.write_text(json.dumps({
        "timestamp": ts,
        "source_html": str(input_html),
        "index_file": str(index_txt),
        "articles_expected_count": len(article_index),
        "articles_found_count": len(found_articles),
        "missing_articles": missing,
        "failures_count": len(failures),
        "dataset_id": cfg["dataset_id"],
        "atto_tipo": cfg["atto_tipo"],
        "atto_numero": cfg["atto_numero"],
        "atto_anno": cfg["atto_anno"],
        "versione": cfg["versione"]
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] articoli estratti correttamente: {len(found_articles)}")
    print(f"[INFO] articoli mancanti: {len(missing)}")
    print(f"[INFO] articoli con errore: {len(failures)}")
    print(f"[INFO] log riepilogo: {summary_log}")
    print(f"[INFO] log errori: {fail_log}")


if __name__ == "__main__":
    main()
