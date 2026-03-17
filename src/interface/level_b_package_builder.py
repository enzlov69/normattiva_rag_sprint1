from typing import Optional

from src.audit.audit_integrity import AuditIntegrityResult
from src.models.shadow_trace import ShadowTrace
from src.reporting.report_types import TechnicalReport
from src.utils.ids import build_id

from src.interface.level_b_package_types import LevelBDeliveryPackage


class LevelBPackageBuilder:
    def build(
        self,
        *,
        technical_report: TechnicalReport,
        audit_integrity_result: Optional[AuditIntegrityResult] = None,
        shadow_trace: Optional[ShadowTrace] = None,
        trace_id: str = '',
    ) -> LevelBDeliveryPackage:
        audit_integrity_result = audit_integrity_result or AuditIntegrityResult(complete=False)

        package_status = 'READY'
        if technical_report.block_ids or technical_report.errors:
            package_status = 'BLOCKED'
        elif technical_report.warnings:
            package_status = 'READY_WITH_WARNINGS'

        if not audit_integrity_result.complete and package_status == 'READY':
            package_status = 'READY_WITH_WARNINGS'

        return LevelBDeliveryPackage(
            record_id=build_id('levelbpackrec'),
            record_type='LevelBDeliveryPackage',
            package_id=build_id('levelbpack'),
            case_id=technical_report.case_id,
            report_id=technical_report.report_id,
            report_status=technical_report.report_status,
            support_only_flag=True,
            source_ids=list(technical_report.source_ids),
            valid_citation_ids=list(technical_report.valid_citation_ids),
            blocked_citation_ids=list(technical_report.blocked_citation_ids),
            citation_status_summary=dict(technical_report.citation_status_summary),
            vigenza_status_summary=dict(technical_report.vigenza_status_summary),
            crossref_status_summary=dict(technical_report.crossref_status_summary),
            coverage_ref_id=technical_report.coverage_ref_id,
            coverage_status=technical_report.coverage_status,
            m07_ref_id=technical_report.m07_ref_id,
            m07_status=technical_report.m07_status,
            warnings=list(technical_report.warnings),
            errors=list(technical_report.errors),
            block_ids=list(technical_report.block_ids),
            block_codes=list(technical_report.block_codes),
            audit_complete=audit_integrity_result.complete,
            audit_checked_events=audit_integrity_result.checked_events,
            audit_missing_phases=list(audit_integrity_result.missing_phases),
            audit_missing_modules=list(audit_integrity_result.missing_modules),
            shadow_id=shadow_trace.shadow_id if shadow_trace else None,
            executed_modules=list(shadow_trace.executed_modules) if shadow_trace else [],
            documents_seen=list(shadow_trace.documents_seen) if shadow_trace else [],
            norm_units_seen=list(shadow_trace.norm_units_seen) if shadow_trace else [],
            shadow_block_codes=list(shadow_trace.blocks) if shadow_trace else [],
            package_status=package_status,
            trace_id=trace_id or technical_report.trace_id,
        )
