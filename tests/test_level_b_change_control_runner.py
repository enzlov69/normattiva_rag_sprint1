from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parents[1]


def test_change_control_runner_executes_and_writes_report(tmp_path: Path) -> None:
    request_path = BASE_DIR / "tests" / "fixtures" / "level_b_change_requests" / "hold" / "cc_hold_001_protected_asset_missing_approval.json"
    output_path = tmp_path / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            str(BASE_DIR / "tools" / "run_level_b_change_control_precheck.py"),
            "--request",
            str(request_path),
            "--output",
            str(output_path),
        ],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Change control decision: HOLD" in result.stdout
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["decision"] == "HOLD"
