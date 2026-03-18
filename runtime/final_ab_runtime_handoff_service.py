from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import re
from typing import Any, Dict, Optional

from runtime.final_ab_runner_raw_validator import FinalABRunnerRawValidator

try:
    from runtime.final_ab_runner_response_mapper import FinalABRunnerResponseMapper
except Exception:  # pragma: no cover
    FinalABRunnerResponseMapper = None
    try:
        from runtime.final_ab_runner_response_mapper import (
            map_runner_response_to_documentary_packet,
        )
    except Exception:  # pragma: no cover
        map_runner_response_to_documentary_packet = None
else:
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
        return {
            "status": mapped.get("status", "SUCCESS"),
            "payload": mapped.get("documentary_packet", {}),
            "warnings": mapped.get("warnings", []),
            "errors": mapped.get("errors", []),
            "blocks": mapped.get("blocks", []),
            "responder_module": request.get("target_module") or "level_b_runtime_handoff",
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }


class FinalABRuntimeHandoffService:
    """
    Controlled A -> B -> runner -> raw validation gate -> response mapper -> A

    Requisiti di compatibilità:
    - mantiene il costruttore storico con `invocation_port`
    - accetta anche `runner_invoker` come alias tecnico
    - mantiene i metodi storici `handle()` e `handoff()`
    - non modifica la logica interna del runner
    - inserisce il raw validation gate prima del response mapper
    - propaga warning/errors/blocks al Livello A
    """

    def __init__(
        self,
        invocation_port: Any = None,
        runner_invoker: Any = None,
        response_mapper: Any = None,
        raw_validator: Optional[FinalABRunnerRawValidator] = None,
        responder_module: str = "level_b_runtime_handoff",
        expected_target_module: str = "level_b_runtime_handoff",
    ) -> None:
        resolved_invoker = invocation_port if invocation_port is not None else runner_invoker
        if resolved_invoker is None:
            raise TypeError(
                "FinalABRuntimeHandoffService requires `invocation_port` "
                "or `runner_invoker`."
            )

        self.invocation_port = resolved_invoker
        self.runner_invoker = resolved_invoker
        self.response_mapper = self._resolve_response_mapper(response_mapper)
        self.raw_validator = raw_validator or FinalABRunnerRawValidator()
        self.responder_module = responder_module
        self.expected_target_module = expected_target_module

    def execute(self, request_envelope: Dict[str, Any]) -> Dict[str, Any]:
        request_rejection = self._validate_request_envelope(request_envelope)
        if request_rejection is not None:
            return request_rejection

        try:
            raw_output = self._invoke_runner(request_envelope)
        except Exception as exc:
            return self._build_envelope(
                request_envelope=request_envelope,
                status="ERROR",
                payload={
                    "documentary_packet": None,
                    "raw_validation": None,
                },
                warnings=[],
                errors=[
                    {
                        "anomaly_code": "RUNNER_INVOCATION_ERROR",
                        "message": str(exc),
                        "path": "$",
                    }
                ],
                blocks=[],
            )

        raw_for_validation = self._normalize_raw_output_for_validation(raw_output)
        validation_result = self.raw_validator.validate(
            raw_output=raw_for_validation,
            request_context={
                "request_id": request_envelope.get("request_id"),
                "case_id": request_envelope.get("case_id"),
                "trace_id": request_envelope.get("trace_id"),
            },
        )

        status = validation_result.status
        if status in {"BLOCKED", "REJECTED", "ERROR"}:
            return self._build_envelope(
                request_envelope=request_envelope,
                status=status,
                payload={
                    "documentary_packet": None,
                    "raw_validation": validation_result.to_dict(),
                },
                warnings=validation_result.warnings,
                errors=validation_result.errors,
                blocks=validation_result.blocks,
            )

        mapped_output = self._map_validated_raw(
            validated_raw_payload=raw_output if isinstance(raw_output, dict) else {},
            request_envelope=request_envelope,
            validation_result=validation_result.to_dict(),
        )

        return self._merge_mapped_output(
            request_envelope=request_envelope,
            validation_result=validation_result.to_dict(),
            mapped_output=mapped_output,
        )

    def handle(self, request_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return self.execute(request_envelope)

    def handoff(self, request_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return self.execute(request_envelope)

    def __call__(self, request_envelope: Dict[str, Any]) -> Dict[str, Any]:
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

    def _validate_request_envelope(
        self, request_envelope: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        required_fields = ("request_id", "case_id", "trace_id", "target_module")
        missing_fields = [
            field
            for field in required_fields
            if not request_envelope.get(field)
        ]
        if missing_fields:
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
                        "message": f"Missing required request field(s): {', '.join(missing_fields)}",
                        "path": "$",
                    }
                ],
                blocks=[
                    {
                        "block_code": "AUDIT_INCOMPLETE",
                        "anomaly_code": "MISSING_REQUIRED_REQUEST_FIELD",
                        "message": f"Missing required request field(s): {', '.join(missing_fields)}",
                        "path": "$",
                    }
                ],
            )

        target_module = request_envelope.get("target_module")
        accepted_target_modules = {
            "level_b_runtime_handoff",
            "B_RUNTIME_HANDOFF",
        }
        if self.expected_target_module:
            accepted_target_modules.add(self.expected_target_module)

        if target_module not in accepted_target_modules:
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
                        "message": (
                            f"Unexpected target_module '{target_module}'. "
                            f"Expected one of: {sorted(accepted_target_modules)}."
                        ),
                        "path": "$.target_module",
                    }
                ],
                blocks=[
                    {
                        "block_code": "RAG_SCOPE_VIOLATION",
                        "anomaly_code": "TARGET_MODULE_MISMATCH",
                        "message": (
                            f"Unexpected target_module '{target_module}'. "
                            f"Expected one of: {sorted(accepted_target_modules)}."
                        ),
                        "path": "$.target_module",
                    }
                ],
            )

        return None

    def _invoke_runner(self, request_envelope: Dict[str, Any]) -> Any:
        runner_request = self._build_runner_request(request_envelope)
        if hasattr(self.runner_invoker, "invoke"):
            return self.runner_invoker.invoke(runner_request)
        if callable(self.runner_invoker):
            return self.runner_invoker(runner_request)
        raise TypeError("Runner invoker must expose 'invoke' or be callable.")

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
    def _normalize_raw_output_for_validation(raw_output: Any) -> Any:
        if not isinstance(raw_output, dict):
            return raw_output

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

    def _map_validated_raw(
        self,
        validated_raw_payload: Dict[str, Any],
        request_envelope: Dict[str, Any],
        validation_result: Dict[str, Any],
    ) -> Any:
        if hasattr(self.response_mapper, "map"):
            map_fn = self.response_mapper.map
        elif callable(self.response_mapper):
            map_fn = self.response_mapper
        else:
            raise TypeError("Response mapper must expose 'map' or be callable.")

        candidate_kwargs = (
            {
                "raw_output": validated_raw_payload,
                "request_envelope": request_envelope,
                "validation_result": validation_result,
            },
            {
                "raw_output": validated_raw_payload,
                "request_envelope": request_envelope,
            },
            {
                "raw_output": validated_raw_payload,
            },
        )

        for kwargs in candidate_kwargs:
            try:
                return map_fn(**kwargs)
            except TypeError:
                continue

        return map_fn(validated_raw_payload)

    def _merge_mapped_output(
        self,
        request_envelope: Dict[str, Any],
        validation_result: Dict[str, Any],
        mapped_output: Any,
    ) -> Dict[str, Any]:
        validation_status = validation_result["status"]

        if isinstance(mapped_output, dict) and self._looks_like_envelope(mapped_output):
            final_status = self._max_status(
                validation_status,
                mapped_output.get("status", "SUCCESS"),
            )
            return {
                "request_id": request_envelope.get("request_id"),
                "case_id": request_envelope.get("case_id"),
                "trace_id": request_envelope.get("trace_id"),
                "api_version": request_envelope.get("api_version"),
                "responder_module": mapped_output.get(
                    "responder_module", self.responder_module
                ),
                "status": final_status,
                "payload": mapped_output.get("payload"),
                "warnings": self._dedupe_events(
                    validation_result["warnings"] + mapped_output.get("warnings", [])
                ),
                "errors": self._dedupe_events(
                    validation_result["errors"] + mapped_output.get("errors", [])
                ),
                "blocks": self._dedupe_events(
                    validation_result["blocks"] + mapped_output.get("blocks", [])
                ),
                "timestamp": mapped_output.get("timestamp", self._utc_now()),
            }

        final_status = validation_status
        if final_status == "SUCCESS" and validation_result["warnings"]:
            final_status = "SUCCESS_WITH_WARNINGS"
        elif final_status == "DEGRADED":
            final_status = "DEGRADED"

        return self._build_envelope(
            request_envelope=request_envelope,
            status=final_status,
            payload={
                "documentary_packet": mapped_output,
                "raw_validation": validation_result,
            },
            warnings=validation_result["warnings"],
            errors=validation_result["errors"],
            blocks=validation_result["blocks"],
        )

    def _build_envelope(
        self,
        request_envelope: Dict[str, Any],
        status: str,
        payload: Dict[str, Any],
        warnings: list,
        errors: list,
        blocks: list,
    ) -> Dict[str, Any]:
        return {
            "request_id": request_envelope.get("request_id"),
            "case_id": request_envelope.get("case_id"),
            "trace_id": request_envelope.get("trace_id"),
            "api_version": request_envelope.get("api_version"),
            "responder_module": self.responder_module,
            "status": status,
            "payload": payload,
            "warnings": warnings,
            "errors": errors,
            "blocks": blocks,
            "timestamp": self._utc_now(),
        }

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    @staticmethod
    def _looks_like_envelope(mapped_output: Dict[str, Any]) -> bool:
        required_keys = {"status", "payload", "warnings", "errors", "blocks"}
        return required_keys.issubset(mapped_output.keys())

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
    def _dedupe_events(events: list) -> list:
        seen = set()
        output = []
        for event in events:
            key = (
                event.get("anomaly_code"),
                event.get("path"),
                event.get("block_code"),
                event.get("message"),
            )
            if key in seen:
                continue
            seen.add(key)
            output.append(event)
        return output
