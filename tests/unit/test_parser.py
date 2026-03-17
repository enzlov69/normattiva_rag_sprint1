from src.blocks.manager import BlockManager
from src.models.source_document import SourceDocument
from src.parsing.parser import Parser


def _source() -> SourceDocument:
    return SourceDocument(
        record_id='rec_1',
        record_type='SourceDocument',
        source_id='source_1',
        atto_tipo='D.Lgs.',
        atto_numero='267',
        atto_anno='2000',
        titolo='TUEL',
        uri_ufficiale='https://www.normattiva.it/x',
        authoritative_flag=True,
        stato_verifica_fonte='VERIFIED',
    )


def test_parser_preserves_basic_structure():
    parser = Parser(BlockManager())
    text = """Art. 1 - Oggetto
1. Primo comma.
2. Secondo comma.

Art. 2 - Finalità
1. Altro testo."""
    units = parser.parse(case_id='case_001', source_document=_source(), text=text)
    assert len(units) == 3
    assert units[0].articolo == '1'
    assert units[0].comma == '1'
    assert units[1].comma == '2'
    assert units[2].articolo == '2'
