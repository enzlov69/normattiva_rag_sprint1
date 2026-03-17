from typing import Iterable, Optional

from src.blocks import codes
from src.blocks.manager import BlockManager
from src.coverage.coverage_types import CoverageAssessment
from src.crossref.crossref_types import CrossReferenceRecord
from src.m07.m07_types import M07EvidencePack
from src.models.norm_unit import NormUnit
from src.models.source_document import SourceDocument
from src.utils.ids import build_id


class M07Support:
    def __init__(self, *, block_manager: Optional[BlockManager] = None) -> None:
        self.block_manager = block_manager or BlockManager()

    def build(
        self,
        *,
        case_id: str,
        source_documents: Iterable[SourceDocument],
        norm_units: Iterable[NormUnit],
        crossref_records: Optional[Iterable[CrossReferenceRecord]] = None,
        coverage_assessment: Optional[CoverageAssessment] = None,
        require_m07: bool = True,
        trace_id: str = '',
    ) -> M07EvidencePack:
        source_documents = list(source_documents)
        norm_units = list(norm_units)
        crossref_records = list(crossref_records or [])

        ordered_units = sorted(
            norm_units,
            key=lambda unit: (unit.position_index, unit.articolo or '', unit.comma or '', unit.allegato or ''),
        )

        annex_refs = sorted({unit.allegato for unit in ordered_units if unit.allegato})
        annex_refs.extend(
            record.crossref_text for record in crossref_records if record.crossref_type == 'allegato' and record.crossref_text not in annex_refs
        )

        crossref_refs = [record.crossref_text for record in crossref_records]
        missing_elements = []
        if coverage_assessment is not None:
            missing_elements.extend(coverage_assessment.missing_sources)
            missing_elements.extend(coverage_assessment.missing_annexes)
            missing_elements.extend(coverage_assessment.missing_crossrefs)

        if not ordered_units:
            missing_elements.append('norm_units_missing')

        status = 'READY'
        if missing_elements:
            status = 'PARTIAL'

        pack = M07EvidencePack(
            record_id=build_id('m07packrec'),
            record_type='M07EvidencePack',
            m07_pack_id=build_id('m07pack'),
            case_id=case_id,
            source_ids=[doc.source_id for doc in source_documents if doc.source_id],
            norm_unit_ids=[unit.norm_unit_id for unit in ordered_units if unit.norm_unit_id],
            ordered_reading_sequence=[unit.hierarchy_path or unit.norm_unit_id for unit in ordered_units],
            annex_refs=annex_refs,
            crossref_refs=crossref_refs,
            coverage_ref_id=coverage_assessment.coverage_id if coverage_assessment else None,
            missing_elements=missing_elements,
            m07_support_status=status,
            human_completion_required=True,
            trace_id=trace_id,
        )

        if require_m07 and missing_elements:
            self.block_manager.open_block(
                case_id=case_id,
                block_code=codes.M07_REQUIRED,
                block_category='m07',
                block_severity='CRITICAL',
                origin_module='M07Support',
                affected_object_type='M07EvidencePack',
                affected_object_id=pack.m07_pack_id,
                block_reason='Supporto documentale M07 incompleto o lettura integrale ancora necessaria',
                release_condition='Integrare il perimetro documentale e completare il presidio M07 nel Livello A',
                trace_id=trace_id,
            )

        return pack
