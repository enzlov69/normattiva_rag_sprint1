from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import re
from typing import Any, Callable, Dict, Iterable, Mapping, Optional

from runtime.final_ab_response_envelope_gate import FinalABResponseEnvelopeGate
from runtime.final_ab_runner_raw_validator import FinalABRunnerRawValidator

try:
    from runtime.final_ab_runner_response_mapper import FinalABRunnerResponseMapper
except Exception:  # pragma: no cover
    FinalABRunnerResponseMapper = None

try:
    from runtime.final_ab_runner_response_mapper import map_runner_response_to_documentary_packet
except Exception:  # pragma: no cover
    map_runner_response_to_documentary_packet = None


class _IdentityResponseMapper:
    def map(
        self,
        raw_output: Dict[str, Any],
        request_envelope: Optional[Dict[str, Any]] = None,
        validation_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return raw_output


class _FunctionResponseMapperAdapter:
    """Adapter per il mapper funzionale legacy `map_runner_response_to_documentary_packet`."""

    def map(
        self,
        raw_output: Dict[str, Any],
        request_envelope: Optional[Dict[str, Any]] = None,
        validation_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if map_runner_response_to_documentary_packet is None:
            return raw_output

        request = request_envelope or {}
        mapped = map_runner_response_to_documentary_packet(
            raw_response=raw_output,
            case_id=request.get("case_id", ""),
            trace_id=request.get("trace_id", ""),
        )

        packet = deepcopy(mapped.get("documentary_packet", {}))
        if isinstance(packet, dict):
            packet.setdefault(
                "audit_fragment",
                {
                    "trace_id": request.get("trace_id"),
                    "event_type": "response_mapped",
                },
            )

        return {
            "status": mapped.get("status", "SUCCESS"),
            "payload": packet,
            "warnings": mapped.get("warnings", []),
            "errors": mapped.get("errors", []),
            "blocks": mapped.get("blocks", []),
            "responder_module": request.get("target_module") or "level_b_runtime_handoff",
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }


class FinalABRuntimeHandoffService:
    """
    Runtime handoff A->B->runner->raw validation gate->response mapper->response envelope gate->A.

    Compatibilita' legacy:
    - accetta sia `invocation_port` sia `runner_invoker`;
    - espone `handle`, `handoff`, `execute`, `run`;
    - blocca prima del mapper su status raw BLOCKED/REJECTED/ERROR.
    """

    def __init__(
        self,
        invocation_port: Any = None,
        runner_invoker: Any = None,
        response_mapper: Any = None,
        raw_validator: Optional[Any] = None,
        response_envelope_gate: Optional[Any] = None,
        responder_module: str = "level_b_runtime_handoff",
        expected_target_module: Optional[str] = None,
    ) -> None:
        resolved_invoker = invocation_port if invocation_port is not None else runner_invoker
        if resolved_invoker is None:
            raise TypeError(
                "FinalABRuntimeHandoffService requires `invocation_port` or `runner_invoker`."
            )

        self.invocation_port = resolved_invoker
        self.runner_invoker = resolved_invoker
        self.raw_validator = raw_validator or FinalABRunnerRawValidator()
        self.response_mapper = self._resolve_response_mapper(response_mapper)
        self.response_envelope_gate = response_envelope_gate or FinalABResponseEnvelopeGate()
        self.responder_module = responder_module

        accepted_targets = {
            "level_b_runtime_handoff",
            "B_RUNTIME_HANDOFF",
            "B_Runtime",
        }
        if expected_target_module:
            accepted_targets.add(expected_target_module)
        self.accepted_target_modules = accepted_targets

    def handoff(self, request_envelope: Mapping[str, Any]) -> Dict[str, Any]:
        return self.execute(request_envelope)

    def execute(self, request_envelope: Mapping[str, Any]) -> Dict[str, Any]:
        request = self._normalize_to_dict(request_envelope)

        request_rejection = self._validate_request_envelope(request)
        if request_rejection is not None:
            return request_rejection

        try:
            raw_output = self._invoke_runner(request)
        except Exception as exc:
            return self._build_envelope(
                request_envelope=request,
                status="ERROR",
                payload={
                    "documentary_packet": None,
                    "raw_validation": None,
                },
                warnings=[],
                errors=[
                    {
                        "code": "RUNNER_INVOCATION_ERROR",
                        "anomaly_code": "RUNNER_INVOCATION_ERROR",
                        "message": str(exc),
                        "path": "$",
                    }
                ],
                blocks=[],
            )

        raw_for_validation = self._normalize_raw_output_for_validation(raw_output)
        raw_validation_obj = self._invoke_raw_validator(
            raw_output_for_validation=raw_for_validation,
            raw_output_original=raw_output,
            request_envelope=request,
        )
        raw_validation = self._normalize_raw_validation_result(
            raw_validation_obj,
            fallback_payload=raw_for_validation,
        )
        raw_status = self._normalize_status(raw_validation.get("status"))

        if raw_status in {"BLOCKED", "REJECTED", "ERROR"} and self._should_stop_before_mapper(raw_validation):
            return self._build_envelope(
                request_envelope=request,
                status=raw_status,
                payload={
                    "documentary_packet": None,
                    "raw_validation": raw_validation,
                },
                warnings=raw_validation.get("warnings", []),
                errors=raw_validation.get("errors", []),
                blocks=raw_validation.get("blocks", []),
            )

        mapped_output = self._map_response(
            raw_output=raw_output,
            raw_validation_result=raw_validation,
            request_envelope=request,
        )

        if self._should_apply_response_envelope_gate(mapped_output):
            return self._apply_response_envelope_gate(
                envelope=self._prepare_gate_input_envelope(request, mapped_output),
                raw_validation_result=raw_validation,
                raw_response=raw_for_validation,
            )

        return self._merge_mapped_output(
            request_envelope=request,
            raw_validation_result=raw_validation,
            mapped_output=mapped_output,
        )

    def run(self, request_envelope: Mapping[str, Any]) -> Dict[str, Any]:
        return self.execute(request_envelope)

    def handle(self, request_envelope: Mapping[str, Any]) -> Dict[str, Any]:
        return self.execute(request_envelope)

    def _resolve_response_mapper(self, response_mapper: Any) -> Any:
        if response_mapper is not None:
            return response_mapper

        if FinalABRunnerResponseMapper is not None:
            try:
                return FinalABRunnerResponseMapper()
            except Exception:
                pass

        if map_runner_response_to_documentary_packet is not None:
            return _FunctionResponseMapperAdapter()

        return _IdentityResponseMapper()

    def _validate_request_envelope(self, request_envelope: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        required_fields = ("request_id", "case_id", "trace_id", "target_module")
        missing_fields = [field for field in required_fields if not request_envelope.get(field)]

        if missing_fields:
            message = f"Missing required request field(s): {', '.join(missing_fields)}"
            return self._build_envelope(
                request_envelope=request_envelope,
                status="REJECTED",
                payload={
                    "documentary_packet": None,
                    "raw_validation": None,
                },
                warnings=[],
                errors=[
                    {
                        "code": "INVALID_AB_REQUEST",
                        "anomaly_code": "MISSING_REQUIRED_REQUEST_FIELD",
                        "message": message,
                        "path": "$",
                    }
                ],
                blocks=[
                    {
                        "block_code": "AUDIT_INCOMPLETE",
                        "anomaly_code": "MISSING_REQUIRED_REQUEST_FIELD",
                        "message": message,
                        "path": "$",
                    }
                ],
            )

        target_module = str(request_envelope.get("target_module"))
        if target_module not in self.accepted_target_modules:
            message = (
                f"Unexpected target_module '{target_module}'. "
                f"Expected one of: {sorted(self.accepted_target_modules)}."
            )
            return self._build_envelope(
                request_envelope=request_envelope,
                status="REJECTED",
                payload={
                    "documentary_packet": None,
                    "raw_validation": None,
                },
                warnings=[],
                errors=[
                    {
                        "code": "TARGET_MODULE_MISMATCH",
                        "anomaly_code": "TARGET_MODULE_MISMATCH",
                        "message": message,
                        "path": "$.target_module",
                    }
                ],
                blocks=[
                    {
                        "block_code": "RAG_SCOPE_VIOLATION",
                        "anomaly_code": "TARGET_MODULE_MISMATCH",
                        "message": message,
                        "path": "$.target_module",
                    }
                ],
            )

        return None

    def _invoke_runner(self, request_envelope: Dict[str, Any]) -> Dict[str, Any]:
        runner_request = self._build_runner_request(request_envelope)

        methods = ("invoke", "run", "execute")
        for method_name in methods:
            method = getattr(self.runner_invoker, method_name, None)
            if callable(method):
                return self._normalize_to_dict(method(runner_request))

        if callable(self.runner_invoker):
            return self._normalize_to_dict(self.runner_invoker(runner_request))

        raise TypeError("Runner invoker must expose invoke/run/execute or be callable.")

    def _invoke_raw_validator(
        self,
        raw_output_for_validation: Dict[str, Any],
        raw_output_original: Dict[str, Any],
        request_envelope: Dict[str, Any],
    ) -> Any:
        methods = ("validate", "validate_response", "run", "execute")
        raw_candidates = (raw_output_for_validation, raw_output_original)
        for method_name in methods:
            method = getattr(self.raw_validator, method_name, None)
            if not callable(method):
                continue

            for raw_candidate in raw_candidates:
                candidate_calls = (
                    lambda: method(raw_candidate, request_context={
                        "request_id": request_envelope.get("request_id"),
                        "case_id": request_envelope.get("case_id"),
                        "trace_id": request_envelope.get("trace_id"),
                    }),
                    lambda: method(raw_candidate),
                )
                for call in candidate_calls:
                    try:
                        return call()
                    except TypeError:
                        continue
                    except Exception:
                        continue

        if callable(self.raw_validator):
            try:
                return self.raw_validator(raw_output_for_validation)
            except TypeError:
                return self.raw_validator(raw_output_for_validation, request_envelope)
            except Exception:
                try:
                    return self.raw_validator(raw_output_original)
                except TypeError:
                    return self.raw_validator(raw_output_original, request_envelope)

        raise TypeError(
            "raw_validator must expose validate/validate_response/run/execute or be callable"
        )

    def _should_apply_response_envelope_gate(self, mapped_output: Any) -> bool:
        if not isinstance(mapped_output, Mapping):
            return False
        if not self._looks_like_envelope(dict(mapped_output)):
            return False
        payload = mapped_output.get("payload")
        return isinstance(payload, Mapping) and isinstance(payload.get("documentary_packet"), Mapping)

    def _prepare_gate_input_envelope(
        self,
        request_envelope: Dict[str, Any],
        mapped_output: Mapping[str, Any],
    ) -> Dict[str, Any]:
        mapped = dict(mapped_output)
        return {
            "request_id": mapped.get("request_id", request_envelope.get("request_id")),
            "case_id": mapped.get("case_id", request_envelope.get("case_id")),
            "trace_id": mapped.get("trace_id", request_envelope.get("trace_id")),
            "api_version": mapped.get("api_version", request_envelope.get("api_version")),
            "responder_module": mapped.get("responder_module", self.responder_module),
            "status": self._normalize_status(mapped.get("status") or "SUCCESS"),
            "payload": mapped.get("payload"),
            "warnings": self._as_event_list(mapped.get("warnings")),
            "errors": self._as_event_list(mapped.get("errors")),
            "blocks": self._as_event_list(mapped.get("blocks")),
            "timestamp": mapped.get("timestamp", self._utc_now()),
        }

    def _should_stop_before_mapper(self, raw_validation_result: Dict[str, Any]) -> bool:
        return bool(raw_validation_result.get("__stop_before_mapper__", False))

    def _map_response(
        self,
        *,
        raw_output: Dict[str, Any],
        raw_validation_result: Dict[str, Any],
        request_envelope: Dict[str, Any],
    ) -> Dict[str, Any]:
        if hasattr(self.response_mapper, "map") and callable(self.response_mapper.map):
            return self._invoke_mapper_callable(
                self.response_mapper.map,
                raw_output,
                raw_validation_result,
                request_envelope,
            )

        if hasattr(self.response_mapper, "map_response") and callable(self.response_mapper.map_response):
            return self._invoke_mapper_callable(
                self.response_mapper.map_response,
                raw_output,
                raw_validation_result,
                request_envelope,
            )

        if hasattr(self.response_mapper, "execute") and callable(self.response_mapper.execute):
            return self._invoke_mapper_callable(
                self.response_mapper.execute,
                raw_output,
                raw_validation_result,
                request_envelope,
            )

        if hasattr(self.response_mapper, "run") and callable(self.response_mapper.run):
            return self._invoke_mapper_callable(
                self.response_mapper.run,
                raw_output,
                raw_validation_result,
                request_envelope,
            )

        if callable(self.response_mapper):
            return self._invoke_mapper_callable(
                self.response_mapper,
                raw_output,
                raw_validation_result,
                request_envelope,
            )

        raise TypeError(
            "Response mapper must expose map/map_response/execute/run or be callable."
        )

    def _invoke_mapper_callable(
        self,
        mapper_fn: Callable[..., Any],
        raw_output: Dict[str, Any],
        raw_validation_result: Dict[str, Any],
        request_envelope: Dict[str, Any],
    ) -> Dict[str, Any]:
        call_patterns = (
            ((), {
                "raw_output": raw_output,
                "request_envelope": request_envelope,
                "validation_result": raw_validation_result,
            }),
            ((), {
                "raw_output": raw_output,
                "request_envelope": request_envelope,
                "raw_validation_result": raw_validation_result,
            }),
            ((raw_output,), {
                "raw_validation_result": raw_validation_result,
                "request_envelope": request_envelope,
            }),
            ((raw_output, raw_validation_result), {"request_envelope": request_envelope}),
            ((raw_output,), {"request_envelope": request_envelope}),
            ((raw_output,), {}),
        )

        for args, kwargs in call_patterns:
            try:
                return self._normalize_to_dict(mapper_fn(*args, **kwargs))
            except TypeError:
                continue

        return self._normalize_to_dict(mapper_fn(raw_output))

    def _merge_mapped_output(
        self,
        *,
        request_envelope: Dict[str, Any],
        raw_validation_result: Dict[str, Any],
        mapped_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        raw_status = self._normalize_status(raw_validation_result.get("status"))

        if self._looks_like_envelope(mapped_output):
            mapped_status = self._normalize_status(mapped_output.get("status") or "SUCCESS")
            final_status = self._max_status(raw_status or "SUCCESS", mapped_status)

            warnings = self._dedupe_events(
                self._as_event_list(raw_validation_result.get("warnings"))
                + self._as_event_list(mapped_output.get("warnings"))
            )
            errors = self._dedupe_events(
                self._as_event_list(raw_validation_result.get("errors"))
                + self._as_event_list(mapped_output.get("errors"))
            )
            blocks = self._dedupe_events(
                self._as_event_list(raw_validation_result.get("blocks"))
                + self._as_event_list(mapped_output.get("blocks"))
            )

            return {
                "request_id": request_envelope.get("request_id"),
                "case_id": request_envelope.get("case_id"),
                "trace_id": request_envelope.get("trace_id"),
                "api_version": request_envelope.get("api_version"),
                "responder_module": mapped_output.get("responder_module", self.responder_module),
                "status": final_status,
                "payload": mapped_output.get("payload"),
                "warnings": warnings,
                "errors": errors,
                "blocks": blocks,
                "timestamp": mapped_output.get("timestamp", self._utc_now()),
            }

        final_status = raw_status or "SUCCESS"
        raw_warnings = self._as_event_list(raw_validation_result.get("warnings"))
        if final_status == "SUCCESS" and raw_warnings:
            final_status = "SUCCESS_WITH_WARNINGS"

        return self._build_envelope(
            request_envelope=request_envelope,
            status=final_status,
            payload={
                "documentary_packet": mapped_output,
                "raw_validation": raw_validation_result,
            },
            warnings=raw_warnings,
            errors=self._as_event_list(raw_validation_result.get("errors")),
            blocks=self._as_event_list(raw_validation_result.get("blocks")),
        )

    def _apply_response_envelope_gate(
        self,
        *,
        envelope: Dict[str, Any],
        raw_validation_result: Dict[str, Any],
        raw_response: Dict[str, Any],
    ) -> Dict[str, Any]:
        gate = self.response_envelope_gate
        if hasattr(gate, "validate") and callable(gate.validate):
            return self._normalize_to_dict(
                gate.validate(
                    envelope,
                    raw_validation_result=raw_validation_result,
                    raw_response=raw_response,
                )
            )
        if callable(gate):
            return self._normalize_to_dict(
                gate(
                    envelope,
                    raw_validation_result=raw_validation_result,
                    raw_response=raw_response,
                )
            )
        raise TypeError("response_envelope_gate must expose validate(...) or be callable")

    @staticmethod
    def _build_runner_request(request_envelope: Dict[str, Any]) -> Dict[str, Any]:
        runner_request = {
            "request_id": request_envelope.get("request_id"),
            "case_id": request_envelope.get("case_id"),
            "trace_id": request_envelope.get("trace_id"),
        }
        payload = request_envelope.get("payload")
        if isinstance(payload, dict):
            runner_request.update(payload)
        return runner_request

    @staticmethod
    def _normalize_raw_output_for_validation(raw_output: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(raw_output, dict):
            return {}

        if isinstance(raw_output.get("documentary_packet"), dict):
            normalized = deepcopy(raw_output["documentary_packet"])
        elif isinstance(raw_output.get("payload"), dict):
            normalized = deepcopy(raw_output["payload"])
        else:
            normalized = deepcopy(raw_output)

        for channel in ("warnings", "errors", "blocks"):
            if channel not in normalized and channel in raw_output:
                normalized[channel] = deepcopy(raw_output[channel])

        normalized["citations_valid"] = FinalABRuntimeHandoffService._canonicalize_citations_for_validation(
            normalized.get("citations_valid")
        )

        return normalized

    @staticmethod
    def _canonicalize_citations_for_validation(citations: Any) -> Any:
        if not isinstance(citations, list):
            return citations

        normalized_items = []
        for item in citations:
            if not isinstance(item, dict):
                normalized_items.append(item)
                continue

            if all(
                key in item
                for key in (
                    "atto_tipo",
                    "atto_numero",
                    "atto_anno",
                    "articolo",
                    "uri_ufficiale",
                    "stato_vigenza",
                )
            ):
                normalized_items.append(item)
                continue

            legacy_act = str(item.get("act") or item.get("atto") or "").strip()
            legacy_article = str(item.get("article") or item.get("articolo") or "").strip()
            legacy_uri = str(item.get("uri_ufficiale") or item.get("uri") or "").strip()
            legacy_status = str(item.get("stato_vigenza") or item.get("status") or "").strip()

            atto_tipo = legacy_act or "LEGACY_ATTO"
            atto_numero = "0"
            atto_anno = "0000"
            match = re.search(r"(.+?)\s+(\d+)\/(\d{4})$", legacy_act)
            if match:
                atto_tipo = match.group(1).strip()
                atto_numero = match.group(2)
                atto_anno = match.group(3)

            canonical = deepcopy(item)
            canonical["atto_tipo"] = str(canonical.get("atto_tipo") or atto_tipo)
            canonical["atto_numero"] = str(canonical.get("atto_numero") or atto_numero)
            canonical["atto_anno"] = str(canonical.get("atto_anno") or atto_anno)
            canonical["articolo"] = str(canonical.get("articolo") or legacy_article or "0")
            canonical["uri_ufficiale"] = str(
                canonical.get("uri_ufficiale") or legacy_uri or "urn:legacy:unknown"
            )
            canonical["stato_vigenza"] = str(
                canonical.get("stato_vigenza") or legacy_status or "UNKNOWN"
            )
            normalized_items.append(canonical)

        return normalized_items

    def _normalize_raw_validation_result(
        self,
        raw_validation_result: Any,
        *,
        fallback_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        normalized = self._normalize_to_dict(raw_validation_result)

        if not normalized and raw_validation_result is not None:
            normalized = self._object_to_dict(raw_validation_result)

        trace = normalized.get("trace")
        validator_module = ""
        if isinstance(trace, Mapping):
            validator_module = str(trace.get("validator_module") or "")

        result_type_name = type(raw_validation_result).__name__
        stop_before_mapper = any(
            (
                "validated_raw_payload" in normalized,
                "findings" in normalized,
                "registry_versions" in normalized,
                "FinalABRunnerRawValidator" in validator_module,
                result_type_name == "RawValidationResult",
            )
        )

        status = self._normalize_status(
            normalized.get("status")
            or normalized.get("validation_status")
            or normalized.get("result_status")
        )
        if not status:
            status = "SUCCESS"

        validated_payload = normalized.get("validated_raw_payload")
        if not isinstance(validated_payload, dict):
            validated_payload = fallback_payload if isinstance(fallback_payload, dict) else None

        return {
            "status": status,
            "validated_raw_payload": validated_payload,
            "warnings": self._as_event_list(normalized.get("warnings")),
            "errors": self._as_event_list(normalized.get("errors")),
            "blocks": self._as_event_list(normalized.get("blocks")),
            "findings": self._as_event_list(normalized.get("findings")),
            "registry_versions": self._normalize_to_dict(normalized.get("registry_versions")),
            "trace": self._normalize_to_dict(normalized.get("trace")),
            "__stop_before_mapper__": stop_before_mapper,
        }

    def _build_envelope(
        self,
        *,
        request_envelope: Dict[str, Any],
        status: str,
        payload: Any,
        warnings: Any,
        errors: Any,
        blocks: Any,
    ) -> Dict[str, Any]:
        return {
            "request_id": request_envelope.get("request_id"),
            "case_id": request_envelope.get("case_id"),
            "trace_id": request_envelope.get("trace_id"),
            "api_version": request_envelope.get("api_version"),
            "responder_module": self.responder_module,
            "status": self._normalize_status(status) or "SUCCESS",
            "payload": payload,
            "warnings": self._as_event_list(warnings),
            "errors": self._as_event_list(errors),
            "blocks": self._as_event_list(blocks),
            "timestamp": self._utc_now(),
        }

    @staticmethod
    def _normalize_to_dict(value: Any) -> Dict[str, Any]:
        if isinstance(value, Mapping):
            return deepcopy(dict(value))

        if value is None:
            return {}

        to_dict = getattr(value, "to_dict", None)
        if callable(to_dict):
            try:
                data = to_dict()
                if isinstance(data, Mapping):
                    return deepcopy(dict(data))
            except Exception:
                pass

        if is_dataclass(value):
            try:
                data = asdict(value)
                if isinstance(data, Mapping):
                    return deepcopy(dict(data))
            except Exception:
                pass

        return FinalABRuntimeHandoffService._object_to_dict(value)

    @staticmethod
    def _object_to_dict(value: Any) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for name in dir(value):
            if name.startswith("_"):
                continue
            try:
                attr = getattr(value, name)
            except Exception:
                continue
            if callable(attr):
                continue
            data[name] = attr
        return deepcopy(data)

    @staticmethod
    def _as_event_list(value: Any) -> list:
        if value is None:
            return []
        if isinstance(value, list):
            return deepcopy(value)
        if isinstance(value, tuple):
            return deepcopy(list(value))
        if isinstance(value, Mapping):
            return [deepcopy(dict(value))]
        return [value]

    @staticmethod
    def _dedupe_events(events: Iterable[Any]) -> list:
        seen = set()
        output = []
        for event in events:
            if isinstance(event, Mapping):
                key = (
                    str(event.get("code") or event.get("anomaly_code") or event.get("block_code") or ""),
                    str(event.get("path") or ""),
                    str(event.get("message") or event.get("reason") or ""),
                )
                normalized = dict(event)
            else:
                key = (str(event), "", "")
                normalized = {"code": str(event), "message": str(event)}
            if key in seen:
                continue
            seen.add(key)
            output.append(normalized)
        return output

    @staticmethod
    def _looks_like_envelope(mapped_output: Dict[str, Any]) -> bool:
        required = {"status", "payload", "warnings", "errors", "blocks"}
        return required.issubset(set(mapped_output.keys()))

    @staticmethod
    def _normalize_status(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip().upper()

    @staticmethod
    def _max_status(left: str, right: str) -> str:
        order = {
            "SUCCESS": 0,
            "SUCCESS_WITH_WARNINGS": 1,
            "DEGRADED": 2,
            "BLOCKED": 3,
            "REJECTED": 4,
            "ERROR": 5,
        }
        return left if order.get(left, -1) >= order.get(right, -1) else right

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
