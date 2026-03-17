from src.blocks import codes
from src.blocks.manager import BlockManager
from src.models.norm_unit import NormUnit
from src.models.source_document import SourceDocument
from src.vigenza.vigenza_checker import VigenzaChecker


def _source(status: str) -> SourceDocument:
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
        stato_vigenza=status,
        authoritative_flag=True,
    )


def _unit() -> NormUnit:
    return NormUnit(
        record_id='nrec_1',
        record_type='NormUnit',
        norm_unit_id='norm_001',
        source_id='source_001',
        articolo='107',
        comma='3',
        testo_unita='Il responsabile adotta gli atti di gestione.',
    )


def test_vigenza_checker_returns_verified_record_without_blocks() -> None:
    block_manager = BlockManager()
    checker = VigenzaChecker(block_manager=block_manager)

    record = checker.check(
        case_id='case_601',
        source_document=_source('VIGENTE_VERIFICATA'),
        norm_unit=_unit(),
        essential_point_flag=True,
    )

    assert record.vigore_status == 'VIGENTE_VERIFICATA'
    assert record.block_if_uncertain_flag is False
    assert block_manager.list_open_blocks(case_id='case_601') == []


def test_vigenza_checker_opens_block_when_uncertain_on_essential_point() -> None:
    block_manager = BlockManager()
    checker = VigenzaChecker(block_manager=block_manager)

    record = checker.check(
        case_id='case_602',
        source_document=_source('VIGENZA_INCERTA'),
        norm_unit=_unit(),
        essential_point_flag=True,
    )

    assert record.vigore_status == 'VIGENZA_INCERTA'
    assert record.block_if_uncertain_flag is True
    assert any(block.block_code == codes.VIGENZA_UNCERTAIN for block in block_manager.list_open_blocks(case_id='case_602'))
