import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARSER_PATH = PROJECT_ROOT / "src" / "parsers" / "dlgs33_parser.py"
CANTIERE_DIR = PROJECT_ROOT / "data" / "cantieri" / "dlgs33_2013"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "dlgs33_2013"
NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized" / "dlgs33_2013"
CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks" / "dlgs33_2013"


def run_parser(*args: str):
    cmd = [sys.executable, str(PARSER_PATH), *args]
    return subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_parser_script_exists():
    assert PARSER_PATH.exists(), f"Parser non trovato: {PARSER_PATH}"


def test_contract_bundle_exists():
    expected = [
        CANTIERE_DIR / "DLGS33_2013_parser_contract_v1.json",
        CANTIERE_DIR / "DLGS33_2013_parser_mapping_rules_v1.json",
        CANTIERE_DIR / "DLGS33_2013_parser_error_catalog_v1.json",
    ]
    for path in expected:
        assert path.exists(), f"File contract mancante: {path}"


def test_required_raw_inputs_exist():
    expected = [
        RAW_DIR / "dlgs33_2013_vigente_normattiva.html",
        RAW_DIR / "dlgs33_2013_allegato.html",
        RAW_DIR / "dlgs97_2016_normattiva.html",
        RAW_DIR / "dlgs97_2016_allegato_b.html",
    ]
    for path in expected:
        assert path.exists(), f"Input raw mancante: {path}"


def test_dry_run_with_placeholders_returns_success():
    result = run_parser("--dry-run", "--allow-placeholder-inputs")
    assert result.returncode == 0, f"Return code inatteso: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    payload = json.loads(result.stdout)
    assert payload["status"] == "SUCCESS"
    assert payload["blocks"] == 0
    assert payload["errors"] == 0
    assert payload["warnings"] == 0


def test_response_package_written_after_dry_run():
    result = run_parser("--dry-run", "--allow-placeholder-inputs")
    assert result.returncode == 0, result.stdout + "\n" + result.stderr

    response_path = CANTIERE_DIR / "DLGS33_2013_parser_response_package.json"
    assert response_path.exists(), "Response package non scritto"

    response = load_json(response_path)
    assert response["status"] == "SUCCESS"
    assert response["payload"]["coverage_report"]["main_source_parsed"] is True
    assert response["payload"]["coverage_report"]["linked_source_parsed"] is True


def test_write_mode_creates_structured_outputs():
    result = run_parser("--allow-placeholder-inputs")
    assert result.returncode == 0, f"Return code inatteso: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    expected = [
        NORMALIZED_DIR / "dlgs33_2013_articles.json",
        NORMALIZED_DIR / "dlgs33_2013_commi.json",
        NORMALIZED_DIR / "dlgs97_2016_articles.json",
        CHUNKS_DIR / "dlgs33_2013_allegato_chunks.jsonl",
        CHUNKS_DIR / "dlgs97_2016_allegato_b_chunks.jsonl",
    ]
    for path in expected:
        assert path.exists(), f"Output strutturato mancante: {path}"


def test_articles_json_has_minimum_shape():
    path = NORMALIZED_DIR / "dlgs33_2013_articles.json"
    data = load_json(path)

    assert data["file_type"] == "norm_units"
    assert data["unit_scope"] == "articles"
    assert "source_document" in data
    assert "records" in data
    assert isinstance(data["records"], list)
    assert len(data["records"]) >= 1

    first = data["records"][0]
    assert first["record_type"] == "NormUnit"
    assert first["unit_type"] == "articolo"
    assert "source_id" in first
    assert "hierarchy_path" in first
    assert isinstance(first["hierarchy_path"], list)


def test_commi_json_has_minimum_shape():
    path = NORMALIZED_DIR / "dlgs33_2013_commi.json"
    data = load_json(path)

    assert data["file_type"] == "norm_units"
    assert data["unit_scope"] == "commi"
    assert isinstance(data["records"], list)
    assert len(data["records"]) >= 1

    first = data["records"][0]
    assert first["record_type"] == "NormUnit"
    assert first["unit_type"] == "comma"
    assert first["comma"] is not None


def test_annex_chunks_jsonl_has_minimum_shape():
    path = CHUNKS_DIR / "dlgs33_2013_allegato_chunks.jsonl"
    assert path.exists(), f"File non trovato: {path}"

    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    row = json.loads(first_line)

    assert row["record_type"] == "ChunkRecord"
    assert row["source_id"] == "dlgs33_2013_vigente_normattiva"
    assert row["orphan_flag"] is False
    assert row["source_layer"] == "B"
    assert row["allegato"] == "Allegato"


def test_parser_blocks_without_allow_placeholder_inputs():
    result = run_parser("--dry-run")
    # In presenza dei placeholder attuali, il parser deve bloccare.
    assert result.returncode == 2, f"Return code inatteso: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    payload = json.loads(result.stdout)
    assert payload["status"] == "BLOCKED"
    assert payload["blocks"] >= 1
