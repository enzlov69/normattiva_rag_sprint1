from src.blocks import codes
from src.blocks.manager import BlockManager
from src.coverage.coverage_types import CoverageAssessment
from src.crossref.crossref_types import CrossReferenceRecord
from src.m07.m07_support import M07Support
from src.models.norm_unit import NormUnit
from src.models.source_document import SourceDocument


def _source() -> SourceDocument:
    return SourceDocument(
        record_id='srcrec_1',
        record_type='SourceDocument',
        source_id='source_001',
        atto_tipo='D.Lgs.',
        atto_numero='267',
        atto_anno='2000',
        titolo='TUEL',
        uri_ufficiale='https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2000-08-18;267',
        stato_verifica_fonte='VERIFIED',
        authoritative_flag=True,
    )


def _unit(position: int, articolo: str, comma: str) -> NormUnit:
    return NormUnit(
        record_id=f'nrec_{position}',
        record_type='NormUnit',
        norm_unit_id=f'norm_{position}',
        source_id='source_001',
        unit_type='COMMA',
        articolo=articolo,
        comma=comma,
        testo_unita=f'Testo {articolo}.{comma}',
        position_index=position,
        hierarchy_path=f'articolo:{articolo}/comma:{comma}',
    )


def test_m07_support_builds_ordered_pack_and_keeps_human_completion_required() -> None:
    block_manager = BlockManager()
    support = M07Support(block_manager=block_manager)

    pack = support.build(
        case_id='case_901',
        source_documents=[_source()],
        norm_units=[_unit(2, '107', '2'), _unit(1, '107', '1')],
        crossref_records=[
            CrossReferenceRecord(
                record_id='xrefrec_1',
                record_type='CrossReferenceRecord',
                crossref_id='xref_1',
                source_id='source_001',
                norm_unit_id='norm_1',
                crossref_type='interno',
                crossref_text='articolo 109',
                resolved_flag=True,
                resolution_status='RESOLVED',
            )
        ],
        coverage_assessment=CoverageAssessment(
            record_id='covrec_1',
            record_type='CoverageAssessment',
            coverage_id='cov_1',
            case_id='case_901',
            query_id='qry_1',
            domain_target='enti_locali',
            coverage_score=1.0,
            coverage_status='ADEQUATE',
            critical_gap_flag=False,
        ),
    )

    assert pack.ordered_reading_sequence == ['articolo:107/comma:1', 'articolo:107/comma:2']
    assert pack.human_completion_required is True
    assert pack.missing_elements == []
    assert block_manager.list_open_blocks(case_id='case_901') == []


def test_m07_support_opens_block_when_pack_is_partial() -> None:
    block_manager = BlockManager()
    support = M07Support(block_manager=block_manager)

    pack = support.build(
        case_id='case_902',
        source_documents=[_source()],
        norm_units=[],
        crossref_records=[
            CrossReferenceRecord(
                record_id='xrefrec_2',
                record_type='CrossReferenceRecord',
                crossref_id='xref_2',
                source_id='source_001',
                norm_unit_id='norm_missing',
                crossref_type='allegato',
                crossref_text='allegato A',
                resolved_flag=False,
                resolution_status='PENDING_MANUAL_CHECK',
            )
        ],
        coverage_assessment=CoverageAssessment(
            record_id='covrec_2',
            record_type='CoverageAssessment',
            coverage_id='cov_2',
            case_id='case_902',
            query_id='qry_2',
            domain_target='enti_locali',
            coverage_score=0.2,
            coverage_status='INADEQUATE',
            critical_gap_flag=True,
            missing_sources=['source_extra'],
            missing_annexes=['allegato A'],
            missing_crossrefs=['articolo 109'],
        ),
        require_m07=True,
    )

    assert pack.m07_support_status == 'PARTIAL'
    assert 'norm_units_missing' in pack.missing_elements
    assert 'source_extra' in pack.missing_elements
    assert any(block.block_code == codes.M07_REQUIRED for block in block_manager.list_open_blocks(case_id='case_902'))
