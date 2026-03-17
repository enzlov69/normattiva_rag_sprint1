from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Union

from src.adapters.level_a_request_mapper import LevelARequestEnvelope


class LevelAResponseGuard:
    FORBIDDEN_FIELDS = {
        'final_decision',
        'final_applicability',
        'legal_conclusion',
        'motivazione_finale',
        'output_authorized',
        'go_finale',
        'no_go_finale',
        'm07_closed',
        'ppav_closed',
        'rac_finalizzato',
        'authorization_status',
        'final_gate_status',
    }

    def validate(self, payload: Union[LevelARequestEnvelope, Dict[str, Any]]) -> Dict[str, Any]:
        normalized = self._normalize(payload)
        forbidden_present = sorted(self.FORBIDDEN_FIELDS.intersection(normalized.keys()))
        errors: List[str] = []

        if normalized.get('support_only_flag') is not True:
            errors.append('Il pacchetto inoltrato al Livello A deve restare tecnico-documentale.')

        if normalized.get('technical_status') == 'GO':
            errors.append('Il bridge tecnico non può esprimere GO finale.')

        if forbidden_present:
            errors.append('Sono presenti campi conclusivi vietati nel bridge verso il Livello A.')

        return {
            'valid': not errors and not forbidden_present,
            'forbidden_fields': forbidden_present,
            'errors': errors,
            'normalized_payload': normalized,
        }

    def _normalize(self, payload: Union[LevelARequestEnvelope, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return dict(payload)
        if is_dataclass(payload):
            return asdict(payload)
        raise TypeError('payload must be a dict or dataclass instance')
