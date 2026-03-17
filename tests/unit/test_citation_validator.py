from src.blocks import codes
from src.blocks.manager import BlockManager
from src.citations.citation_builder import CitationRecord
from src.citations.citation_validator import CitationValidator


def test_citation_validator_marks_complete_citation_as_valid() -> None:
    validator = CitationValidator(block_manager=BlockManager())
    citation = CitationRecord(
        record_id='citrec_1',
        record_type='CitationRecord',
        citation_id='citation_1',
        case_id='case_501',
        source_id='source_1',
        norm_unit_id='norm_1',
        atto_tipo='D.Lgs.',
        atto_numero='267',
        atto_anno='2000',
        articolo='107',
        comma='3',
        uri_ufficiale='https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2000-08-18;267',
        stato_vigenza='VIGENTE_VERIFICATA',
    )

    validated = validator.validate(case_id='case_501', citation=citation)

    assert validated.citation_status == 'VALID'
    assert validated.opponibile_flag is True
    assert validated.validation_errors == []


def test_citation_validator_blocks_incomplete_citation() -> None:
    block_manager = BlockManager()
    validator = CitationValidator(block_manager=block_manager)
    citation = CitationRecord(
        record_id='citrec_2',
        record_type='CitationRecord',
        citation_id='citation_2',
        case_id='case_502',
        source_id='source_1',
        norm_unit_id='norm_1',
        atto_tipo='D.Lgs.',
        atto_numero='267',
        atto_anno='2000',
        articolo='107',
        uri_ufficiale='',
        stato_vigenza='VIGENTE_VERIFICATA',
    )

    validated = validator.validate(case_id='case_502', citation=citation)

    assert validated.citation_status == 'INVALID'
    assert validated.opponibile_flag is False
    assert any(block.block_code == codes.CITATION_INCOMPLETE for block in block_manager.list_open_blocks(case_id='case_502'))
