import re
from typing import List, Tuple

from src.blocks import codes
from src.blocks.manager import BlockManager
from src.models.norm_unit import NormUnit
from src.models.source_document import SourceDocument
from src.utils.ids import build_id


ARTICLE_PATTERN = re.compile(
    r'(?im)^\s*art\.?\s*(\d+[\-/a-zA-Z]*)\s*(?:[-–—:]\s*(.*))?$'
)
COMMA_PATTERN = re.compile(r'(?m)^\s*(\d+[\-a-z]*)\.\s+')


class Parser:
    def __init__(self, block_manager: BlockManager) -> None:
        self.block_manager = block_manager

    def parse(
        self,
        *,
        case_id: str,
        source_document: SourceDocument,
        text: str,
        trace_id: str = '',
    ) -> List[NormUnit]:
        matches = list(ARTICLE_PATTERN.finditer(text))
        if not matches:
            self.block_manager.open_block(
                case_id=case_id,
                block_code=codes.PARSE_INCONSISTENT,
                block_category='parse',
                block_severity='CRITICAL',
                origin_module='Parser',
                affected_object_type='SourceDocument',
                affected_object_id=source_document.source_id,
                block_reason='Nessun articolo riconosciuto dal parser',
                trace_id=trace_id,
            )
            return []

        units: List[NormUnit] = []
        for idx, match in enumerate(matches, start=1):
            art_num = match.group(1).strip()
            rubrica = (match.group(2) or '').strip()
            start = match.end()
            end = matches[idx].start() if idx < len(matches) else len(text)
            body = text[start:end].strip()

            if not body:
                continue

            comma_matches = list(COMMA_PATTERN.finditer(body))
            if not comma_matches:
                units.append(
                    NormUnit(
                        record_id=build_id('normunitrec'),
                        record_type='NormUnit',
                        norm_unit_id=build_id('normunit'),
                        source_id=source_document.source_id,
                        unit_type='ARTICOLO',
                        articolo=art_num,
                        rubrica=rubrica,
                        testo_unita=body,
                        position_index=idx,
                        hierarchy_path=f"articolo:{art_num}",
                        trace_id=trace_id,
                    )
                )
                continue

            for c_idx, c_match in enumerate(comma_matches, start=1):
                comma_num = c_match.group(1).strip()
                c_start = c_match.end()
                c_end = comma_matches[c_idx].start() if c_idx < len(comma_matches) else len(body)
                comma_text = body[c_start:c_end].strip()
                units.append(
                    NormUnit(
                        record_id=build_id('normunitrec'),
                        record_type='NormUnit',
                        norm_unit_id=build_id('normunit'),
                        source_id=source_document.source_id,
                        unit_type='COMMA',
                        articolo=art_num,
                        comma=comma_num,
                        rubrica=rubrica,
                        testo_unita=comma_text,
                        position_index=idx * 100 + c_idx,
                        hierarchy_path=f"articolo:{art_num}/comma:{comma_num}",
                        trace_id=trace_id,
                    )
                )

        if not units:
            self.block_manager.open_block(
                case_id=case_id,
                block_code=codes.PARSE_INCONSISTENT,
                block_category='parse',
                block_severity='CRITICAL',
                origin_module='Parser',
                affected_object_type='SourceDocument',
                affected_object_id=source_document.source_id,
                block_reason='Parsing privo di unità normative utilizzabili',
                trace_id=trace_id,
            )
        return units
