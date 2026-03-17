from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.retrieval.reranker_dlgs33_patch import RetrievalCandidate, RerankerDLGS33Patch


def _norm_collection_name(value: str) -> str:
    return str(value or "").strip().lower()


def is_dlgs33_collection(source_collection: str) -> bool:
    coll = _norm_collection_name(source_collection)
    return "dlgs33" in coll or "33_2013" in coll or "33/2013" in coll


def expand_retrieval_query_for_runtime(query_text: str, source_collection: str) -> str:
    """
    Espansione minima runtime solo per il corpus D.Lgs. 33/2013.
    Serve ad aumentare la recall dei candidati prima del reranking.
    """
    if not is_dlgs33_collection(source_collection):
        return query_text

    q = str(query_text or "").strip().lower()

    expansions = {
        "amministrazione trasparente": "amministrazione trasparente sezione amministrazione trasparente",
        "responsabile per la trasparenza": "responsabile per la trasparenza",
    }

    return expansions.get(q, query_text)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _row_to_candidate(row: dict, source_collection: str) -> RetrievalCandidate:
    metadata = row.get("metadata", {}) or {}

    text_value = (
        row.get("text")
        or row.get("testo_unita")
        or row.get("document_full")
        or row.get("document")
        or ""
    )

    return RetrievalCandidate(
        retrieval_result_id=str(row.get("id", "")),
        atto_tipo=str(row.get("atto_tipo", metadata.get("atto_tipo", "Decreto legislativo"))),
        atto_numero=str(row.get("atto_numero", metadata.get("atto_numero", ""))),
        atto_anno=str(row.get("atto_anno", metadata.get("atto_anno", ""))),
        articolo=str(row.get("articolo", metadata.get("articolo", ""))),
        comma=str(row.get("comma", metadata.get("comma", ""))),
        rubrica=str(row.get("rubrica", metadata.get("rubrica", ""))),
        testo_unita=str(text_value),
        source_collection=str(row.get("source_collection", source_collection)),
        score_lexical=_safe_float(row.get("score_lexical", 0.0)),
        score_vector=_safe_float(row.get("score_vector", 0.0)),
        metadata=metadata,
    )


def _candidate_to_row(candidate: RetrievalCandidate, original_row: dict, rank: int) -> dict:
    row = deepcopy(original_row)
    row["rank"] = rank
    row["score_reranked"] = candidate.score_reranked
    row["retrieval_reason"] = list(candidate.retrieval_reason or [])
    return row


def apply_dlgs33_runtime_rerank(
    query_text: str,
    raw_results: list[dict],
    source_collection: str,
    top_k: int = 5,
) -> tuple[list[dict], dict]:
    """
    Bridge runtime per applicare la patch di reranking D.Lgs. 33/2013
    nel flusso reale del retriever/router.

    Regola:
    - se la collection NON è D.Lgs. 33/2013 -> passthrough puro, ordine invariato;
    - se la collection È D.Lgs. 33/2013 -> applica reranker corpus-scoped.
    """
    patch_applicable = is_dlgs33_collection(source_collection)
    retrieval_query = expand_retrieval_query_for_runtime(query_text, source_collection)

    shadow = {
        "query_text": query_text,
        "retrieval_query": retrieval_query,
        "source_collection": source_collection,
        "input_count": len(raw_results),
        "top_k": top_k,
        "patch_applicable": patch_applicable,
        "patch_name": "dlgs33_runtime_rerank_v2",
    }

    if not raw_results:
        shadow["output_count"] = 0
        return [], shadow

    # PASSTHROUGH PURO sui corpus non D.Lgs. 33/2013
    if not patch_applicable:
        passthrough_rows: list[dict] = []
        for idx, row in enumerate(raw_results[:top_k], start=1):
            cloned = deepcopy(row)
            cloned["rank"] = idx
            cloned["score_reranked"] = (
                _safe_float(cloned.get("score_lexical", 0.0))
                + _safe_float(cloned.get("score_vector", 0.0))
            )
            cloned["retrieval_reason"] = ["passthrough_non_dlgs33"]
            passthrough_rows.append(cloned)

        shadow["output_count"] = len(passthrough_rows)
        shadow["mode"] = "passthrough"
        return passthrough_rows, shadow

    patcher = RerankerDLGS33Patch()

    candidates = [_row_to_candidate(row, source_collection) for row in raw_results]
    reranked_candidates = patcher.rerank(query_text, candidates)

    original_by_id = {str(row.get("id", "")): row for row in raw_results}
    reranked_rows: list[dict] = []

    for idx, candidate in enumerate(reranked_candidates[:top_k], start=1):
        original_row = original_by_id.get(candidate.retrieval_result_id, {})
        reranked_rows.append(_candidate_to_row(candidate, original_row, idx))

    shadow["output_count"] = len(reranked_rows)
    shadow["mode"] = "reranked"
    return reranked_rows, shadow