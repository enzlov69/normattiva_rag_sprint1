import pytest

from src.blocks.manager import BlockManager
from src.connectors.normattiva_errors import NormattivaMetadataError, NormattivaSourceUnverifiedError
from src.connectors.normattiva_mapper import NormattivaMapper


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


def test_normattiva_mapper_maps_search_item_to_source_document() -> None:
    mapper = NormattivaMapper(BlockManager())

    source_document = mapper.map_search_item_to_source_document(
        case_id="case_001",
        item=SEARCH_ITEM,
        trace_id="trace_001",
    )

    assert source_document.atto_tipo == "DECRETO LEGISLATIVO"
    assert source_document.atto_numero == "267"
    assert source_document.atto_anno == "2000"
    assert source_document.authoritative_flag is True
    assert source_document.stato_verifica_fonte == "VERIFIED"


def test_normattiva_mapper_maps_detail_payload_to_norm_units() -> None:
    mapper = NormattivaMapper(BlockManager())
    source_document = mapper.map_search_item_to_source_document(
        case_id="case_001",
        item=SEARCH_ITEM,
        trace_id="trace_001",
    )

    norm_units = mapper.map_detail_payload_to_norm_units(
        case_id="case_001",
        source_document=source_document,
        detail_payload=DETAIL_PAYLOAD,
        trace_id="trace_001",
    )

    assert len(norm_units) == 2
    assert norm_units[0].articolo == "107"
    assert norm_units[0].comma == "1"
    assert norm_units[1].comma == "3"
    assert norm_units[1].source_id == source_document.source_id


def test_normattiva_mapper_blocks_missing_uri() -> None:
    mapper = NormattivaMapper(BlockManager())
    broken_item = dict(SEARCH_ITEM)
    broken_item.pop("uri")

    with pytest.raises((NormattivaMetadataError, NormattivaSourceUnverifiedError)) as exc:
        mapper.map_search_item_to_source_document(
            case_id="case_001",
            item=broken_item,
            trace_id="trace_001",
        )

    assert "metadati" in str(exc.value).lower() or "uri" in str(exc.value).lower()
