from src.ingestion.normattiva_ingestor import NormattivaIngestor


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
                {"comma": "1", "testo": "Spetta ai dirigenti la direzione degli uffici."},
                {"comma": "3", "testo": "Sono attribuiti ai dirigenti tutti i compiti di gestione."},
            ],
        }
    ]
}


def test_normattiva_ingestor_builds_internal_objects() -> None:
    ingestor = NormattivaIngestor()

    result = ingestor.ingest_from_payloads(
        case_id="case_100",
        search_item=SEARCH_ITEM,
        detail_payload=DETAIL_PAYLOAD,
    )

    assert result.source_document is not None
    assert result.source_document.atto_numero == "267"
    assert len(result.norm_units) == 2
    assert len(result.chunks) == 2
    assert not any(block.block_severity == "CRITICAL" for block in result.blocks)
    assert len(result.audit_events) >= 2
