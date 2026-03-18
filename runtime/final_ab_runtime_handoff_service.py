from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Dict, Mapping, Optional

from runtime.final_ab_response_envelope_gate import FinalABResponseEnvelopeGate


class FinalABRuntimeHandoffService:
    """
    Controlled runtime handoff service for the final A→B→A path.

    Canonical pipeline:
    frontdoor runtime
        -> handoff service
        -> runner invoker
        -> raw validation gate
        -> response mapper
        -> response-envelope gate
        -> final ABResponseEnvelope

    Notes:
    - the federated runner remains black-box and untouched;
    - the raw validator remains the authoritative pre-mapper guard;
    - this service adds only the post-mapper final response-envelope guard.
    """

    def __init__(
        self,
        *,
        runner_invoker: Any,
        raw_validator: Any,
        response_mapper: Any,
        response_envelope_gate: Optional[FinalABResponseEnvelopeGate] = None,
    ) -> None:
        self.runner_invoker = runner_invoker
        self.raw_validator = raw_validator
        self.response_mapper = response_mapper
        self.response_envelope_gate = response_envelope_gate or FinalABResponseEnvelopeGate()

    def handoff(self, request_envelope: Mapping[str, Any]) -> Dict[str, Any]:
        request_payload = self._safe_copy_mapping(request_envelope)

        raw_response = self._invoke_runner(request_payload)
        raw_validation_result = self._validate_raw_response(raw_response)
        mapped_response = self._map_response(
            raw_response=raw_response,
            raw_validation_result=raw_validation_result,
            request_envelope=request_payload,
        )
        final_envelope = self._apply_response_envelope_gate(
            mapped_response=mapped_response,
            raw_validation_result=raw_validation_result,
            raw_response=raw_response,
        )
        return final_envelope

    def execute(self, request_envelope: Mapping[str, Any]) -> Dict[str, Any]:
        return self.handoff(request_envelope)

    def run(self, request_envelope: Mapping[str, Any]) -> Dict[str, Any]:
        return self.handoff(request_envelope)

    def _invoke_runner(self, request_envelope: Mapping[str, Any]) -> Dict[str, Any]:
        candidate_methods = (
            (self.runner_invoker, "invoke"),
            (self.runner_invoker, "run"),
            (self.runner_invoker, "execute"),
        )
        for target, method_name in candidate_methods:
            method = getattr(target, method_name, None)
            if callable(method):
                return self._safe_copy_mapping(method(request_envelope))
        if callable(self.runner_invoker):
            return self._safe_copy_mapping(self.runner_invoker(request_envelope))
        raise TypeError("runner_invoker must expose invoke/run/execute or be callable")

    def _validate_raw_response(self, raw_response: Mapping[str, Any]) -> Dict[str, Any]:
        candidate_methods = (
            (self.raw_validator, "validate"),
            (self.raw_validator, "validate_response"),
            (self.raw_validator, "run"),
            (self.raw_validator, "execute"),
        )
        for target, method_name in candidate_methods:
            method = getattr(target, method_name, None)
            if callable(method):
                return self._safe_copy_mapping(method(raw_response))
        if callable(self.raw_validator):
            return self._safe_copy_mapping(self.raw_validator(raw_response))
        raise TypeError("raw_validator must expose validate/validate_response/run/execute or be callable")

    def _map_response(
        self,
        *,
        raw_response: Mapping[str, Any],
        raw_validation_result: Mapping[str, Any],
        request_envelope: Mapping[str, Any],
    ) -> Dict[str, Any]:
        mapper_callables = (
            self._build_mapper_callable("map_response", raw_response, raw_validation_result, request_envelope),
            self._build_mapper_callable("map", raw_response, raw_validation_result, request_envelope),
            self._build_mapper_callable("execute", raw_response, raw_validation_result, request_envelope),
            self._build_mapper_callable("run", raw_response, raw_validation_result, request_envelope),
        )
        for invocation in mapper_callables:
            if invocation is None:
                continue
            try:
                return self._safe_copy_mapping(invocation())
            except TypeError:
                continue

        if callable(self.response_mapper):
            for args, kwargs in (
                ((raw_response,), {"raw_validation_result": raw_validation_result, "request_envelope": request_envelope}),
                ((raw_response, raw_validation_result), {"request_envelope": request_envelope}),
                ((raw_response, raw_validation_result), {}),
                ((raw_response,), {}),
            ):
                try:
                    return self._safe_copy_mapping(self.response_mapper(*args, **kwargs))
                except TypeError:
                    continue

        raise TypeError(
            "response_mapper must expose map_response/map/execute/run or be callable with the raw response"
        )

    def _build_mapper_callable(
        self,
        method_name: str,
        raw_response: Mapping[str, Any],
        raw_validation_result: Mapping[str, Any],
        request_envelope: Mapping[str, Any],
    ) -> Optional[Callable[[], Any]]:
        method = getattr(self.response_mapper, method_name, None)
        if not callable(method):
            return None

        def invoke() -> Any:
            call_patterns = (
                ((raw_response,), {"raw_validation_result": raw_validation_result, "request_envelope": request_envelope}),
                ((raw_response,), {"validation_result": raw_validation_result, "request_envelope": request_envelope}),
                ((raw_response, raw_validation_result), {"request_envelope": request_envelope}),
                ((raw_response, raw_validation_result), {}),
                ((raw_response,), {}),
            )
            last_error: Optional[TypeError] = None
            for args, kwargs in call_patterns:
                try:
                    return method(*args, **kwargs)
                except TypeError as exc:
                    last_error = exc
                    continue
            if last_error is not None:
                raise last_error
            raise TypeError(f"Unsupported mapper signature for {method_name}")

        return invoke

    def _apply_response_envelope_gate(
        self,
        *,
        mapped_response: Mapping[str, Any],
        raw_validation_result: Mapping[str, Any],
        raw_response: Mapping[str, Any],
    ) -> Dict[str, Any]:
        gate = self.response_envelope_gate
        if hasattr(gate, "validate") and callable(gate.validate):
            return self._safe_copy_mapping(
                gate.validate(
                    mapped_response,
                    raw_validation_result=raw_validation_result,
                    raw_response=raw_response,
                )
            )
        if callable(gate):
            return self._safe_copy_mapping(
                gate(
                    mapped_response,
                    raw_validation_result=raw_validation_result,
                    raw_response=raw_response,
                )
            )
        raise TypeError("response_envelope_gate must expose validate(...) or be callable")

    def _safe_copy_mapping(self, value: Any) -> Dict[str, Any]:
        if not isinstance(value, Mapping):
            raise TypeError(f"Expected mapping/dict payload, got {type(value)!r}")
        return deepcopy(dict(value))
