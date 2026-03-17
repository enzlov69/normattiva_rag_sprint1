from src.blocks import codes
from src.blocks.manager import BlockManager
from src.coverage.coverage_estimator import CoverageEstimator
from src.crossref.crossref_types import CrossReferenceRecord
from src.retrieval.retrieval_types import RetrievalResult


def _result(source_id: str, chunk_id: str = 'chunk_1') -> RetrievalResult:
    return RetrievalResult(
        record_id=f'resrec_{source_id}',
        record_type='RetrievalResult',
        retrieval_result_id=f'res_{source_id}',
        query_id='qry_001',
        case_id='case_801',
        source_id=source_id,
        norm_unit_id='norm_001',
        chunk_id=chunk_id,
        rank_position=1,
        score_lexical=1.0,
        retrieval_reason='test',
    )


def _crossref(*, text: str, resolved: bool, essential: bool = True) -> CrossReferenceRecord:
    return CrossReferenceRecord(
        record_id='xrefrec_1',
        record_type='CrossReferenceRecord',
        crossref_id='xref_1',
        source_id='source_001',
        norm_unit_id='norm_001',
        crossref_text=text,
        essential_ref_flag=essential,
        resolved_flag=resolved,
        resolution_status='RESOLVED' if resolved else 'UNRESOLVED',
    )


def test_coverage_estimator_marks_adequate_when_expected_source_is_present() -> None:
    block_manager = BlockManager()
    estimator = CoverageEstimator(block_manager=block_manager)

    assessment = estimator.assess(
        case_id='case_801',
        query_id='qry_001',
        retrieval_results=[_result('source_001')],
        expected_source_ids=['source_001'],
        crossref_records=[],
    )

    assert assessment.coverage_status == 'ADEQUATE'
    assert assessment.critical_gap_flag is False
    assert assessment.coverage_score == 1.0
    assert block_manager.list_open_blocks(case_id='case_801') == []


def test_coverage_estimator_opens_block_when_coverage_is_inadequate() -> None:
    block_manager = BlockManager()
    estimator = CoverageEstimator(block_manager=block_manager)

    assessment = estimator.assess(
        case_id='case_802',
        query_id='qry_002',
        retrieval_results=[],
        expected_source_ids=['source_001'],
        required_annex_refs=['allegato A'],
        crossref_records=[_crossref(text='articolo 109', resolved=False)],
    )

    assert assessment.coverage_status == 'INADEQUATE'
    assert assessment.critical_gap_flag is True
    assert 'source_001' in assessment.missing_sources
    assert 'allegato A' in assessment.missing_annexes
    assert 'articolo 109' in assessment.missing_crossrefs
    assert any(block.block_code == codes.COVERAGE_INADEQUATE for block in block_manager.list_open_blocks(case_id='case_802'))
