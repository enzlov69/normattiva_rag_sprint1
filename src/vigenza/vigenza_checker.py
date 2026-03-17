from typing import Optional

from src.blocks import codes
from src.blocks.manager import BlockManager
from src.models.norm_unit import NormUnit
from src.models.source_document import SourceDocument
from src.utils.ids import build_id
from src.vigenza.vigenza_types import VigenzaRecord


class VigenzaChecker:
    ALLOWED_STATUSES = {
        'VIGENTE_VERIFICATA',
        'NON_VIGENTE',
        'VIGENZA_INCERTA',
        'IMPOSSIBILE_VERIFICARE',
    }

    def __init__(self, *, block_manager: Optional[BlockManager] = None) -> None:
        self.block_manager = block_manager or BlockManager()

    def check(
        self,
        *,
        case_id: str,
        source_document: SourceDocument,
        norm_unit: Optional[NormUnit] = None,
        explicit_status: Optional[str] = None,
        essential_point_flag: bool = False,
        trace_id: str = '',
    ) -> VigenzaRecord:
        status = (explicit_status or source_document.stato_vigenza or 'VIGENZA_INCERTA').strip().upper()
        if status not in self.ALLOWED_STATUSES:
            status = 'IMPOSSIBILE_VERIFICARE'

        confidence = 1.0 if status == 'VIGENTE_VERIFICATA' else 0.9 if status == 'NON_VIGENTE' else 0.25
        block_if_uncertain = essential_point_flag and status in {'VIGENZA_INCERTA', 'IMPOSSIBILE_VERIFICARE'}

        record = VigenzaRecord(
            record_id=build_id('vigenzarec'),
            record_type='VigenzaRecord',
            vigenza_id=build_id('vigenza'),
            source_id=source_document.source_id,
            norm_unit_id=norm_unit.norm_unit_id if norm_unit else '',
            vigore_status=status,
            vigore_basis='source_document.stato_vigenza' if not explicit_status else 'explicit_status',
            verification_method='documentale',
            verification_confidence=confidence,
            essential_point_flag=essential_point_flag,
            block_if_uncertain_flag=block_if_uncertain,
            trace_id=trace_id,
        )

        if block_if_uncertain:
            self.block_manager.open_block(
                case_id=case_id,
                block_code=codes.VIGENZA_UNCERTAIN,
                block_category='vigenza',
                block_severity='CRITICAL',
                origin_module='VigenzaChecker',
                affected_object_type='VigenzaRecord',
                affected_object_id=record.vigenza_id,
                block_reason='Vigenza non chiarita su punto essenziale',
                release_condition='Integrare verifica di vigenza su fonte ufficiale',
                trace_id=trace_id,
            )

        return record
