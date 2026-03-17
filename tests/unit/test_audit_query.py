from pathlib import Path

from src.audit.audit_query import AuditQuery
from src.audit.logger import AuditLogger


def test_audit_query_filters_events_by_case_and_module(tmp_path: Path) -> None:
    log_file = tmp_path / 'audit.jsonl'
    logger = AuditLogger(log_file=log_file)
    logger.log_event(
        case_id='case_1101',
        event_type='PIPELINE_START',
        event_phase='INGESTION',
        origin_module='IngestionPipeline',
    )
    logger.log_event(
        case_id='case_1101',
        event_type='PIPELINE_END',
        event_phase='INGESTION',
        origin_module='IngestionPipeline',
    )
    logger.log_event(
        case_id='case_1102',
        event_type='RETRIEVAL',
        event_phase='RETRIEVAL',
        origin_module='RetrievalService',
    )

    query = AuditQuery(log_file=log_file)
    results = query.query(case_id='case_1101', origin_module='IngestionPipeline')

    assert len(results) == 2
    assert all(event.case_id == 'case_1101' for event in results)
    assert all(event.origin_module == 'IngestionPipeline' for event in results)
