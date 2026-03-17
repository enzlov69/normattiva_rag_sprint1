#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import chromadb
from sentence_transformers import SentenceTransformer

ROUTER_FILE = Path("tests/run_router_federato_generale_base_v25_6_4.py")
CHROMA_PATH = "data/chroma"
OUTPUT_FILE = Path("data/test_results/riaccertamento_straordinario_micro_results.json")
PER_COLLECTION_K = 8

DLGS126_ARTICLES = "normattiva_dlgs126_2014_articles"
DLGS126_MAIN = "normattiva_dlgs126_2014_main"
DLGS118_ALL_4_2 = "normattiva_dlgs118_2011_all_4_2"
ANNEX_118_COLLECTIONS = {
    "normattiva_dlgs118_2011_all_1",
    "normattiva_dlgs118_2011_all_4_1",
    "normattiva_dlgs118_2011_all_4_2",
}

TEST_CASES: List[Dict[str, str]] = [
    {
        "test_id": "rrs_micro_001",
        "area": "riaccertamento_straordinario_micro",
        "query": "riaccertamento straordinario",
        "expected_subintent": "riaccertamento_straordinario_micro",
    },
    {
        "test_id": "rrs_micro_002",
        "area": "riaccertamento_straordinario_micro",
        "query": "riaccertamento straordinario dei residui",
        "expected_subintent": "riaccertamento_straordinario_micro",
    },
    {
        "test_id": "rrs_micro_003",
        "area": "riaccertamento_straordinario_micro",
        "query": "prima applicazione armonizzazione contabile",
        "expected_subintent": "riaccertamento_straordinario_micro",
    },
    {
        "test_id": "rrs_micro_004",
        "area": "riaccertamento_straordinario_micro",
        "query": "prima applicazione residui attivi passivi",
        "expected_subintent": "riaccertamento_straordinario_micro",
    },
    {
        "test_id": "rrs_micro_005",
        "area": "riaccertamento_straordinario_micro",
        "query": "correttivo 126/2014",
        "expected_subintent": "riaccertamento_straordinario_micro",
    },
    {
        "test_id": "rrs_micro_006",
        "area": "riaccertamento_straordinario_micro",
        "query": "decreto correttivo 126/2014",
        "expected_subintent": "riaccertamento_straordinario_micro",
    },
    {
        "test_id": "rrs_micro_007",
        "area": "riaccertamento_straordinario_micro",
        "query": "riaccertamento straordinario prima applicazione",
        "expected_subintent": "riaccertamento_straordinario_micro",
    },
    {
        "test_id": "rrs_micro_008",
        "area": "riaccertamento_straordinario_micro",
        "query": "armonizzazione contabile riaccertamento straordinario",
        "expected_subintent": "riaccertamento_straordinario_micro",
    },
    {
        "test_id": "regression_001",
        "area": "fpv_operativo",
        "query": "fondo pluriennale vincolato cronoprogramma",
        "expected_subintent": "fpv_operativo",
    },
    {
        "test_id": "regression_002",
        "area": "entrate_vincolate_cassa",
        "query": "cassa vincolata entrate vincolate",
        "expected_subintent": "entrate_vincolate_cassa",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist-dir", default=CHROMA_PATH, help="Path Chroma persist directory")
    parser.add_argument("--per-collection-k", type=int, default=PER_COLLECTION_K)
    return parser.parse_args()


def load_router_module():
    if not ROUTER_FILE.exists():
        raise FileNotFoundError(f"Router file non trovato: {ROUTER_FILE}")

    spec = importlib.util.spec_from_file_location("router_v25_6_4", ROUTER_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Impossibile caricare il router da: {ROUTER_FILE}")

    module = importlib.util.module_from_spec(spec)

    # Python 3.13: il modulo va registrato prima di exec_module,
    # altrimenti @dataclass può fallire su cls.__module__
    sys.modules[spec.name] = module

    spec.loader.exec_module(module)
    return module


def top_keys(ranked: List[Any], top_n: int) -> List[str]:
    return [c.key for c in ranked[:top_n]]


def top_rows(ranked: List[Any], top_n: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for c in ranked[:top_n]:
        rows.append(
            {
                "key": c.key,
                "collection": c.collection,
                "doc_id": c.doc_id,
                "score_final": c.score_final,
                "sim_score": c.sim_score,
                "collection_prior": c.collection_prior,
                "query_bonus": c.query_bonus,
                "penalty_score": c.penalty_score,
                "specificity_tiebreak_score": c.specificity_tiebreak_score,
                "anchor_hits": c.anchor_hits,
                "snippet": (c.text or "").replace("\n", " ").strip()[:180],
            }
        )
    return rows


def evaluate_rrs_micro(result: Dict[str, Any], expected_subintent: str) -> Dict[str, Any]:
    ranked = result["ranked"]
    actual_subintent = result["subintent"]

    if actual_subintent != expected_subintent:
        return {
            "status": "KO",
            "note": f"Subintent errato: atteso {expected_subintent}, ottenuto {actual_subintent}.",
            "articles_top3": False,
            "main_top5": False,
            "annex_top1": None,
            "top3_keys": top_keys(ranked, 3),
            "top5_keys": top_keys(ranked, 5),
        }

    keys_top3 = top_keys(ranked, 3)
    keys_top5 = top_keys(ranked, 5)

    articles_top3 = any(DLGS126_ARTICLES in k for k in keys_top3)
    main_top5 = any(DLGS126_MAIN in k for k in keys_top5)
    annex_top1 = bool(ranked) and ranked[0].collection in ANNEX_118_COLLECTIONS

    if articles_top3 and main_top5 and not annex_top1:
        status = "OK"
        note = "126_articles entra nei top3, 126_main entra nei top5 e nessun allegato 118 domina il top1."
    elif articles_top3 and main_top5 and annex_top1:
        status = "WARNING"
        note = "126_articles e 126_main sono emersi, ma un allegato 118 domina ancora il top1."
    elif articles_top3 or main_top5:
        status = "WARNING"
        note = "Solo una parte dell'obiettivo è stata raggiunta."
    else:
        status = "KO"
        note = "Il 126/2014 non entra con sufficiente stabilità nelle prime posizioni."

    return {
        "status": status,
        "note": note,
        "articles_top3": articles_top3,
        "main_top5": main_top5,
        "annex_top1": annex_top1,
        "top3_keys": keys_top3,
        "top5_keys": keys_top5,
    }


def evaluate_fpv_regression(result: Dict[str, Any], expected_subintent: str) -> Dict[str, Any]:
    ranked = result["ranked"]
    actual_subintent = result["subintent"]
    top1_ok = bool(ranked) and "par_0060_5_3_1" in ranked[0].key

    status = "OK" if (actual_subintent == expected_subintent and top1_ok) else "KO"
    note = (
        "Regression FPV preservata: area 5.3.x in top1."
        if status == "OK"
        else f"Regression FPV non preservata: subintent={actual_subintent}, top1={ranked[0].key if ranked else 'NONE'}."
    )

    return {
        "status": status,
        "note": note,
        "top1_ok": top1_ok,
        "top3_keys": top_keys(ranked, 3),
    }


def evaluate_cassa_regression(result: Dict[str, Any], expected_subintent: str) -> Dict[str, Any]:
    ranked = result["ranked"]
    actual_subintent = result["subintent"]
    keys_top3 = top_keys(ranked, 3)

    all42_top3 = any(DLGS118_ALL_4_2 in k for k in keys_top3)
    anchor_top3 = any(len(c.anchor_hits) > 0 for c in ranked[:3])

    status = "OK" if (actual_subintent == expected_subintent and all42_top3 and anchor_top3) else "KO"
    note = (
        "Regression cassa vincolata preservata: all_4_2 nei top3 con anchor presenti."
        if status == "OK"
        else f"Regression cassa non preservata: subintent={actual_subintent}, all_4_2_top3={all42_top3}, anchor_top3={anchor_top3}."
    )

    return {
        "status": status,
        "note": note,
        "all42_top3": all42_top3,
        "anchor_top3": anchor_top3,
        "top3_keys": keys_top3,
    }


def main() -> int:
    args = parse_args()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print("=== TEST DEDICATO — RIACCERTAMENTO STRAORDINARIO MICRO ===")
    print("CHROMA_PATH:", args.persist_dir)
    print("ROUTER_FILE:", ROUTER_FILE)

    router = load_router_module()
    model = SentenceTransformer(router.EMBED_MODEL)
    client = chromadb.PersistentClient(path=args.persist_dir)

    summary = {"OK": 0, "WARNING": 0, "KO": 0}
    results_payload: List[Dict[str, Any]] = []

    for case in TEST_CASES:
        test_id = case["test_id"]
        area = case["area"]
        query_text = case["query"]
        expected_subintent = case["expected_subintent"]

        print("\n" + "=" * 110)
        print("TEST:", test_id)
        print("AREA:", area)
        print("QUERY:", query_text)
        print("EXPECTED_SUBINTENT:", expected_subintent)

        result = router.run_single_query(
            client=client,
            model=model,
            query_text=query_text,
            per_collection_k=args.per_collection_k,
        )

        if area == "riaccertamento_straordinario_micro":
            evaluation = evaluate_rrs_micro(result, expected_subintent)
        elif area == "fpv_operativo":
            evaluation = evaluate_fpv_regression(result, expected_subintent)
        elif area == "entrate_vincolate_cassa":
            evaluation = evaluate_cassa_regression(result, expected_subintent)
        else:
            evaluation = {
                "status": "KO",
                "note": f"Area non gestita nel test: {area}",
            }

        summary[evaluation["status"]] += 1

        print("SUBINTENT DETECTED:", result["subintent"])
        print("DOMAINS:", result["domains"])
        print("QUERY_VARIANTS:", result["query_variants"])
        print("ESITO:", evaluation["status"])
        print("NOTE:", evaluation["note"])

        top5 = top_rows(result["ranked"], 5)
        print("TOP5:")
        for idx, row in enumerate(top5, start=1):
            print(
                f"{idx}. {row['key']} | score_final={row['score_final']} | "
                f"collection_prior={row['collection_prior']} | "
                f"specificity_tiebreak={row['specificity_tiebreak_score']}"
            )

        results_payload.append(
            {
                "test_id": test_id,
                "area": area,
                "query": query_text,
                "expected_subintent": expected_subintent,
                "actual_subintent": result["subintent"],
                "domains": result["domains"],
                "query_variants": result["query_variants"],
                "evaluation": evaluation,
                "top5": top5,
            }
        )

    payload = {
        "status": "OK",
        "router_file": str(ROUTER_FILE),
        "chroma_path": args.persist_dir,
        "summary": summary,
        "tests": results_payload,
    }

    OUTPUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 110)
    print("=== SUMMARY ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("Risultati salvati in:", OUTPUT_FILE)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())