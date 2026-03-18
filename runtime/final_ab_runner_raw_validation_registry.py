from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict


def _schema_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "schemas"


def _load_json(filename: str) -> Dict[str, Any]:
    path = _schema_dir() / filename
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_raw_minimum_schema() -> Dict[str, Any]:
    return _load_json("final_ab_runner_raw_minimum_schema_v1.json")


@lru_cache(maxsize=1)
def load_raw_forbidden_fields_registry() -> Dict[str, Any]:
    return _load_json("final_ab_runner_raw_forbidden_fields_v1.json")


@lru_cache(maxsize=1)
def load_raw_block_rules_registry() -> Dict[str, Any]:
    return _load_json("final_ab_runner_raw_block_rules_v1.json")


def registry_versions() -> Dict[str, str]:
    minimum = load_raw_minimum_schema()
    forbidden = load_raw_forbidden_fields_registry()
    rules = load_raw_block_rules_registry()
    return {
        "minimum_schema": minimum.get("schema_version", "unknown"),
        "forbidden_registry": forbidden.get("registry_version", "unknown"),
        "block_rules": rules.get("registry_version", "unknown"),
    }
