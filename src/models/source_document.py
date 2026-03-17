from dataclasses import dataclass
from typing import Optional

from src.models.base import BaseRecord


@dataclass
class SourceDocument(BaseRecord):
    source_id: str = ''
    corpus_domain_id: str = 'corpus_enti_locali'
    source_type: str = 'norma'
    atto_tipo: str = ''
    atto_numero: str = ''
    atto_anno: str = ''
    titolo: str = ''
    ente_emittente: str = ''
    pubblicazione: str = ''
    data_pubblicazione: str = ''
    uri_ufficiale: str = ''
    stato_verifica_fonte: str = 'UNVERIFIED'
    stato_vigenza: str = 'VIGENZA_INCERTA'
    versione_documento: str = 'v1'
    hash_contenuto: str = ''
    authoritative_flag: bool = False
    last_verified_at: Optional[str] = None
    human_verified_flag: bool = False
    document_status: str = 'RAW'
    parse_ready_flag: bool = False
    index_ready_flag: bool = False
    annex_presence_flag: bool = False
    multivigente_flag: bool = False
