from src.blocks import codes
from src.blocks.manager import BlockManager
from src.crossref.crossref_resolver import CrossReferenceResolver
from src.models.norm_unit import NormUnit
from src.models.source_document import SourceDocument


def _source() -> SourceDocument:
    return SourceDocument(
        record_id='srcrec_1',
        record_type='SourceDocument',
        source_id='source_001',
        atto_tipo='D.Lgs.',
        atto_numero='267',
        atto_anno='2000',
        titolo='TUEL',
        uri_ufficiale='https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2000-08-18;267',
        stato_verifica_fonte='VERIFIED',
        authoritative_flag=True,
    )


def test_crossref_resolver_resolves_internal_article_reference() -> None:
    block_manager = BlockManager()
    resolver = CrossReferenceResolver(block_manager=block_manager)
    known_units = [
        NormUnit(record_id='rec_1', record_type='NormUnit', norm_unit_id='norm_109', source_id='source_001', articolo='109', testo_unita='Testo art. 109')
    ]
    current = NormUnit(
        record_id='rec_2',
        record_type='NormUnit',
        norm_unit_id='norm_107',
        source_id='source_001',
        articolo='107',
        testo_unita='Si applica quanto previsto dall\'articolo 109.',
    )

    records = resolver.resolve(
        case_id='case_701',
        source_document=_source(),
        norm_unit=current,
        known_norm_units=known_units,
    )

    assert len(records) == 1
    assert records[0].resolved_flag is True
    assert records[0].resolution_status == 'RESOLVED'
    assert block_manager.list_open_blocks(case_id='case_701') == []


def test_crossref_resolver_opens_block_when_essential_reference_unresolved() -> None:
    block_manager = BlockManager()
    resolver = CrossReferenceResolver(block_manager=block_manager)
    current = NormUnit(
        record_id='rec_3',
        record_type='NormUnit',
        norm_unit_id='norm_108',
        source_id='source_001',
        articolo='108',
        testo_unita='Si applica quanto previsto dall\'articolo 999.',
    )

    records = resolver.resolve(
        case_id='case_702',
        source_document=_source(),
        norm_unit=current,
        known_norm_units=[],
        essential_ref_default=True,
    )

    assert len(records) == 1
    assert records[0].resolved_flag is False
    assert records[0].resolution_status == 'UNRESOLVED'
    assert any(block.block_code == codes.CROSSREF_UNRESOLVED for block in block_manager.list_open_blocks(case_id='case_702'))
