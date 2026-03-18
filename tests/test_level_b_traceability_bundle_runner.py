from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "schemas" / "level_b_traceability_bundle_registry_v1.json"


def test_traceability_runner_executes_on_synthetic_workspace(tmp_path: Path) -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    for item in registry["required_paths"]:
        path = tmp_path / item["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")

    bundle_registry_target = tmp_path / "schemas" / "level_b_traceability_bundle_registry_v1.json"
    bundle_registry_target.parent.mkdir(parents=True, exist_ok=True)
    bundle_registry_target.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    output_path = tmp_path / "artifacts" / "report.json"
    tags = ",".join(registry["required_tags"])

    result = subprocess.run(
        [
            sys.executable,
            str(BASE_DIR / "tools" / "run_level_b_traceability_bundle.py"),
            "--base-dir",
            str(tmp_path),
            "--registry",
            "schemas/level_b_traceability_bundle_registry_v1.json",
            "--output",
            "artifacts/report.json",
            "--skip-git-check",
            "--tags",
            tags,
        ],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Traceability bundle decision: COMPLETE" in result.stdout

    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["decision"] == "COMPLETE"
