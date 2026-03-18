from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


def test_runner_executes_and_writes_report(tmp_path: Path) -> None:
    output_path = tmp_path / "baseline_index_report.json"
    result = subprocess.run(
        [
            sys.executable,
            str(BASE_DIR / "tools" / "run_level_b_baseline_index_master.py"),
            "--output",
            str(output_path),
        ],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert output_path.exists()
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["decision"] in {"COMPLETE", "HOLD", "ERROR"}
