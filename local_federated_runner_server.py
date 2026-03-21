from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Iterable, List, Tuple

from runtime.federated_global_runtime import (
    load_default_runtime_config,
    run_federated_query,
)

JsonDict = Dict[str, Any]

SERVER_MODULE = "B_REAL_FEDERATED_RUNNER"
API_VERSION = "1.0"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9000


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def normalize_request(body: JsonDict) -> JsonDict:
    request_id = body.get("request_id")
    case_id = body.get("case_id")
    trace_id = body.get("trace_id")

    if not request_id or not case_id or not trace_id:
        raise ValueError("request_id, case_id e trace_id sono obbligatori.")

    return {
        "request_id": request_id,
        "case_id": case_id,
        "trace_id": trace_id,
        "api_version": body.get("api_version", API_VERSION),
        "timestamp": body.get("timestamp", now_iso()),
        "payload": body.get("payload", {}),
        "warnings": body.get("warnings", []),
        "errors": body.get("errors", []),
        "blocks": body.get("blocks", []),
        "audit": body.get("audit", {"trail_events": []}),
        "shadow": body.get("shadow", {"fragments": []}),
    }


def extract_query_text(payload: JsonDict) -> str:
    documentary_request = payload.get("documentary_request", {})
    if isinstance(documentary_request, dict):
        for key in ("query_text", "topic", "objective"):
            value = documentary_request.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    for key in ("query_text", "document_query", "input_query", "question", "topic"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    raise ValueError("Query documentale mancante nel payload.")


def extract_collections(payload: JsonDict, defaults: JsonDict) -> List[str]:
    documentary_request = payload.get("documentary_request", {})
    raw = None
    if isinstance(documentary_request, dict) and isinstance(documentary_request.get("collections"), list):
        raw = documentary_request.get("collections")
    elif isinstance(payload.get("collections"), list):
        raw = payload.get("collections")

    if raw is None:
        return list(defaults["collections"])

    return [str(item) for item in raw if isinstance(item, str) and item.strip()]


def extract_runtime_params(payload: JsonDict, defaults: JsonDict) -> Tuple[str, List[str], int, int]:
    documentary_request = payload.get("documentary_request", {})
    query_text = extract_query_text(payload)
    collections = extract_collections(payload, defaults)

    persist_dir = payload.get("persist_dir", defaults["persist_dir"])
    if isinstance(documentary_request, dict):
        persist_dir = documentary_request.get("persist_dir", persist_dir)

    top_k_per_collection = payload.get("top_k_per_collection", defaults["top_k_per_collection"])
    global_eval_top_k = payload.get("global_eval_top_k", defaults["global_eval_top_k"])
    if isinstance(documentary_request, dict):
        top_k_per_collection = documentary_request.get("top_k_per_collection", top_k_per_collection)
        global_eval_top_k = documentary_request.get("global_eval_top_k", global_eval_top_k)

    return (
        str(persist_dir),
        collections,
        int(top_k_per_collection),
        int(global_eval_top_k),
    )


def _metadata_text(metadata: JsonDict, key: str) -> str:
    value = metadata.get(key)
    return value if isinstance(value, str) else ""


def _build_source(hit: JsonDict) -> JsonDict:
    metadata = hit.get("metadata") or {}
    source_id = _metadata_text(metadata, "source_id") or _metadata_text(metadata, "source_collection") or hit.get("collection", "")
    return {
        "source_id": source_id,
        "collection": hit.get("collection"),
        "record_id": hit.get("record_id"),
        "source_collection": _metadata_text(metadata, "source_collection") or hit.get("collection"),
        "uri_ufficiale": _metadata_text(metadata, "uri_ufficiale"),
        "source_layer": _metadata_text(metadata, "source_layer"),
        "trace_id": _metadata_text(metadata, "trace_id"),
        "distance": hit.get("distance"),
    }


def _build_normative_unit(hit: JsonDict) -> JsonDict:
    metadata = hit.get("metadata") or {}
    return {
        "norm_unit_id": _metadata_text(metadata, "norm_unit_id") or hit.get("record_id"),
        "collection": hit.get("collection"),
        "record_id": hit.get("record_id"),
        "articolo": _metadata_text(metadata, "articolo") or _metadata_text(metadata, "article_label"),
        "comma": _metadata_text(metadata, "comma"),
        "numero": _metadata_text(metadata, "numero"),
        "rubrica": _metadata_text(metadata, "rubrica"),
        "unit_type": _metadata_text(metadata, "unit_type") or _metadata_text(metadata, "record_type"),
        "vigenza_ref_id": _metadata_text(metadata, "vigenza_ref_id"),
        "stato_vigenza": _metadata_text(metadata, "stato_vigenza"),
        "uri_ufficiale": _metadata_text(metadata, "uri_ufficiale"),
        "distance": hit.get("distance"),
    }


def _build_citation(hit: JsonDict) -> JsonDict:
    metadata = hit.get("metadata") or {}
    citation_text = []
    articolo = _metadata_text(metadata, "articolo") or _metadata_text(metadata, "article_label")
    comma = _metadata_text(metadata, "comma")
    if articolo:
        citation_text.append(f"art. {articolo}")
    if comma:
        citation_text.append(f"comma {comma}")

    return {
        "citation_id": f"cit_{hit.get('record_id')}",
        "record_id": hit.get("record_id"),
        "collection": hit.get("collection"),
        "citation_text": ", ".join(citation_text),
        "uri_ufficiale": _metadata_text(metadata, "uri_ufficiale"),
        "status": "STRUCTURED_MINIMAL",
    }


def _dedupe_by(items: Iterable[JsonDict], key_fields: List[str]) -> List[JsonDict]:
    seen = set()
    out: List[JsonDict] = []
    for item in items:
        key = tuple(item.get(field) for field in key_fields)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def build_documentary_packet(runtime_result: JsonDict) -> JsonDict:
    hits = runtime_result.get("results", [])
    sources = _dedupe_by((_build_source(hit) for hit in hits), ["source_id", "record_id"])
    normative_units = _dedupe_by((_build_normative_unit(hit) for hit in hits), ["norm_unit_id", "record_id"])
    citations = _dedupe_by((_build_citation(hit) for hit in hits), ["citation_id"])

    warnings: List[JsonDict] = []
    errors: List[JsonDict] = []
    blocks: List[JsonDict] = []

    fallback_collections = runtime_result.get("fallback_collections", [])
    if fallback_collections:
        warnings.append(
            {
                "code": "WORKER_FALLBACK_SYNC",
                "message": f"Fallback sincrono attivato per: {', '.join(fallback_collections)}",
                "severity": "WARNING",
            }
        )

    if runtime_result.get("runtime_failures"):
        errors.extend(
            {
                "code": "COLLECTION_RUNTIME_FAILURE",
                "message": err.get("error", "Errore runtime collection"),
                "collection": err.get("collection"),
                "attempt": err.get("attempt"),
                "severity": "ERROR",
            }
            for err in runtime_result["runtime_failures"]
        )

    if hits:
        coverage_value = "ADEQUATE" if len(hits) >= 5 else "PARTIAL"
    else:
        coverage_value = "INADEQUATE"
        warnings.append(
            {
                "code": "DOCUMENTARY_RETRIEVAL_EMPTY",
                "message": "Nessun risultato documentale recuperato dal federato globale.",
                "severity": "WARNING",
            }
        )

    packet = {
        "sources": sources,
        "normative_units": normative_units,
        "citations": citations,
        "incomplete_citations": [],
        "vigenza_status": {
            "status": "DOCUMENTARY_ONLY",
            "records_with_vigenza_ref": sum(1 for item in normative_units if item.get("vigenza_ref_id")),
            "records_with_stato_vigenza": sum(1 for item in normative_units if item.get("stato_vigenza")),
        },
        "rinvii_status": {
            "status": "NOT_ANALYZED",
            "notes": "Stato tecnico documentale: nessuna conclusione applicativa sui rinvii.",
        },
        "coverage": {
            "status": coverage_value,
            "hits_total": int(runtime_result.get("hits_total", 0)),
            "collections_queried": runtime_result.get("collections", []),
        },
        "warnings": warnings,
        "errors": errors,
        "blocks": blocks,
        "level_b_documentary_only": True,
        "opponibility_outside_level_a": "forbidden",
    }
    return packet


def build_response_envelope(request_envelope: JsonDict, runtime_result: JsonDict) -> JsonDict:
    packet = build_documentary_packet(runtime_result)
    packet_warnings = list(packet.get("warnings", []))
    packet_errors = list(packet.get("errors", []))
    packet_blocks = list(packet.get("blocks", []))

    if packet_errors:
        status = "DEGRADED"
    elif packet["coverage"]["status"] == "INADEQUATE":
        status = "SUCCESS_WITH_WARNINGS"
    elif packet_warnings:
        status = "SUCCESS_WITH_WARNINGS"
    else:
        status = "SUCCESS"

    timestamp = now_iso()
    return {
        "request_id": request_envelope["request_id"],
        "case_id": request_envelope["case_id"],
        "trace_id": request_envelope["trace_id"],
        "api_version": request_envelope.get("api_version", API_VERSION),
        "responder_module": SERVER_MODULE,
        "status": status,
        "warnings": packet_warnings,
        "errors": packet_errors,
        "blocks": packet_blocks,
        "payload": {
            "documentary_packet": packet,
            "level_b_documentary_only": True,
            "opponibility_outside_level_a": "forbidden",
        },
        "audit": {
            "trail_events": [
                {
                    "event_type": "LEVEL_B_REQUEST_RECEIVED",
                    "module": SERVER_MODULE,
                    "request_id": request_envelope["request_id"],
                    "case_id": request_envelope["case_id"],
                    "trace_id": request_envelope["trace_id"],
                    "timestamp": timestamp,
                },
                {
                    "event_type": "LEVEL_B_DOCUMENTARY_PACKET_BUILT",
                    "module": SERVER_MODULE,
                    "hits_total": runtime_result.get("hits_total", 0),
                    "timestamp": timestamp,
                },
            ],
            "level_b_documentary_only": True,
        },
        "shadow": {
            "fragments": [
                {
                    "module": SERVER_MODULE,
                    "runtime_collections": runtime_result.get("collections", []),
                    "fallback_collections": runtime_result.get("fallback_collections", []),
                    "coverage_status": packet["coverage"]["status"],
                    "timestamp": timestamp,
                }
            ],
            "level_b_documentary_only": True,
            "opponibility_outside_level_a": "forbidden",
        },
        "timestamp": timestamp,
    }


def build_runtime_error_envelope(request_envelope: JsonDict, error_message: str) -> JsonDict:
    timestamp = now_iso()
    packet = {
        "sources": [],
        "normative_units": [],
        "citations": [],
        "incomplete_citations": [],
        "vigenza_status": {
            "status": "UNAVAILABLE",
            "records_with_vigenza_ref": 0,
            "records_with_stato_vigenza": 0,
        },
        "rinvii_status": {
            "status": "UNAVAILABLE",
            "notes": "Rinvii non analizzati per errore runtime documentale.",
        },
        "coverage": {
            "status": "INADEQUATE",
            "hits_total": 0,
            "collections_queried": [],
        },
        "warnings": [
            {
                "code": "DOCUMENTARY_RUNTIME_DEGRADED",
                "message": "Pacchetto documentale restituito in modalita' degradata.",
                "severity": "WARNING",
            }
        ],
        "errors": [
            {
                "code": "DOCUMENTARY_RUNTIME_ERROR",
                "message": error_message,
                "severity": "ERROR",
            }
        ],
        "blocks": [],
        "level_b_documentary_only": True,
        "opponibility_outside_level_a": "forbidden",
    }
    return {
        "request_id": request_envelope["request_id"],
        "case_id": request_envelope["case_id"],
        "trace_id": request_envelope["trace_id"],
        "api_version": request_envelope.get("api_version", API_VERSION),
        "responder_module": SERVER_MODULE,
        "status": "DEGRADED",
        "warnings": list(packet["warnings"]),
        "errors": list(packet["errors"]),
        "blocks": [],
        "payload": {
            "documentary_packet": packet,
            "level_b_documentary_only": True,
            "opponibility_outside_level_a": "forbidden",
        },
        "audit": {
            "trail_events": [
                {
                    "event_type": "LEVEL_B_DOCUMENTARY_RUNTIME_ERROR",
                    "module": SERVER_MODULE,
                    "request_id": request_envelope["request_id"],
                    "case_id": request_envelope["case_id"],
                    "trace_id": request_envelope["trace_id"],
                    "timestamp": timestamp,
                }
            ],
            "level_b_documentary_only": True,
        },
        "shadow": {
            "fragments": [
                {
                    "module": SERVER_MODULE,
                    "runtime_error": error_message,
                    "timestamp": timestamp,
                }
            ],
            "level_b_documentary_only": True,
            "opponibility_outside_level_a": "forbidden",
        },
        "timestamp": timestamp,
    }


class LocalFederatedRunnerHandler(BaseHTTPRequestHandler):
    server_version = "LocalFederatedRunner/1.0"

    def _send_json(self, status_code: int, payload: JsonDict) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(
                200,
                {
                    "status": "UP",
                    "service": "local_federated_runner_server",
                    "responder_module": SERVER_MODULE,
                    "timestamp": now_iso(),
                    "level_b_documentary_only": True,
                },
            )
            return

        self._send_json(
            404,
            {
                "status": "NOT_FOUND",
                "error": f"Percorso non supportato: {self.path}",
                "timestamp": now_iso(),
            },
        )

    def do_POST(self) -> None:
        if self.path != "/api/v1/level-b/documentary-packet":
            self._send_json(
                404,
                {
                    "status": "NOT_FOUND",
                    "error": f"Percorso non supportato: {self.path}",
                    "timestamp": now_iso(),
                },
            )
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length).decode("utf-8")

            if not raw.strip():
                raise ValueError("Body JSON mancante.")

            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise ValueError("Il body deve essere un oggetto JSON.")

            request_envelope = normalize_request(parsed)
            defaults = load_default_runtime_config()
            persist_dir, collections, top_k_per_collection, global_eval_top_k = extract_runtime_params(
                request_envelope["payload"],
                defaults,
            )
            query_text = extract_query_text(request_envelope["payload"])

            try:
                runtime_result = run_federated_query(
                    query_text=query_text,
                    persist_dir=persist_dir,
                    collections=collections,
                    top_k_per_collection=top_k_per_collection,
                    global_eval_top_k=global_eval_top_k,
                )
                response_envelope = build_response_envelope(request_envelope, runtime_result)
            except Exception as exc:
                response_envelope = build_runtime_error_envelope(
                    request_envelope=request_envelope,
                    error_message=str(exc),
                )
            self._send_json(200, response_envelope)

        except json.JSONDecodeError:
            self._send_json(
                400,
                {
                    "status": "BAD_REQUEST",
                    "error": "JSON non valido.",
                    "timestamp": now_iso(),
                },
            )
        except ValueError as exc:
            self._send_json(
                400,
                {
                    "status": "BAD_REQUEST",
                    "error": str(exc),
                    "timestamp": now_iso(),
                },
            )
        except Exception as exc:
            self._send_json(
                500,
                {
                    "status": "INTERNAL_ERROR",
                    "error": str(exc),
                    "timestamp": now_iso(),
                },
            )

    def log_message(self, format: str, *args: Any) -> None:
        print("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))


def run() -> None:
    host = os.getenv("LEVEL_B_LOCAL_HOST", DEFAULT_HOST)
    port = int(os.getenv("LEVEL_B_LOCAL_PORT", str(DEFAULT_PORT)))
    server = ThreadingHTTPServer((host, port), LocalFederatedRunnerHandler)
    print(f"Local Federated Runner attivo su http://{host}:{port}")
    print("Health: GET /health")
    print("Level B: POST /api/v1/level-b/documentary-packet")
    server.serve_forever()


if __name__ == "__main__":
    run()
