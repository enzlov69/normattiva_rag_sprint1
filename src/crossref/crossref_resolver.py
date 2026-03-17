import re
from typing import Iterable, List, Optional

from src.blocks import codes
from src.blocks.manager import BlockManager
from src.crossref.crossref_types import CrossReferenceRecord
from src.models.norm_unit import NormUnit
from src.models.source_document import SourceDocument
from src.utils.ids import build_id


class CrossReferenceResolver:
    ARTICLE_PATTERN = re.compile(r'\b(?:articolo|art\.)\s*(\d+[\w/-]*)', re.IGNORECASE)
    ANNEX_PATTERN = re.compile(r'\ballegato\s+([A-Z0-9]+)', re.IGNORECASE)

    def __init__(self, *, block_manager: Optional[BlockManager] = None) -> None:
        self.block_manager = block_manager or BlockManager()

    def resolve(
        self,
        *,
        case_id: str,
        source_document: SourceDocument,
        norm_unit: NormUnit,
        known_norm_units: Optional[Iterable[NormUnit]] = None,
        essential_ref_default: bool = True,
        trace_id: str = '',
    ) -> List[CrossReferenceRecord]:
        text = norm_unit.testo_unita or ''
        known_norm_units = list(known_norm_units or [])
        records: List[CrossReferenceRecord] = []

        for article in self.ARTICLE_PATTERN.findall(text):
            target = self._match_article(article, known_norm_units)
            resolved = target is not None
            record = CrossReferenceRecord(
                record_id=build_id('crossrefrec'),
                record_type='CrossReferenceRecord',
                crossref_id=build_id('crossref'),
                source_id=source_document.source_id,
                norm_unit_id=norm_unit.norm_unit_id,
                crossref_type='interno',
                crossref_text=f'articolo {article}',
                target_source_id=source_document.source_id if resolved else None,
                target_norm_unit_id=target.norm_unit_id if resolved else None,
                target_uri=source_document.uri_ufficiale if resolved else None,
                resolution_status='RESOLVED' if resolved else 'UNRESOLVED',
                essential_ref_flag=essential_ref_default,
                resolved_flag=resolved,
                block_if_unresolved_flag=essential_ref_default and not resolved,
                trace_id=trace_id,
            )
            records.append(record)
            if record.block_if_unresolved_flag:
                self._open_unresolved_block(case_id=case_id, record=record, trace_id=trace_id)

        for annex in self.ANNEX_PATTERN.findall(text):
            record = CrossReferenceRecord(
                record_id=build_id('crossrefrec'),
                record_type='CrossReferenceRecord',
                crossref_id=build_id('crossref'),
                source_id=source_document.source_id,
                norm_unit_id=norm_unit.norm_unit_id,
                crossref_type='allegato',
                crossref_text=f'allegato {annex}',
                target_source_id=source_document.source_id,
                target_uri=source_document.uri_ufficiale,
                resolution_status='PENDING_MANUAL_CHECK',
                essential_ref_flag=essential_ref_default,
                resolved_flag=False,
                block_if_unresolved_flag=essential_ref_default,
                trace_id=trace_id,
            )
            records.append(record)
            if record.block_if_unresolved_flag:
                self._open_unresolved_block(case_id=case_id, record=record, trace_id=trace_id)

        return records

    @staticmethod
    def _match_article(article: str, known_norm_units: Iterable[NormUnit]) -> Optional[NormUnit]:
        for norm_unit in known_norm_units:
            if (norm_unit.articolo or '').strip().lower() == article.strip().lower():
                return norm_unit
        return None

    def _open_unresolved_block(self, *, case_id: str, record: CrossReferenceRecord, trace_id: str) -> None:
        self.block_manager.open_block(
            case_id=case_id,
            block_code=codes.CROSSREF_UNRESOLVED,
            block_category='crossref',
            block_severity='CRITICAL',
            origin_module='CrossReferenceResolver',
            affected_object_type='CrossReferenceRecord',
            affected_object_id=record.crossref_id,
            block_reason=f'Rinvio essenziale non ricostruito: {record.crossref_text}',
            release_condition='Ricostruire il rinvio normativo o verificare manualmente il riferimento',
            trace_id=trace_id,
        )
