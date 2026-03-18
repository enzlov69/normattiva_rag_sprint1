from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from validators.level_b_baseline_index_rules import (  # noqa: E402
    build_report,
    compute_decision,
    evaluate_checkpoints,
    get_git_status_clean,
    load_json,
    validate_registry_shape,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Level B Baseline Index Master v1")
    parser.add_argument(
        "--output",
        default=str(BASE_DIR / "artifacts" / "level_b_baseline_index_master_report_v1.json"),
        help="Path for the generated report JSON",
    )
    args = parser.parse_args()

    registry_path = BASE_DIR / "schemas" / "level_b_baseline_index_master_registry_v1.json"
    registry = load_json(registry_path)
    registry_problems = validate_registry_shape(registry)
    checkpoint_results = evaluate_checkpoints(BASE_DIR, registry)
    git_status_clean = get_git_status_clean(BASE_DIR)
    decision, reasons = compute_decision(
        registry_problems=registry_problems,
        checkpoint_results=checkpoint_results,
        git_status_clean=git_status_clean,
    )
    report = build_report(
        registry=registry,
        registry_problems=registry_problems,
        checkpoint_results=checkpoint_results,
        decision=decision,
        reasons=reasons,
        base_dir=BASE_DIR,
        git_status_clean=git_status_clean,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Baseline index decision: {decision}")
    print(f"Report written to: {output_path}")
    if reasons:
        print("Reasons:")
        for reason in reasons:
            print(f"- {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
