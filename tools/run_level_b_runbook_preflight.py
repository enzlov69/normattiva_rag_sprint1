from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
BASE_DIR = CURRENT_FILE.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from validators.level_b_runbook_rules import (
    build_preflight_report,
    check_required_paths,
    check_required_suites,
    compute_preflight_decision,
    load_json,
    validate_runbook_checklist_shape,
    write_json,
)


def detect_git_status_clean(base_dir: Path) -> bool | None:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() == ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Runbook preflight for the offline Level B track")
    parser.add_argument("--base-dir", default=".", help="Repository base dir")
    parser.add_argument(
        "--checklist-path",
        default="schemas/level_b_runbook_checklist_v1.json",
        help="Relative path to the runbook checklist JSON",
    )
    parser.add_argument(
        "--report-path",
        default=None,
        help="Optional explicit report path. Defaults to checklist preflight.report_default_path",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    checklist_path = (base_dir / args.checklist_path).resolve()

    if not checklist_path.exists():
        print("Preflight decision: ERROR")
        print(f"Missing checklist: {checklist_path}")
        return 2

    checklist = load_json(checklist_path)
    checklist_problems = validate_runbook_checklist_shape(checklist)
    path_results = check_required_paths(base_dir, checklist.get("required_paths", []))
    suite_results = check_required_suites(base_dir, checklist.get("required_suites", []))
    git_status_clean = detect_git_status_clean(base_dir)
    decision, reasons = compute_preflight_decision(
        checklist_problems=checklist_problems,
        path_results=path_results,
        suite_results=suite_results,
        git_status_clean=git_status_clean,
    )

    report_path = args.report_path or checklist["preflight"]["report_default_path"]
    report = build_preflight_report(
        checklist=checklist,
        checklist_problems=checklist_problems,
        path_results=path_results,
        suite_results=suite_results,
        decision=decision,
        reasons=reasons,
        base_dir=base_dir,
        git_status_clean=git_status_clean,
    )
    output_path = (base_dir / report_path).resolve()
    write_json(output_path, report)

    print(f"Preflight decision: {decision}")
    print(f"Report written to: {output_path}")
    if reasons:
        print("Reasons:")
        for reason in reasons:
            print(f"- {reason}")

    if decision == "READY":
        return 0
    if decision == "HOLD":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
