import json
from pathlib import Path

from src.ingestion.normattiva_pipeline_adapter import NormattivaPipelineAdapter


SEARCH_ITEM = {
    "codiceRedazionale": "urn:nir:stato:decreto.legislativo:2000-08-18;267",
    "descrizioneAtto": "DECRETO LEGISLATIVO 18 agosto 2000, n. 267",
    "denominazioneAtto": "DECRETO LEGISLATIVO",
    "numeroProvvedimento": 267,
    "annoProvvedimento": 2000,
    "uri": "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2000-08-18;267",
    "descrizione_emettitore": "Stato",
    "dataEmanazione": "2000-08-18",
}

DETAIL_PAYLOAD = {
    "articoli": [
        {
            "articolo": "107",
            "rubrica": "Funzioni e responsabilita' della dirigenza",
            "commi": [
                {"comma": "1", "testo": "Spetta ai dirigenti la direzione degli uffici."}
            ],
        }
    ]
}


def test_normattiva_pipeline_adapter_runs_from_saved_files(tmp_path: Path) -> None:
    search_path = tmp_path / "search_item.json"
    detail_path = tmp_path / "detail_payload.json"
    search_path.write_text(json.dumps(SEARCH_ITEM), encoding="utf-8")
    detail_path.write_text(json.dumps(DETAIL_PAYLOAD), encoding="utf-8")

    adapter = NormattivaPipelineAdapter()
    result = adapter.run_from_files(
        case_id="case_200",
        search_item_path=search_path,
        detail_payload_path=detail_path,
    )

    assert result.source_document is not None
    assert result.source_document.uri_ufficiale.startswith("https://www.normattiva.it/")
    assert len(result.norm_units) == 1
    assert len(result.chunks) == 1
    assert result.shadow_trace.executed_modules
