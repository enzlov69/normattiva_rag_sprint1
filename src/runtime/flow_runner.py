from __future__ import annotations

from typing import Optional

from src.adapters.level_a_adapter import LevelAAdapter
from src.compliance.final_compliance_gate import FinalComplianceGate
from src.finalization.go_final_controller import GoFinalController
from src.finalization.output_authorizer import OutputAuthorizer
from src.interface.level_b_package_types import LevelBDeliveryPackage
from src.level_a.m07_governor import M07Governor
from src.level_a.orchestrator_ppav import PPAVOrchestrator
from src.level_a.rac_builder import RACBuilder
from src.runtime.runtime_types import EndToEndFlowResult
from src.utils.ids import build_id


class EndToEndFlowRunner:
    def __init__(
        self,
        *,
        adapter: Optional[LevelAAdapter] = None,
        orchestrator: Optional[PPAVOrchestrator] = None,
        m07_governor: Optional[M07Governor] = None,
        rac_builder: Optional[RACBuilder] = None,
        compliance_gate: Optional[FinalComplianceGate] = None,
        go_controller: Optional[GoFinalController] = None,
        output_authorizer: Optional[OutputAuthorizer] = None,
    ) -> None:
        self.adapter = adapter or LevelAAdapter()
        self.orchestrator = orchestrator or PPAVOrchestrator()
        self.m07_governor = m07_governor or M07Governor()
        self.rac_builder = rac_builder or RACBuilder()
        self.compliance_gate = compliance_gate or FinalComplianceGate()
        self.go_controller = go_controller or GoFinalController()
        self.output_authorizer = output_authorizer or OutputAuthorizer()

    def run(
        self,
        package: LevelBDeliveryPackage,
        *,
        requested_output_type: str = 'RAC_DRAFT',
        trace_id: str = '',
    ) -> EndToEndFlowResult:
        envelope = self.adapter.build_request(package, trace_id=trace_id)
        workflow = self.orchestrator.start_workflow(envelope, trace_id=trace_id)
        ppav = self.orchestrator.orchestrate(envelope, trace_id=trace_id)
        m07 = self.m07_governor.govern(envelope, trace_id=trace_id)
        rac = self.rac_builder.build_draft(envelope, trace_id=trace_id)
        compliance = self.compliance_gate.evaluate(
            envelope,
            m07_record=m07,
            rac_draft=rac,
            trace_id=trace_id,
        )
        assessment = self.go_controller.assess(
            envelope,
            compliance,
            ppav_record=ppav,
            m07_record=m07,
            rac_draft=rac,
            trace_id=trace_id,
        )
        authorization = self.output_authorizer.authorize(
            assessment,
            requested_output_type=requested_output_type,
            trace_id=trace_id,
        )

        final_runtime_status = 'READY_FOR_METHOD_REVIEW'
        if authorization.authorization_allowed:
            final_runtime_status = 'AUTHORIZED_TECHNICAL_OUTPUT'
        elif compliance.technical_readiness_status == 'BLOCKED' or assessment.blocking_reasons:
            final_runtime_status = 'BLOCKED'
        elif compliance.technical_readiness_status == 'SUPPORT_ONLY':
            final_runtime_status = 'SUPPORT_ONLY'

        warnings = list(dict.fromkeys(list(envelope.warnings) + list(compliance.warnings) + list(assessment.warnings)))
        block_codes = list(dict.fromkeys(list(envelope.block_codes) + list(compliance.open_block_codes)))
        required_reviews = list(dict.fromkeys(list(assessment.required_reviews)))
        notes = [
            'Wiring end-to-end tecnico tra Livello B e Livello A.',
            'Il flusso resta subordinato al Metodo Cerda e non delega alcuna decisione al RAG.',
            "L'eventuale autorizzazione riguarda solo output tecnici del Livello A.",
        ]
        if block_codes:
            notes.append('Sono presenti blocchi tecnici da gestire prima di qualunque uso opponibile.')
        if required_reviews:
            notes.append('Persistono revisioni metodologiche e umane richieste.')

        return EndToEndFlowResult(
            record_id=build_id('e2eflowrec'),
            record_type='EndToEndFlowResult',
            flow_id=build_id('e2eflow'),
            case_id=package.case_id,
            package_id=package.package_id,
            request_id=envelope.request_id,
            support_only_flag=True,
            workflow_status=workflow.workflow_status,
            ppav_status=ppav.ppav_status,
            m07_status=m07.m07_governance_status,
            rac_status=rac.rac_draft_status,
            compliance_status=compliance.technical_readiness_status,
            go_final_status=assessment.go_final_status,
            authorization_status=authorization.authorization_status,
            requested_output_type=requested_output_type,
            authorized_output_ref=authorization.authorized_output_ref,
            final_runtime_status=final_runtime_status,
            warnings=warnings,
            block_codes=block_codes,
            required_reviews=required_reviews,
            notes=notes,
            source_layer='A',
            trace_id=trace_id or package.trace_id,
        )
