from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def run_step(script_name: str, *extra_args: str) -> None:
    script = BASE_DIR / script_name
    cmd = [sys.executable, str(script), *extra_args]
    print(f"\n=== RUN {script_name} ===")
    completed = subprocess.run(cmd, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    print(
        "[INFO] Pipeline scope: manifest check -> ingest -> baseline retrieval. "
        "Final stronger validation remains a separate manual step: "
        "tools/dlgs33_ingest/test_retrieval_dlgs33_vigente_top13.py"
    )
    run_step("check_manifest_dlgs33_vigente.py")
    run_step("ingest_dlgs33_vigente.py", "--reset")
    run_step("test_retrieval_dlgs33_vigente.py")
