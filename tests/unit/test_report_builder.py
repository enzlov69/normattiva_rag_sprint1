from src.citations.citation_builder import CitationRecord
from src.coverage.coverage_types import CoverageAssessment
from src.crossref.crossref_types import CrossReferenceRecord
from src.m07.m07_types import M07EvidencePack
from src.models.block_event import BlockEvent
from src.models.source_document import SourceDocument
from src.reporting.report_builder import ReportBuilder
from src.vigenza.vigenza_types import VigenzaRecord


def test_report_builder_creates_support_only_technical_report() -> None:
    builder = ReportBuilder()

    report = builder.build(
        case_id='case_1001',
        source_documents=[
            SourceDocument(
                record_id='src_1',
                record_type='SourceDocument',
                source_id='source_001',
                atto_tipo='D.Lgs.',
                atto_numero='267',
                atto_anno='2000',
                uri_ufficiale='https://www.normattiva.it/example',
            )
        ],
        citations=[
            CitationRecord(
                record_id='citrec_1',
                record_type='CitationRecord',
                citation_id='citation_valid',
                citation_status='VALID',
            ),
            CitationRecord(
                record_id='citrec_2',
                record_type='CitationRecord',
                citation_id='citation_invalid',
                citation_status='INVALID',
            ),
        ],
        vigenza_records=[
            VigenzaRecord(
                record_id='vigrec_1',
                record_type='VigenzaRecord',
                vigenza_id='vig_1',
                vigore_status='VIGENTE_VERIFICATA',
            )
        ],
        crossref_records=[
            CrossReferenceRecord(
                record_id='xrefrec_1',
                record_type='CrossReferenceRecord',
                crossref_id='xref_1',
                resolution_status='RESOLVED',
            )
        ],
        coverage_assessment=CoverageAssessment(
            record_id='covrec_1',
            record_type='CoverageAssessment',
            coverage_id='cov_1',
            coverage_status='ADEQUATE',
        ),
        m07_pack=M07EvidencePack(
            record_id='m07rec_1',
            record_type='M07EvidencePack',
            m07_pack_id='m07_1',
            m07_support_status='READY',
        ),
        blocks=[
            BlockEvent(
                record_id='blockrec_1',
                record_type='BlockEvent',
                block_id='block_1',
                block_code='CITATION_INCOMPLETE',
            )
        ],
        warnings=['coverage parziale'],
        errors=[],
    )

    assert report.case_id == 'case_1001'
    assert report.support_only_flag is True
    assert report.valid_citation_ids == ['citation_valid']
    assert report.blocked_citation_ids == ['citation_invalid']
    assert report.citation_status_summary['VALID'] == 1
    assert report.coverage_status == 'ADEQUATE'
    assert report.m07_status == 'READY'
    assert report.block_codes == ['CITATION_INCOMPLETE']
    assert report.report_status == 'BLOCKED'
