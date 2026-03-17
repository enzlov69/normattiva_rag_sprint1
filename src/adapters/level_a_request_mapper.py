from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.interface.level_b_package_types import LevelBDeliveryPackage
from src.models.base import BaseRecord
from src.utils.ids import build_id


@dataclass
class LevelARequestEnvelope(BaseRecord):
    request_id: str = ''
    case_id: str = ''
    source_package_id: str = ''
    source_report_id: str = ''
    support_only_flag: bool = True
    technical_status: str = 'READY'

    source_ids: List[str] = field(default_factory=list)
    valid_citation_ids: List[str] = field(default_factory=list)
    blocked_citation_ids: List[str] = field(default_factory=list)

    citation_status_summary: Dict[str, int] = field(default_factory=dict)
    vigenza_status_summary: Dict[str, int] = field(default_factory=dict)
    crossref_status_summary: Dict[str, int] = field(default_factory=dict)

    coverage_ref_id: Optional[str] = None
    coverage_status: Optional[str] = None
    m07_ref_id: Optional[str] = None
    m07_status: Optional[str] = None

    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    block_ids: List[str] = field(default_factory=list)
    block_codes: List[str] = field(default_factory=list)

    audit_complete: bool = False
    audit_checked_events: int = 0
    audit_missing_phases: List[str] = field(default_factory=list)
    audit_missing_modules: List[str] = field(default_factory=list)

    shadow_id: Optional[str] = None
    executed_modules: List[str] = field(default_factory=list)
    documents_seen: List[str] = field(default_factory=list)
    norm_units_seen: List[str] = field(default_factory=list)
    shadow_block_codes: List[str] = field(default_factory=list)

    adapter_notes: List[str] = field(default_factory=list)


class LevelARequestMapper:
    def map_from_package(self, package: LevelBDeliveryPackage, *, trace_id: str = '') -> LevelARequestEnvelope:
        notes: List[str] = [
            'Pacchetto tecnico-documentale di supporto, non conclusivo.',
            'Il Livello A conserva interpretazione, motivazione, validazione e decisione finale.',
        ]
        if package.block_codes:
            notes.append('Sono presenti blocchi da governare nel Livello A.')
        if package.warnings:
            notes.append('Sono presenti warning tecnici da considerare nel governo metodologico.')

        return LevelARequestEnvelope(
            record_id=build_id('levelareqrec'),
            record_type='LevelARequestEnvelope',
            request_id=build_id('levelareq'),
            case_id=package.case_id,
            source_package_id=package.package_id,
            source_report_id=package.report_id,
            support_only_flag=True,
            technical_status=package.package_status,
            source_ids=list(package.source_ids),
            valid_citation_ids=list(package.valid_citation_ids),
            blocked_citation_ids=list(package.blocked_citation_ids),
            citation_status_summary=dict(package.citation_status_summary),
            vigenza_status_summary=dict(package.vigenza_status_summary),
            crossref_status_summary=dict(package.crossref_status_summary),
            coverage_ref_id=package.coverage_ref_id,
            coverage_status=package.coverage_status,
            m07_ref_id=package.m07_ref_id,
            m07_status=package.m07_status,
            warnings=list(package.warnings),
            errors=list(package.errors),
            block_ids=list(package.block_ids),
            block_codes=list(package.block_codes),
            audit_complete=package.audit_complete,
            audit_checked_events=package.audit_checked_events,
            audit_missing_phases=list(package.audit_missing_phases),
            audit_missing_modules=list(package.audit_missing_modules),
            shadow_id=package.shadow_id,
            executed_modules=list(package.executed_modules),
            documents_seen=list(package.documents_seen),
            norm_units_seen=list(package.norm_units_seen),
            shadow_block_codes=list(package.shadow_block_codes),
            adapter_notes=notes,
            trace_id=trace_id or package.trace_id,
            source_layer='A',
        )
