from dataclasses import dataclass
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from src.blocks import codes
from src.blocks.manager import BlockManager
from src.config.settings import OFFICIAL_SOURCE_DOMAINS
from src.models.source_document import SourceDocument
from src.utils.hashing import sha256_text
from src.utils.ids import build_id
from src.utils.timestamps import utc_now_iso


@dataclass
class ValidationResult:
    valid: bool
    source_document: SourceDocument | None
    errors: List[str]
    block_codes: List[str]


class SourceValidator:
    REQUIRED_METADATA = ('atto_tipo', 'atto_numero', 'atto_anno', 'titolo', 'uri_ufficiale')

    def __init__(self, block_manager: BlockManager) -> None:
        self.block_manager = block_manager

    def validate(
        self,
        *,
        case_id: str,
        text: str,
        metadata: Dict[str, str],
        trace_id: str = '',
    ) -> ValidationResult:
        errors: List[str] = []
        block_codes: List[str] = []

        missing = [key for key in self.REQUIRED_METADATA if not metadata.get(key)]
        if missing:
            errors.append(f'Metadati mancanti: {", ".join(missing)}')
            self.block_manager.open_block(
                case_id=case_id,
                block_code=codes.METADATA_INSUFFICIENT,
                block_category='metadata',
                block_severity='CRITICAL',
                origin_module='SourceValidator',
                affected_object_type='SourceDocument',
                affected_object_id='pending',
                block_reason=errors[-1],
                trace_id=trace_id,
            )
            block_codes.append(codes.METADATA_INSUFFICIENT)

        uri = metadata.get('uri_ufficiale', '')
        parsed = urlparse(uri)
        domain_ok = parsed.netloc.lower() in OFFICIAL_SOURCE_DOMAINS
        if not uri or not domain_ok:
            reason = 'Fonte non ufficiale o URI non identificabile'
            errors.append(reason)
            self.block_manager.open_block(
                case_id=case_id,
                block_code=codes.SOURCE_UNVERIFIED,
                block_category='fonte',
                block_severity='CRITICAL',
                origin_module='SourceValidator',
                affected_object_type='SourceDocument',
                affected_object_id='pending',
                block_reason=reason,
                trace_id=trace_id,
            )
            block_codes.append(codes.SOURCE_UNVERIFIED)

        if errors:
            return ValidationResult(valid=False, source_document=None, errors=errors, block_codes=block_codes)

        doc = SourceDocument(
            record_id=build_id('srcdocrec'),
            record_type='SourceDocument',
            source_id=build_id('source'),
            atto_tipo=metadata['atto_tipo'],
            atto_numero=str(metadata['atto_numero']),
            atto_anno=str(metadata['atto_anno']),
            titolo=metadata['titolo'],
            ente_emittente=metadata.get('ente_emittente', 'Stato'),
            pubblicazione=metadata.get('pubblicazione', 'Normattiva'),
            data_pubblicazione=metadata.get('data_pubblicazione', ''),
            uri_ufficiale=metadata['uri_ufficiale'],
            stato_verifica_fonte='VERIFIED',
            stato_vigenza=metadata.get('stato_vigenza', 'VIGENZA_INCERTA'),
            versione_documento=metadata.get('versione_documento', 'v1'),
            hash_contenuto=sha256_text(text),
            authoritative_flag=True,
            last_verified_at=utc_now_iso(),
            human_verified_flag=False,
            document_status='VERIFIED',
            parse_ready_flag=True,
            trace_id=trace_id,
        )
        return ValidationResult(valid=True, source_document=doc, errors=[], block_codes=[])
