from typing import Optional

from src.adapters.level_a_request_mapper import LevelARequestEnvelope
from src.compliance.compliance_rules import ComplianceRules
from src.compliance.compliance_types import FinalComplianceSnapshot
from src.level_a.level_a_types import M07GovernanceRecord, RACDraftRecord
from src.utils.ids import build_id


class FinalComplianceGate:
    def __init__(self, *, rules: Optional[ComplianceRules] = None) -> None:
        self.rules = rules or ComplianceRules()

    def evaluate(
        self,
        envelope: LevelARequestEnvelope,
        *,
        m07_record: Optional[M07GovernanceRecord] = None,
        rac_draft: Optional[RACDraftRecord] = None,
        trace_id: str = '',
    ) -> FinalComplianceSnapshot:
        checks = self.rules.evaluate(envelope, m07_record=m07_record, rac_draft=rac_draft)
        missing = [check.reason for check in checks if not check.passed and check.reason]
        warnings = list(envelope.warnings)
        notes = [
            'Gate tecnico finale non decisorio.',
            'Il GO/NO_GO finale resta riservato al Metodo Cerda.',
            'Questo esito non autorizza output opponibili.',
        ]
        if envelope.block_codes:
            notes.append('Sono presenti blocchi tecnici aperti da governare nel Livello A.')

        status = 'READY_FOR_REVIEW'
        if envelope.errors or envelope.block_codes or any(not check.passed and check.critical for check in checks):
            status = 'BLOCKED'
        elif warnings or any(not check.passed for check in checks):
            status = 'SUPPORT_ONLY'

        return FinalComplianceSnapshot(
            record_id=build_id('compgaterec'),
            record_type='FinalComplianceSnapshot',
            compliance_id=build_id('compgate'),
            case_id=envelope.case_id,
            request_id=envelope.request_id,
            source_package_id=envelope.source_package_id,
            support_only_flag=True,
            technical_readiness_status=status,
            citation_ok=next(check.passed for check in checks if check.rule_name == 'citations'),
            vigenza_ok=next(check.passed for check in checks if check.rule_name == 'vigenza'),
            crossref_ok=next(check.passed for check in checks if check.rule_name == 'crossrefs'),
            coverage_ok=next(check.passed for check in checks if check.rule_name == 'coverage'),
            m07_ok=next(check.passed for check in checks if check.rule_name == 'm07'),
            audit_ok=next(check.passed for check in checks if check.rule_name == 'audit'),
            open_block_codes=list(envelope.block_codes),
            missing_requirements=missing,
            warnings=warnings,
            notes=notes,
            source_layer='A',
            trace_id=trace_id or envelope.trace_id,
        )
