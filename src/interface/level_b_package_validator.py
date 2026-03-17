from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, Union

from src.interface.level_b_package_types import LevelBDeliveryPackage, LevelBPackageValidationResult


class LevelBPackageValidator:
    REQUIRED_FIELDS = (
        'package_id',
        'case_id',
        'report_id',
        'support_only_flag',
        'source_ids',
        'warnings',
        'errors',
        'block_ids',
        'block_codes',
        'package_status',
    )

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

    def validate(self, payload: Union[LevelBDeliveryPackage, Dict[str, Any]]) -> LevelBPackageValidationResult:
        normalized = self._normalize(payload)
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in normalized or normalized.get(field) in (None, '')]
        forbidden_fields = sorted(self.FORBIDDEN_FIELDS.intersection(normalized.keys()))
        errors = []

        if normalized.get('support_only_flag') is not True:
            errors.append('Il pacchetto Livello B deve restare di solo supporto tecnico-documentale.')

        if normalized.get('package_status') == 'GO':
            errors.append('Il pacchetto Livello B non può avere stato GO finale.')

        if forbidden_fields:
            errors.append('Sono presenti campi conclusivi vietati nel pacchetto Livello B.')

        valid = not missing_fields and not forbidden_fields and not errors
        return LevelBPackageValidationResult(
            valid=valid,
            missing_fields=missing_fields,
            forbidden_fields=forbidden_fields,
            errors=errors,
            normalized_payload=normalized,
        )

    def _normalize(self, payload: Union[LevelBDeliveryPackage, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return dict(payload)
        if is_dataclass(payload):
            return asdict(payload)
        raise TypeError('payload must be a dict or dataclass instance')
