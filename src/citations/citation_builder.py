from dataclasses import dataclass, field
from typing import List, Optional

from src.models.base import BaseRecord
from src.models.norm_unit import NormUnit
from src.models.source_document import SourceDocument
from src.utils.ids import build_id


@dataclass
class CitationRecord(BaseRecord):
    citation_id: str = ''
    case_id: str = ''
    source_id: str = ''
    norm_unit_id: str = ''
    chunk_id: Optional[str] = None
    atto_tipo: str = ''
    atto_numero: str = ''
    atto_anno: str = ''
    articolo: str = ''
    comma: Optional[str] = None
    allegato: Optional[str] = None
    uri_ufficiale: str = ''
    stato_vigenza: str = ''
    citation_text: str = ''
    citation_status: str = 'DRAFT'
    source_authority_flag: bool = False
    reconstructible_flag: bool = False
    opponibile_flag: bool = False
    validation_errors: List[str] = field(default_factory=list)
    block_refs: List[str] = field(default_factory=list)


class CitationBuilder:
    def build(
        self,
        *,
        case_id: str,
        source_document: SourceDocument,
        norm_unit: NormUnit,
        chunk_id: Optional[str] = None,
        trace_id: str = '',
    ) -> CitationRecord:
        citation_text = f"{source_document.atto_tipo} {source_document.atto_numero}/{source_document.atto_anno}, art. {norm_unit.articolo}"
        if norm_unit.comma:
            citation_text += f", comma {norm_unit.comma}"
        if norm_unit.allegato:
            citation_text += f", allegato {norm_unit.allegato}"

        return CitationRecord(
            record_id=build_id('citrec'),
            record_type='CitationRecord',
            citation_id=build_id('citation'),
            case_id=case_id,
            source_id=source_document.source_id,
            norm_unit_id=norm_unit.norm_unit_id,
            chunk_id=chunk_id,
            atto_tipo=source_document.atto_tipo,
            atto_numero=source_document.atto_numero,
            atto_anno=source_document.atto_anno,
            articolo=norm_unit.articolo,
            comma=norm_unit.comma,
            allegato=norm_unit.allegato,
            uri_ufficiale=source_document.uri_ufficiale,
            stato_vigenza=source_document.stato_vigenza,
            citation_text=citation_text,
            source_authority_flag=source_document.authoritative_flag,
            trace_id=trace_id,
        )
