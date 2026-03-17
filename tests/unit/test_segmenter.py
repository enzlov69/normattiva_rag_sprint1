from src.blocks.manager import BlockManager
from src.models.norm_unit import NormUnit
from src.parsing.segmenter import Segmenter


def test_segmenter_blocks_orphan_chunk():
    manager = BlockManager()
    segmenter = Segmenter(manager)
    units = [
        NormUnit(
            record_id='r1',
            record_type='NormUnit',
            norm_unit_id='',
            source_id='source_1',
            testo_unita='Testo',
            articolo='1',
        )
    ]
    chunks = segmenter.segment(case_id='case_001', norm_units=units)
    assert chunks[0].orphan_flag is True
    assert any(b.block_code == 'CHUNK_ORPHAN' for b in manager.list_open_blocks(case_id='case_001'))
