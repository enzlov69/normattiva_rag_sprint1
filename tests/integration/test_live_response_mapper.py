from src.live_api.live_response_mapper import LiveResponseMapper


def test_response_mapper_maps_search_item_and_detail_payload() -> None:
    mapper = LiveResponseMapper()
    search_item = {
        'codiceRedazionale': '090G0241',
        'denominazioneAtto': 'LEGGE',
        'numeroProvvedimento': '241',
        'annoProvvedimento': '1990',
        'descrizioneAtto': 'Nuove norme in materia di procedimento amministrativo',
        'dataPubblicazione': '1990-08-18',
        'uri': 'https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:legge:1990-08-07;241',
    }
    source_document = mapper.map_search_item_to_source_document(case_id='case_1', search_item=search_item, trace_id='trace_1')

    detail_payload = {
        'testo': '\n'.join([
            'Art. 1 - Principi generali',
            "1. L'attività amministrativa persegue i fini determinati dalla legge.",
            'Art. 2 - Conclusione del procedimento',
            '1. Ove il procedimento consegua obbligatoriamente ad una istanza...',
            '2. Nei casi in cui disposizioni di legge ovvero i provvedimenti ...',
        ])
    }

    norm_units, chunks = mapper.map_detail_payload(
        case_id='case_1',
        source_document=source_document,
        detail_payload=detail_payload,
        trace_id='trace_1',
    )

    assert source_document.atto_numero == '241'
    assert len(norm_units) == 3
    assert len(chunks) == 3
    assert norm_units[0].articolo == '1'
    assert norm_units[1].articolo == '2'
