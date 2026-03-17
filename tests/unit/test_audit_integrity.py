from src.audit.audit_integrity import AuditIntegrity
from src.audit.logger import AuditLogger
from src.blocks import codes
from src.blocks.manager import BlockManager


def test_audit_integrity_opens_block_when_required_module_is_missing(tmp_path) -> None:
    logger = AuditLogger(log_file=tmp_path / 'audit.jsonl')
    event = logger.log_event(
        case_id='case_1201',
        event_type='PIPELINE_START',
        event_phase='INGESTION',
        origin_module='IngestionPipeline',
    )
    block_manager = BlockManager()
    integrity = AuditIntegrity(block_manager=block_manager)

    result = integrity.check(
        case_id='case_1201',
        events=[event],
        required_phases=['INGESTION'],
        required_modules=['IngestionPipeline', 'RetrievalService'],
    )

    assert result.complete is False
    assert result.missing_modules == ['RetrievalService']
    assert any(block.block_code == codes.AUDIT_INCOMPLETE for block in block_manager.list_open_blocks(case_id='case_1201'))


def test_audit_integrity_is_complete_when_required_events_are_present(tmp_path) -> None:
    logger = AuditLogger(log_file=tmp_path / 'audit_complete.jsonl')
    event_1 = logger.log_event(
        case_id='case_1202',
        event_type='PIPELINE_START',
        event_phase='INGESTION',
        origin_module='IngestionPipeline',
    )
    event_2 = logger.log_event(
        case_id='case_1202',
        event_type='RETRIEVAL',
        event_phase='RETRIEVAL',
        origin_module='RetrievalService',
    )
    block_manager = BlockManager()
    integrity = AuditIntegrity(block_manager=block_manager)

    result = integrity.check(
        case_id='case_1202',
        events=[event_1, event_2],
        required_phases=['INGESTION', 'RETRIEVAL'],
        required_modules=['IngestionPipeline', 'RetrievalService'],
    )

    assert result.complete is True
    assert result.missing_phases == []
    assert result.missing_modules == []
    assert block_manager.list_open_blocks(case_id='case_1202') == []
