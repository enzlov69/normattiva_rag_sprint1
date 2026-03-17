from src.citations.citation_builder import CitationBuilder
from src.models.norm_unit import NormUnit
from src.models.source_document import SourceDocument


def test_citation_builder_creates_structured_citation() -> None:
    builder = CitationBuilder()
    source = SourceDocument(
        record_id='srcdoc_1',
        record_type='SourceDocument',
        source_id='source_267_2000',
        atto_tipo='D.Lgs.',
        atto_numero='267',
        atto_anno='2000',
        titolo='TUEL',
        uri_ufficiale='https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2000-08-18;267',
        stato_verifica_fonte='VERIFIED',
        stato_vigenza='VIGENTE_VERIFICATA',
        authoritative_flag=True,
    )
    unit = NormUnit(
        record_id='normrec_1',
        record_type='NormUnit',
        norm_unit_id='norm_107_3',
        source_id='source_267_2000',
        unit_type='COMMA',
        articolo='107',
        comma='3',
        testo_unita='Sono attribuiti ai dirigenti i compiti di gestione.',
    )

    citation = builder.build(case_id='case_500', source_document=source, norm_unit=unit)

    assert citation.atto_numero == '267'
    assert citation.articolo == '107'
    assert citation.comma == '3'
    assert citation.citation_text == 'D.Lgs. 267/2000, art. 107, comma 3'
