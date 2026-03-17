from typing import Any, Dict

from src.adapters.level_a_request_mapper import LevelARequestEnvelope, LevelARequestMapper
from src.adapters.level_a_response_guard import LevelAResponseGuard
from src.interface.level_b_package_types import LevelBDeliveryPackage


class LevelAAdapter:
    def __init__(
        self,
        *,
        mapper: LevelARequestMapper | None = None,
        response_guard: LevelAResponseGuard | None = None,
    ) -> None:
        self.mapper = mapper or LevelARequestMapper()
        self.response_guard = response_guard or LevelAResponseGuard()

    def build_request(self, package: LevelBDeliveryPackage, *, trace_id: str = '') -> LevelARequestEnvelope:
        envelope = self.mapper.map_from_package(package, trace_id=trace_id)
        guard = self.response_guard.validate(envelope)
        if not guard['valid']:
            joined = '; '.join(guard['errors']) or 'Bridge verso il Livello A non valido'
            raise ValueError(joined)
        return envelope

    def build_request_payload(self, package: LevelBDeliveryPackage, *, trace_id: str = '') -> Dict[str, Any]:
        envelope = self.build_request(package, trace_id=trace_id)
        return envelope.to_dict()
