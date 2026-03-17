from typing import Iterable, Optional

from src.blocks import codes
from src.blocks.manager import BlockManager
from src.coverage.coverage_types import CoverageAssessment
from src.crossref.crossref_types import CrossReferenceRecord
from src.retrieval.retrieval_types import RetrievalResult
from src.utils.ids import build_id


class CoverageEstimator:
    def __init__(self, *, block_manager: Optional[BlockManager] = None) -> None:
        self.block_manager = block_manager or BlockManager()

    def assess(
        self,
        *,
        case_id: str,
        query_id: str,
        retrieval_results: Iterable[RetrievalResult],
        domain_target: str = 'enti_locali',
        expected_source_ids: Optional[Iterable[str]] = None,
        required_annex_refs: Optional[Iterable[str]] = None,
        crossref_records: Optional[Iterable[CrossReferenceRecord]] = None,
        trace_id: str = '',
    ) -> CoverageAssessment:
        retrieval_results = list(retrieval_results)
        expected_source_ids = [str(x) for x in (expected_source_ids or []) if str(x)]
        required_annex_refs = [str(x) for x in (required_annex_refs or []) if str(x)]
        crossref_records = list(crossref_records or [])

        seen_source_ids = {result.source_id for result in retrieval_results if result.source_id}
        missing_sources = [source_id for source_id in expected_source_ids if source_id not in seen_source_ids]

        unresolved_essential_crossrefs = [
            record.crossref_text
            for record in crossref_records
            if record.essential_ref_flag and not record.resolved_flag
        ]

        # In this minimal sprint, required annexes are considered missing until explicitly covered.
        missing_annexes = list(required_annex_refs)

        denominator = max(1, len(expected_source_ids) + len(required_annex_refs) + len(unresolved_essential_crossrefs))
        penalties = len(missing_sources) + len(missing_annexes) + len(unresolved_essential_crossrefs)
        if not retrieval_results and not expected_source_ids:
            penalties = max(penalties, 1)
            denominator = max(denominator, 1)

        coverage_score = max(0.0, 1.0 - (penalties / denominator))
        critical_gap_flag = bool(missing_sources or missing_annexes or unresolved_essential_crossrefs or not retrieval_results)
        coverage_status = 'INADEQUATE' if critical_gap_flag else 'ADEQUATE'

        assessment = CoverageAssessment(
            record_id=build_id('coveragerec'),
            record_type='CoverageAssessment',
            coverage_id=build_id('coverage'),
            case_id=case_id,
            query_id=query_id,
            domain_target=domain_target,
            coverage_score=round(coverage_score, 4),
            coverage_scope_notes='Stima tecnica della copertura documentale',
            missing_sources=missing_sources,
            missing_annexes=missing_annexes,
            missing_crossrefs=unresolved_essential_crossrefs,
            coverage_status=coverage_status,
            critical_gap_flag=critical_gap_flag,
            trace_id=trace_id,
        )

        if critical_gap_flag:
            self.block_manager.open_block(
                case_id=case_id,
                block_code=codes.COVERAGE_INADEQUATE,
                block_category='coverage',
                block_severity='CRITICAL',
                origin_module='CoverageEstimator',
                affected_object_type='CoverageAssessment',
                affected_object_id=assessment.coverage_id,
                block_reason='Copertura documentale inadeguata o incompleta',
                release_condition='Integrare fonti, allegati o rinvii essenziali mancanti',
                trace_id=trace_id,
            )

        return assessment
