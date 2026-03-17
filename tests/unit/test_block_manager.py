from src.blocks.manager import BlockManager


def test_block_manager_tracks_critical_blocks():
    manager = BlockManager()
    manager.open_block(
        case_id='case_001',
        block_code='SOURCE_UNVERIFIED',
        block_category='fonte',
        block_severity='CRITICAL',
        origin_module='test',
        affected_object_type='SourceDocument',
        affected_object_id='source_1',
        block_reason='Fonte non ufficiale',
    )
    assert manager.has_critical_blocks(case_id='case_001') is True
