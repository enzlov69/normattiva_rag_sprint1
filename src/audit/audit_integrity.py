from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from src.blocks import codes
from src.blocks.manager import BlockManager
from src.models.audit_event import AuditEvent


@dataclass
class AuditIntegrityResult:
    complete: bool
    missing_phases: List[str] = field(default_factory=list)
    missing_modules: List[str] = field(default_factory=list)
    checked_events: int = 0


class AuditIntegrity:
    def __init__(self, *, block_manager: Optional[BlockManager] = None) -> None:
        self.block_manager = block_manager or BlockManager()

    def check(
        self,
        *,
        case_id: str,
        events: Iterable[AuditEvent],
        required_phases: Optional[Iterable[str]] = None,
        required_modules: Optional[Iterable[str]] = None,
        trace_id: str = '',
    ) -> AuditIntegrityResult:
        events = list(events)
        phases_present = {event.event_phase for event in events if event.event_phase}
        modules_present = {event.origin_module for event in events if event.origin_module}

        required_phases = [str(x) for x in (required_phases or []) if str(x)]
        required_modules = [str(x) for x in (required_modules or []) if str(x)]

        missing_phases = [phase for phase in required_phases if phase not in phases_present]
        missing_modules = [module for module in required_modules if module not in modules_present]
        complete = not missing_phases and not missing_modules and bool(events)

        if not complete:
            reasons: List[str] = []
            if not events:
                reasons.append('audit assente')
            if missing_phases:
                reasons.append('fasi mancanti: ' + ', '.join(missing_phases))
            if missing_modules:
                reasons.append('moduli mancanti: ' + ', '.join(missing_modules))
            self.block_manager.open_block(
                case_id=case_id,
                block_code=codes.AUDIT_INCOMPLETE,
                block_category='audit',
                block_severity='CRITICAL',
                origin_module='AuditIntegrity',
                affected_object_type='AuditTrail',
                affected_object_id=case_id,
                block_reason='; '.join(reasons) or 'Audit trail incompleto',
                release_condition='Integrare eventi audit essenziali',
                trace_id=trace_id,
            )

        return AuditIntegrityResult(
            complete=complete,
            missing_phases=missing_phases,
            missing_modules=missing_modules,
            checked_events=len(events),
        )
