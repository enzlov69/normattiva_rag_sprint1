from src.blocks.manager import BlockManager
from src.ingestion.metadata_enricher import MetadataEnricher
from src.models.source_document import SourceDocument


def test_metadata_enricher_keeps_valid_source_clean():
    manager = BlockManager()
    enricher = MetadataEnricher(manager)
    source = SourceDocument(
        record_id='rec_1',
        record_type='SourceDocument',
        source_id='source_1',
        atto_tipo='D.Lgs.',
        atto_numero='267',
        atto_anno='2000',
        titolo='TUEL',
        uri_ufficiale='https://www.normattiva.it/x',
    )
    source, _, _ = enricher.enrich(case_id='case_001', source_document=source, norm_units=[], chunks=[])
    assert source.index_ready_flag is True
    assert manager.list_open_blocks(case_id='case_001') == []
