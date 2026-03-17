from dataclasses import dataclass
from typing import Any, List, Optional

from src.audit.logger import AuditLogger
from src.audit.shadow import ShadowTracer
from src.blocks import codes
from src.blocks.manager import BlockManager
from src.connectors.normattiva_errors import (
    NormattivaError,
    NormattivaInvalidPayloadError,
    NormattivaMetadataError,
    NormattivaSourceUnverifiedError,
)
from src.connectors.normattiva_mapper import NormattivaMapper
from src.ingestion.metadata_enricher import MetadataEnricher
from src.models.block_event import BlockEvent
from src.models.chunk_record import ChunkRecord
from src.models.norm_unit import NormUnit
from src.models.shadow_trace import ShadowTrace
from src.models.source_document import SourceDocument
from src.models.audit_event import AuditEvent
from src.parsing.segmenter import Segmenter
from src.utils.ids import build_id


@dataclass
class NormattivaIngestResult:
    case_id: str
    trace_id: str
    source_document: Optional[SourceDocument]
    norm_units: List[NormUnit]
    chunks: List[ChunkRecord]
    blocks: List[BlockEvent]
    audit_events: List[AuditEvent]
    shadow_trace: ShadowTrace


class NormattivaIngestor:
    """Bridges raw Normattiva payloads to the internal Sprint 1 pipeline objects."""

    def __init__(
        self,
        *,
        block_manager: Optional[BlockManager] = None,
        audit_logger: Optional[AuditLogger] = None,
        shadow_tracer: Optional[ShadowTracer] = None,
        mapper: Optional[NormattivaMapper] = None,
        segmenter: Optional[Segmenter] = None,
        enricher: Optional[MetadataEnricher] = None,
    ) -> None:
        self.block_manager = block_manager or BlockManager()
        self.audit_logger = audit_logger or AuditLogger()
        self.shadow_tracer = shadow_tracer or ShadowTracer()
        self.mapper = mapper or NormattivaMapper(self.block_manager)
        self.segmenter = segmenter or Segmenter(self.block_manager)
        self.enricher = enricher or MetadataEnricher(self.block_manager)

    def ingest_from_payloads(
        self,
        *,
        case_id: str,
        search_item: dict[str, Any],
        detail_payload: dict[str, Any],
        trace_id: str = "",
    ) -> NormattivaIngestResult:
        trace_id = trace_id or build_id("trace")
        shadow = self.shadow_tracer.start_trace(case_id=case_id, trace_id=trace_id)

        self.audit_logger.log_event(
            case_id=case_id,
            event_type="NORMATTIVA_INGEST_START",
            event_phase="INGESTION",
            origin_module="NormattivaIngestor",
            trace_id=trace_id,
        )
        self.shadow_tracer.append(shadow, module="NormattivaIngestor", note="Avvio ingestion payload Normattiva")

        try:
            if not isinstance(search_item, dict) or not search_item:
                raise NormattivaInvalidPayloadError("Search item Normattiva non valido o vuoto")
            if not isinstance(detail_payload, dict) or not detail_payload:
                raise NormattivaInvalidPayloadError("Detail payload Normattiva non valido o vuoto")

            source_document = self.mapper.map_search_item_to_source_document(
                case_id=case_id,
                item=search_item,
                trace_id=trace_id,
            )
            self.shadow_tracer.append(shadow, module="NormattivaMapper", note="SourceDocument mappato")
            self.audit_logger.log_event(
                case_id=case_id,
                event_type="NORMATTIVA_SOURCE_MAPPED",
                event_phase="INGESTION",
                origin_module="NormattivaMapper",
                trace_id=trace_id,
            )

            norm_units = self.mapper.map_detail_payload_to_norm_units(
                case_id=case_id,
                source_document=source_document,
                detail_payload=detail_payload,
                trace_id=trace_id,
            )
            self.shadow_tracer.append(shadow, module="NormattivaMapper", note=f"NormUnit generate: {len(norm_units)}")

            chunks = self.segmenter.segment(case_id=case_id, norm_units=norm_units, trace_id=trace_id)
            self.shadow_tracer.append(shadow, module="Segmenter", note=f"Chunk generati: {len(chunks)}")

            source_document, norm_units, chunks = self.enricher.enrich(
                case_id=case_id,
                source_document=source_document,
                norm_units=norm_units,
                chunks=chunks,
                trace_id=trace_id,
            )
            self.audit_logger.log_event(
                case_id=case_id,
                event_type="NORMATTIVA_INGEST_COMPLETE",
                event_phase="INGESTION",
                origin_module="NormattivaIngestor",
                trace_id=trace_id,
            )
            self.shadow_tracer.append(shadow, module="MetadataEnricher", note="Enrichment completato")

            return NormattivaIngestResult(
                case_id=case_id,
                trace_id=trace_id,
                source_document=source_document,
                norm_units=norm_units,
                chunks=chunks,
                blocks=self.block_manager.list_open_blocks(case_id=case_id),
                audit_events=list(self.audit_logger.events),
                shadow_trace=shadow,
            )
        except NormattivaSourceUnverifiedError as exc:
            self._open_block(
                case_id=case_id,
                trace_id=trace_id,
                code=codes.SOURCE_UNVERIFIED,
                category="fonte",
                reason=str(exc),
            )
            self.shadow_tracer.append(shadow, module="NormattivaIngestor", note=str(exc), block_code=codes.SOURCE_UNVERIFIED)
        except (NormattivaMetadataError, NormattivaInvalidPayloadError) as exc:
            self._open_block(
                case_id=case_id,
                trace_id=trace_id,
                code=codes.METADATA_INSUFFICIENT,
                category="metadata",
                reason=str(exc),
            )
            self.shadow_tracer.append(shadow, module="NormattivaIngestor", note=str(exc), block_code=codes.METADATA_INSUFFICIENT)
        except NormattivaError as exc:
            self._open_block(
                case_id=case_id,
                trace_id=trace_id,
                code=codes.PARSE_INCONSISTENT,
                category="normattiva",
                reason=str(exc),
            )
            self.shadow_tracer.append(shadow, module="NormattivaIngestor", note=str(exc), block_code=codes.PARSE_INCONSISTENT)

        self.audit_logger.log_event(
            case_id=case_id,
            event_type="NORMATTIVA_INGEST_FAILED",
            event_phase="INGESTION",
            origin_module="NormattivaIngestor",
            event_status="FAILED",
            trace_id=trace_id,
        )
        return NormattivaIngestResult(
            case_id=case_id,
            trace_id=trace_id,
            source_document=None,
            norm_units=[],
            chunks=[],
            blocks=self.block_manager.list_open_blocks(case_id=case_id),
            audit_events=list(self.audit_logger.events),
            shadow_trace=shadow,
        )

    def _open_block(self, *, case_id: str, trace_id: str, code: str, category: str, reason: str) -> None:
        self.block_manager.open_block(
            case_id=case_id,
            block_code=code,
            block_category=category,
            block_severity="CRITICAL",
            origin_module="NormattivaIngestor",
            affected_object_type="NormattivaPayload",
            affected_object_id="payload",
            block_reason=reason,
            trace_id=trace_id,
        )
