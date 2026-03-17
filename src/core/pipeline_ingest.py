from dataclasses import dataclass
from typing import Dict, List

from src.audit.logger import AuditLogger
from src.audit.shadow import ShadowTracer
from src.blocks.manager import BlockManager
from src.ingestion.metadata_enricher import MetadataEnricher
from src.ingestion.source_validator import SourceValidator
from src.parsing.parser import Parser
from src.parsing.segmenter import Segmenter
from src.utils.ids import build_id


@dataclass
class IngestResult:
    case_id: str
    trace_id: str
    source_document: object | None
    norm_units: list
    chunks: list
    blocks: list
    audit_events: list
    shadow_trace: object


class IngestionPipeline:
    def __init__(self) -> None:
        self.block_manager = BlockManager()
        self.audit_logger = AuditLogger()
        self.shadow_tracer = ShadowTracer()
        self.validator = SourceValidator(self.block_manager)
        self.parser = Parser(self.block_manager)
        self.segmenter = Segmenter(self.block_manager)
        self.enricher = MetadataEnricher(self.block_manager)

    def run(self, *, case_id: str, text: str, metadata: Dict[str, str]) -> IngestResult:
        trace_id = build_id('trace')
        shadow = self.shadow_tracer.start_trace(case_id=case_id, trace_id=trace_id)

        self.audit_logger.log_event(
            case_id=case_id,
            event_type='PIPELINE_START',
            event_phase='INGESTION',
            origin_module='IngestionPipeline',
            trace_id=trace_id,
        )
        self.shadow_tracer.append(shadow, module='IngestionPipeline', note='Avvio pipeline')

        validation = self.validator.validate(case_id=case_id, text=text, metadata=metadata, trace_id=trace_id)
        self.shadow_tracer.append(shadow, module='SourceValidator', note='Validazione fonte eseguita')

        if not validation.valid or not validation.source_document:
            return IngestResult(
                case_id=case_id,
                trace_id=trace_id,
                source_document=None,
                norm_units=[],
                chunks=[],
                blocks=self.block_manager.list_open_blocks(case_id=case_id),
                audit_events=self.audit_logger.events,
                shadow_trace=shadow,
            )

        source_document = validation.source_document
        self.audit_logger.log_event(
            case_id=case_id,
            event_type='SOURCE_VALIDATED',
            event_phase='INGESTION',
            origin_module='SourceValidator',
            trace_id=trace_id,
        )

        norm_units = self.parser.parse(case_id=case_id, source_document=source_document, text=text, trace_id=trace_id)
        self.shadow_tracer.append(shadow, module='Parser', note=f'Unità normative generate: {len(norm_units)}')

        chunks = self.segmenter.segment(case_id=case_id, norm_units=norm_units, trace_id=trace_id)
        self.shadow_tracer.append(shadow, module='Segmenter', note=f'Chunk generati: {len(chunks)}')

        source_document, norm_units, chunks = self.enricher.enrich(
            case_id=case_id,
            source_document=source_document,
            norm_units=norm_units,
            chunks=chunks,
            trace_id=trace_id,
        )
        self.shadow_tracer.append(shadow, module='MetadataEnricher', note='Metadati arricchiti')

        self.audit_logger.log_event(
            case_id=case_id,
            event_type='PIPELINE_END',
            event_phase='INGESTION',
            origin_module='IngestionPipeline',
            trace_id=trace_id,
            event_status='OK' if not self.block_manager.has_critical_blocks(case_id=case_id) else 'BLOCKED',
        )

        return IngestResult(
            case_id=case_id,
            trace_id=trace_id,
            source_document=source_document,
            norm_units=norm_units,
            chunks=chunks,
            blocks=self.block_manager.list_open_blocks(case_id=case_id),
            audit_events=self.audit_logger.events,
            shadow_trace=shadow,
        )
