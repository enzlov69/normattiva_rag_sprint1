from src.blocks.manager import BlockManager
from src.ingestion.source_validator import SourceValidator


def test_source_validator_accepts_official_source():
    validator = SourceValidator(BlockManager())
    result = validator.validate(
        case_id='case_001',
        text="""Art. 1 - Oggetto
1. Testo.""",
        metadata={
            'atto_tipo': 'D.Lgs.',
            'atto_numero': '267',
            'atto_anno': '2000',
            'titolo': 'TUEL',
            'uri_ufficiale': 'https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2000-08-18;267',
        },
    )
    assert result.valid is True
    assert result.source_document is not None
    assert result.source_document.authoritative_flag is True


def test_source_validator_blocks_unverified_source():
    manager = BlockManager()
    validator = SourceValidator(manager)
    result = validator.validate(
        case_id='case_001',
        text="""Art. 1 - Oggetto
1. Testo.""",
        metadata={
            'atto_tipo': 'D.Lgs.',
            'atto_numero': '267',
            'atto_anno': '2000',
            'titolo': 'TUEL',
            'uri_ufficiale': 'https://example.com/testo',
        },
    )
    assert result.valid is False
    assert any(b.block_code == 'SOURCE_UNVERIFIED' for b in manager.list_open_blocks(case_id='case_001'))
