from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, UTC
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from validators.level_b_release_gate_rules import (
    build_suite_result,
    compute_release_decision,
    load_json,
    resolve_suite_path,
    suite_exists,
    summarize_suite_results,
    trim_output,
    validate_manifest_shape,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Level B Offline Release Gate v1 without touching runtime or the federated runner."
    )
    parser.add_argument("--base-dir", default=".", help="Repository root where the suites live.")
    parser.add_argument(
        "--manifest",
        default="schemas/level_b_release_gate_manifest_v1.json",
        help="Relative path to the release gate manifest.",
    )
    parser.add_argument(
        "--report-path",
        default=None,
        help="Optional explicit path for the output report JSON.",
    )
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python executable used to invoke pytest.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_dir = Path(args.base_dir).resolve()
    manifest_path = (base_dir / args.manifest).resolve()

    if not manifest_path.exists():
        print(f"[ERROR] Manifest not found: {manifest_path}", file=sys.stderr)
        return 3

    manifest = load_json(manifest_path)
    manifest_problems = validate_manifest_shape(manifest)
    report_schema_path = (base_dir / manifest["report_defaults"]["report_schema_path"]).resolve()

    suite_results = []
    for suite in manifest["required_suites"]:
        suite_path = resolve_suite_path(base_dir, suite["path"])
        if not suite_exists(base_dir, suite["path"]):
            suite_results.append(
                build_suite_result(
                    suite=suite,
                    outcome="MISSING",
                    return_code=4,
                    duration_seconds=0.0,
                    stderr_excerpt=f"Missing suite file: {suite_path}",
                )
            )
            continue

        start = time.perf_counter()
        completed = subprocess.run(
            [args.python_executable, "-m", "pytest", "-q", str(suite_path)],
            cwd=str(base_dir),
            text=True,
            capture_output=True,
        )
        duration = time.perf_counter() - start

        if completed.returncode == 0:
            outcome = "PASSED"
        elif completed.returncode == 5:
            outcome = "SKIPPED"
        else:
            outcome = "FAILED"

        suite_results.append(
            build_suite_result(
                suite=suite,
                outcome=outcome,
                return_code=completed.returncode,
                duration_seconds=duration,
                stdout_excerpt=trim_output(completed.stdout),
                stderr_excerpt=trim_output(completed.stderr),
            )
        )

    release_decision, suspension_reasons = compute_release_decision(
        manifest=manifest,
        results=suite_results,
        manifest_problems=manifest_problems,
        report_schema_exists=report_schema_path.exists(),
    )

    report = {
        "manifest_id": manifest["manifest_id"],
        "manifest_version": manifest["manifest_version"],
        "gate_scope": manifest["gate_scope"],
        "execution_timestamp_utc": datetime.now(UTC).isoformat(),
        "base_dir": str(base_dir),
        "python_executable": args.python_executable,
        "release_decision": release_decision,
        "summary": summarize_suite_results(suite_results),
        "suite_results": suite_results,
        "suspension_reasons": suspension_reasons,
    }

    report_path = Path(args.report_path).resolve() if args.report_path else (base_dir / manifest["report_defaults"]["report_path"]).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    
    print(f"Release decision: {release_decision}")
    print(f"Report written to: {report_path}")
    if suspension_reasons:
        print("Reasons:")
        for reason in suspension_reasons:
            print(f"- {reason}")

    return 0 if release_decision == "GO" else 2 if release_decision == "SUSPEND" else 3


if __name__ == "__main__":
    raise SystemExit(main())
