from typing import Dict, List, Optional, Tuple
import json

from src.config.live_api_settings import LiveApiSettings
from src.live_api.live_normattiva_client import LiveNormattivaClient
from src.live_api.live_request_builder import LiveRequestBuilder
from src.live_api.live_response_mapper import LiveResponseMapper
from src.models.chunk_record import ChunkRecord
from src.models.norm_unit import NormUnit
from src.models.source_document import SourceDocument


class LiveDetailService:
    def __init__(
        self,
        *,
        settings: Optional[LiveApiSettings] = None,
        client: Optional[LiveNormattivaClient] = None,
        request_builder: Optional[LiveRequestBuilder] = None,
        response_mapper: Optional[LiveResponseMapper] = None,
    ) -> None:
        self.settings = settings or LiveApiSettings()
        self.client = client or LiveNormattivaClient(self.settings)
        self.request_builder = request_builder or LiveRequestBuilder(self.settings)
        self.response_mapper = response_mapper or LiveResponseMapper()

    def fetch_and_map(
        self,
        *,
        case_id: str,
        search_item: Dict,
        trace_id: str = "",
        data_vigenza: Optional[str] = None,
    ) -> Tuple[SourceDocument, List[NormUnit], List[ChunkRecord]]:
        source_document = self.response_mapper.map_search_item_to_source_document(
            case_id=case_id,
            search_item=search_item,
            trace_id=trace_id,
        )
        detail_payload = self.response_mapper.build_detail_request_payload_from_search_item(
            search_item,
            data_vigenza=data_vigenza,
        )
        request = self.request_builder.build_detail_atto(detail_payload=detail_payload)
        response = self.client.execute(request)

        print("\n====== LIVE DETAIL REQUEST ======")
        print(json.dumps(detail_payload, indent=2, ensure_ascii=False))
        print("====== LIVE DETAIL RESPONSE PAYLOAD ======")
        print(json.dumps(response.payload, indent=2, ensure_ascii=False))
        print("=========================================\n")

        norm_units, chunks = self.response_mapper.map_detail_payload(
            case_id=case_id,
            source_document=source_document,
            detail_payload=response.payload,
            trace_id=trace_id,
        )
        return source_document, norm_units, chunks
