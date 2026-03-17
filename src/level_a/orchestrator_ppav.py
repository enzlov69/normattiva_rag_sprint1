from src.adapters.level_a_request_mapper import LevelARequestEnvelope
from src.level_a.level_a_types import LevelAWorkflowState, PPAVOrchestrationRecord
from src.utils.ids import build_id


class PPAVOrchestrator:
    DEFAULT_NEXT_MODULES = ['PPAV_ORCHESTRATOR', 'M07_GOVERNOR', 'RAC_BUILDER']

    def start_workflow(self, envelope: LevelARequestEnvelope, *, trace_id: str = '') -> LevelAWorkflowState:
        notes = [
            'Flusso metodologico aperto in modalità tecnica di supporto.',
            'Il Livello A conserva interpretazione, motivazione e decisione finale.',
        ]
        if envelope.block_codes:
            notes.append('Sono presenti blocchi tecnici da governare nel Metodo Cerda.')

        return LevelAWorkflowState(
            record_id=build_id('lawflowrec'),
            record_type='LevelAWorkflowState',
            workflow_id=build_id('lawflow'),
            case_id=envelope.case_id,
            request_id=envelope.request_id,
            source_package_id=envelope.source_package_id,
            support_only_flag=True,
            workflow_status='OPEN_WITH_BLOCKS' if envelope.block_codes else 'OPEN',
            next_modules=list(self.DEFAULT_NEXT_MODULES),
            warnings=list(envelope.warnings),
            errors=list(envelope.errors),
            block_codes=list(envelope.block_codes),
            notes=notes,
            source_layer='A',
            trace_id=trace_id or envelope.trace_id,
        )

    def orchestrate(self, envelope: LevelARequestEnvelope, *, trace_id: str = '') -> PPAVOrchestrationRecord:
        requested_modules = ['M07_GOVERNOR', 'RAC_BUILDER']
        if envelope.coverage_status == 'INADEQUATE' or envelope.m07_status in {'PARTIAL', 'REQUIRED'}:
            requested_modules.insert(0, 'PPAV_REVIEW')

        notes = [
            'Orchestrazione PPAV avviata senza esito conclusivo.',
            'Il pacchetto documentale resta di supporto e non autorizza output opponibili.',
        ]
        if envelope.audit_complete is False:
            notes.append('Audit incompleto: il flusso richiede verifica metodologica rafforzata.')
        if envelope.block_codes:
            notes.append('Sono presenti blocchi tecnici da valutare nel Livello A.')

        return PPAVOrchestrationRecord(
            record_id=build_id('ppavorchrec'),
            record_type='PPAVOrchestrationRecord',
            orchestration_id=build_id('ppavorch'),
            case_id=envelope.case_id,
            request_id=envelope.request_id,
            source_package_id=envelope.source_package_id,
            support_only_flag=True,
            ppav_status='OPEN_WITH_BLOCKS' if envelope.block_codes else 'OPEN',
            requested_modules=requested_modules,
            required_human_governance=True,
            warnings=list(envelope.warnings),
            block_codes=list(envelope.block_codes),
            notes=notes,
            source_layer='A',
            trace_id=trace_id or envelope.trace_id,
        )
