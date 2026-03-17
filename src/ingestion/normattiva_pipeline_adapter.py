from pathlib import Path
from typing import Optional

from src.ingestion.normattiva_document_loader import NormattivaDocumentLoader
from src.ingestion.normattiva_ingestor import NormattivaIngestResult, NormattivaIngestor


class NormattivaPipelineAdapter:
    """Loads saved Normattiva payloads and forwards them into the internal ingestion pipeline."""

    def __init__(
        self,
        *,
        loader: Optional[NormattivaDocumentLoader] = None,
        ingestor: Optional[NormattivaIngestor] = None,
    ) -> None:
        self.loader = loader or NormattivaDocumentLoader()
        self.ingestor = ingestor or NormattivaIngestor()

    def run_from_files(
        self,
        *,
        case_id: str,
        search_item_path: str | Path,
        detail_payload_path: str | Path,
        trace_id: str = "",
    ) -> NormattivaIngestResult:
        search_item = self.loader.load_json_file(search_item_path)
        detail_payload = self.loader.load_json_file(detail_payload_path)
        return self.ingestor.ingest_from_payloads(
            case_id=case_id,
            search_item=search_item,
            detail_payload=detail_payload,
            trace_id=trace_id,
        )
