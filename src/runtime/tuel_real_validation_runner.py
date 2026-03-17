from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.audit.audit_integrity import AuditIntegrity
from src.citations.citation_builder import CitationBuilder, CitationRecord
from src.citations.citation_validator import CitationValidator
from src.coverage.coverage_estimator import CoverageEstimator
from src.crossref.crossref_resolver import CrossReferenceResolver
from src.ingestion.normattiva_document_loader import NormattivaDocumentLoader
from src.ingestion.normattiva_ingestor import NormattivaIngestResult, NormattivaIngestor
from src.interface.level_b_package_builder import LevelBPackageBuilder
from src.interface.level_b_package_types import LevelBDeliveryPackage
from src.interface.level_b_package_validator import LevelBPackageValidationResult, LevelBPackageValidator
from src.m07.m07_support import M07Support
from src.reporting.report_builder import ReportBuilder
from src.reporting.report_types import TechnicalReport
from src.retrieval.retrieval_service import RetrievalQuery, RetrievalResult, RetrievalService
from src.runtime.flow_runner import EndToEndFlowRunner
from src.runtime.runtime_types import EndToEndFlowResult
from src.vigenza.vigenza_checker import VigenzaChecker


@dataclass
class TuelRealValidationArtifacts:
    ingest_result: NormattivaIngestResult
    retrieval_query: RetrievalQuery
    retrieval_results: list[RetrievalResult]
    citations: list[CitationRecord]
    technical_report: TechnicalReport
    package: LevelBDeliveryPackage
    package_validation: LevelBPackageValidationResult
    runtime_result: EndToEndFlowResult


