from collections import Counter
from typing import Iterable, Optional

from src.citations.citation_builder import CitationRecord
from src.coverage.coverage_types import CoverageAssessment
from src.crossref.crossref_types import CrossReferenceRecord
from src.m07.m07_types import M07EvidencePack
from src.models.block_event import BlockEvent
from src.models.source_document import SourceDocument
from src.utils.ids import build_id
from src.vigenza.vigenza_types import VigenzaRecord

from src.reporting.report_types import TechnicalReport


class ReportBuilder:
    def build(
        self,
        *,
        case_id: str,
        source_documents: Iterable[SourceDocument],
        citations: Iterable[CitationRecord],
        vigenza_records: Iterable[VigenzaRecord],
        crossref_records: Iterable[CrossReferenceRecord],
        coverage_assessment: Optional[CoverageAssessment] = None,
        m07_pack: Optional[M07EvidencePack] = None,
        blocks: Optional[Iterable[BlockEvent]] = None,
        warnings: Optional[Iterable[str]] = None,
        errors: Optional[Iterable[str]] = None,
        trace_id: str = '',
    ) -> TechnicalReport:
        source_documents = list(source_documents)
        citations = list(citations)
        vigenza_records = list(vigenza_records)
        crossref_records = list(crossref_records)
        blocks = list(blocks or [])
        warnings = [str(x) for x in (warnings or []) if str(x)]
        errors = [str(x) for x in (errors or []) if str(x)]

        valid_citations = [c.citation_id for c in citations if c.citation_status == 'VALID']
        blocked_citations = [c.citation_id for c in citations if c.citation_status != 'VALID']

        citation_summary = Counter(c.citation_status or 'UNKNOWN' for c in citations)
        vigenza_summary = Counter(v.vigore_status or 'UNKNOWN' for v in vigenza_records)
        crossref_summary = Counter(c.resolution_status or 'UNKNOWN' for c in crossref_records)

        report_status = 'READY'
        if blocks or errors:
            report_status = 'BLOCKED'
        elif warnings:
            report_status = 'READY_WITH_WARNINGS'

        return TechnicalReport(
            record_id=build_id('reportrec'),
            record_type='TechnicalReport',
            report_id=build_id('report'),
            case_id=case_id,
            source_ids=[doc.source_id for doc in source_documents if doc.source_id],
            valid_citation_ids=valid_citations,
            blocked_citation_ids=blocked_citations,
            citation_status_summary=dict(citation_summary),
            vigenza_status_summary=dict(vigenza_summary),
            crossref_status_summary=dict(crossref_summary),
            coverage_ref_id=coverage_assessment.coverage_id if coverage_assessment else None,
            coverage_status=coverage_assessment.coverage_status if coverage_assessment else None,
            m07_ref_id=m07_pack.m07_pack_id if m07_pack else None,
            m07_status=m07_pack.m07_support_status if m07_pack else None,
            warnings=warnings,
            errors=errors,
            block_ids=[block.block_id for block in blocks],
            block_codes=[block.block_code for block in blocks],
            support_only_flag=True,
            report_status=report_status,
            trace_id=trace_id,
        )
