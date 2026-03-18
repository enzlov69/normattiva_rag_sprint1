from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
BASE_DIR = CURRENT_FILE.parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from validators.level_b_readiness_rules import (  # noqa: E402
    build_readiness_report,
    check_checkpoint_paths,
    compute_readiness_decision,
    detect_git_tags,
    is_git_worktree_clean,
    load_json,
    validate_registry_shape,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Level B readiness dossier assessment.")
    parser.add_argument(
        "--output",
        default=str(BASE_DIR / "artifacts" / "level_b_readiness_dossier_report_v1.json"),
        help="Output path for the generated dossier report.",
    )
    args = parser.parse_args()

    registry_path = BASE_DIR / "schemas" / "level_b_readiness_dossier_registry_v1.json"
    registry = load_json(registry_path)
    registry_problems = validate_registry_shape(registry)
    checkpoint_results = check_checkpoint_paths(BASE_DIR, registry.get("checkpoints", []))
    present_tags = detect_git_tags(BASE_DIR)
    expected_tags_total = [item["expected_tag"] for item in registry.get("checkpoints", [])]
    repository_clean = is_git_worktree_clean(BASE_DIR)

    decision, reasons = compute_readiness_decision(
        registry_problems=registry_problems,
        checkpoint_results=checkpoint_results,
        repository_clean=repository_clean,
        expected_tags_present=present_tags,
        expected_tags_total=expected_tags_total,
    )

    report = build_readiness_report(
        registry=registry,
        registry_problems=registry_problems,
        checkpoint_results=checkpoint_results,
        repository_clean=repository_clean,
        expected_tags_present=present_tags,
        decision=decision,
        reasons=reasons,
        base_dir=BASE_DIR,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Readiness dossier decision: {decision}")
    print(f"Report written to: {output_path}")
    if reasons:
        print("Reasons:")
        for reason in reasons:
            print(f"- {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