class TuelRealValidationRunner:
    def __init__(
        self,
        *,
        loader: Optional[NormattivaDocumentLoader] = None,
        ingestor: Optional[NormattivaIngestor] = None,
        retrieval_service: Optional[RetrievalService] = None,
        citation_builder: Optional[CitationBuilder] = None,
        citation_validator: Optional[CitationValidator] = None,
        vigenza_checker: Optional[VigenzaChecker] = None,
        crossref_resolver: Optional[CrossReferenceResolver] = None,
        coverage_estimator: Optional[CoverageEstimator] = None,
        m07_support: Optional[M07Support] = None,
        report_builder: Optional[ReportBuilder] = None,
        audit_integrity: Optional[AuditIntegrity] = None,
        package_builder: Optional[LevelBPackageBuilder] = None,
        package_validator: Optional[LevelBPackageValidator] = None,
        flow_runner: Optional[EndToEndFlowRunner] = None,
    ) -> None:
        self.loader = loader or NormattivaDocumentLoader()
        self.ingestor = ingestor or NormattivaIngestor()
        self.retrieval_service = retrieval_service or RetrievalService(block_manager=self.ingestor.block_manager)
        self.citation_builder = citation_builder or CitationBuilder()
        self.citation_validator = citation_validator or CitationValidator(self.ingestor.block_manager)
        self.vigenza_checker = vigenza_checker or VigenzaChecker(block_manager=self.ingestor.block_manager)
        self.crossref_resolver = crossref_resolver or CrossReferenceResolver(block_manager=self.ingestor.block_manager)
        self.coverage_estimator = coverage_estimator or CoverageEstimator(block_manager=self.ingestor.block_manager)
        self.m07_support = m07_support or M07Support(block_manager=self.ingestor.block_manager)
        self.report_builder = report_builder or ReportBuilder()
        self.audit_integrity = audit_integrity or AuditIntegrity(block_manager=self.ingestor.block_manager)
        self.package_builder = package_builder or LevelBPackageBuilder()
        self.package_validator = package_validator or LevelBPackageValidator()
        self.flow_runner = flow_runner or EndToEndFlowRunner()

    @staticmethod
    def default_fixture_dir() -> Path:
        return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "normattiva"

    def run(
        self,
        *,
        case_id: str = "case_tuel_real",
        query_text: str = "consiglio sindaco dirigenti TUEL",
        trace_id: str = "trace_tuel_real",
        search_item_path: Optional[str | Path] = None,
        detail_payload_path: Optional[str | Path] = None,
        requested_output_type: str = "RAC_DRAFT",
    ) -> TuelRealValidationArtifacts:
        fixture_dir = self.default_fixture_dir()
        search_item_path = Path(search_item_path or (fixture_dir / "tuel_search_item_real.json"))
        detail_payload_path = Path(detail_payload_path or (fixture_dir / "tuel_detail_payload_real.json"))

        search_item = self.loader.load_json_file(search_item_path)
        detail_payload = self.loader.load_json_file(detail_payload_path)

        ingest_result = self.ingestor.ingest_from_payloads(
            case_id=case_id,
            search_item=search_item,
            detail_payload=detail_payload,
            trace_id=trace_id,
        )
        if ingest_result.source_document is None:
            raise RuntimeError("Ingestion TUEL reale fallita: SourceDocument assente")

        ingest_result.shadow_trace.documents_seen = [ingest_result.source_document.source_id]
        ingest_result.shadow_trace.norm_units_seen = [unit.norm_unit_id for unit in ingest_result.norm_units]

        retrieval_query, retrieval_results = self.retrieval_service.query(
            case_id=case_id,
            query_text=query_text,
            chunks=ingest_result.chunks,
            domain_target="enti_locali",
            top_k=10,
            trace_id=trace_id,
        )

        citations: list[CitationRecord] = []
        for norm_unit in ingest_result.norm_units:
            citation = self.citation_builder.build(
                case_id=case_id,
                source_document=ingest_result.source_document,
                norm_unit=norm_unit,
                trace_id=trace_id,
            )
            citations.append(self.citation_validator.validate(case_id=case_id, citation=citation, trace_id=trace_id))

        vigenza_records = [
            self.vigenza_checker.check(
                case_id=case_id,
                source_document=ingest_result.source_document,
                norm_unit=norm_unit,
                essential_point_flag=False,
                trace_id=trace_id,
            )
            for norm_unit in ingest_result.norm_units
        ]

        crossref_records = []
        for norm_unit in ingest_result.norm_units:
            crossref_records.extend(
                self.crossref_resolver.resolve(
                    case_id=case_id,
                    source_document=ingest_result.source_document,
                    norm_unit=norm_unit,
                    known_norm_units=ingest_result.norm_units,
                    essential_ref_default=True,
                    trace_id=trace_id,
                )
            )

        coverage = self.coverage_estimator.assess(
            case_id=case_id,
            query_id=retrieval_query.query_id,
            retrieval_results=retrieval_results,
            domain_target="enti_locali",
            expected_source_ids=[ingest_result.source_document.source_id],
            required_annex_refs=[],
            crossref_records=crossref_records,
            trace_id=trace_id,
        )

        m07_pack = self.m07_support.build(
            case_id=case_id,
            source_documents=[ingest_result.source_document],
            norm_units=ingest_result.norm_units,
            crossref_records=crossref_records,
            coverage_assessment=coverage,
            require_m07=True,
            trace_id=trace_id,
        )

        audit_integrity_result = self.audit_integrity.check(
            case_id=case_id,
            events=ingest_result.audit_events,
            required_phases=["INGESTION"],
            required_modules=["NormattivaIngestor", "NormattivaMapper"],
            trace_id=trace_id,
        )

        blocks = self.ingestor.block_manager.list_open_blocks(case_id=case_id)
        technical_report = self.report_builder.build(
            case_id=case_id,
            source_documents=[ingest_result.source_document],
            citations=citations,
            vigenza_records=vigenza_records,
            crossref_records=crossref_records,
            coverage_assessment=coverage,
            m07_pack=m07_pack,
            blocks=blocks,
            warnings=[],
            errors=[],
            trace_id=trace_id,
        )

        package = self.package_builder.build(
            technical_report=technical_report,
            audit_integrity_result=audit_integrity_result,
            shadow_trace=ingest_result.shadow_trace,
            trace_id=trace_id,
        )
        package_validation = self.package_validator.validate(package)
        if not package_validation.valid:
            raise RuntimeError("Pacchetto Livello B non valido: " + "; ".join(package_validation.errors))

        runtime_result = self.flow_runner.run(
            package,
            requested_output_type=requested_output_type,
            trace_id=trace_id,
        )

        return TuelRealValidationArtifacts(
            ingest_result=ingest_result,
            retrieval_query=retrieval_query,
            retrieval_results=retrieval_results,
            citations=citations,
            technical_report=technical_report,
            package=package,
            package_validation=package_validation,
            runtime_result=runtime_result,
        )


def run_tuel_real_validation() -> dict[str, object]:
    runner = TuelRealValidationRunner()
    artifacts = runner.run()

    return {
        "case_id": artifacts.runtime_result.case_id,
        "go_final_status": artifacts.runtime_result.go_final_status,
        "final_runtime_status": artifacts.runtime_result.final_runtime_status,
        "authorization_status": artifacts.runtime_result.authorization_status,
        "citations_total": len(artifacts.citations),
        "retrieval_results_total": len(artifacts.retrieval_results),
        "package_valid": artifacts.package_validation.valid,
        "open_blocks": len(artifacts.technical_report.block_ids),
        "block_codes": list(artifacts.technical_report.block_codes),
    }
