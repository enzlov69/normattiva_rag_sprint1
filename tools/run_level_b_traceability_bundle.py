from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
BASE_DIR = CURRENT_FILE.parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from validators.level_b_traceability_bundle_rules import (  # noqa: E402
    build_bundle_report,
    check_components,
    check_required_paths,
    check_required_tags,
    compute_bundle_decision,
    get_git_status_clean,
    get_git_tags,
    load_json,
    validate_registry_shape,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Level B offline traceability bundle report.")
    parser.add_argument("--base-dir", default=str(BASE_DIR), help="Repository root to inspect.")
    parser.add_argument(
        "--registry",
        default="schemas/level_b_traceability_bundle_registry_v1.json",
        help="Registry path relative to base-dir.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/level_b_traceability_bundle_report_v1.json",
        help="Output report path relative to base-dir.",
    )
    parser.add_argument(
        "--skip-git-check",
        action="store_true",
        help="Skip live git inspection and use only tags passed through --tags.",
    )
    parser.add_argument(
        "--tags",
        default="",
        help="Comma-separated tag list used when --skip-git-check is enabled.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_dir = Path(args.base_dir).resolve()
    registry_path = (base_dir / args.registry).resolve()
    output_path = (base_dir / args.output).resolve()

    registry = load_json(registry_path)
    registry_problems = validate_registry_shape(registry)

    if args.skip_git_check:
        available_tags = [item.strip() for item in args.tags.split(",") if item.strip()]
        git_status_clean = True
    else:
        available_tags = get_git_tags(base_dir)
        git_status_clean = get_git_status_clean(base_dir)

    path_results = check_required_paths(base_dir, registry["required_paths"])
    tag_results = check_required_tags(registry["required_tags"], available_tags)
    component_results = check_components(base_dir, registry["components"], available_tags)

    decision, reasons = compute_bundle_decision(
        registry_problems=registry_problems,
        path_results=path_results,
        tag_results=tag_results,
        component_results=component_results,
        git_status_clean=git_status_clean,
    )

    report = build_bundle_report(
        registry=registry,
        registry_problems=registry_problems,
        path_results=path_results,
        tag_results=tag_results,
        component_results=component_results,
        decision=decision,
        reasons=reasons,
        base_dir=base_dir,
        available_tags=available_tags,
        git_status_clean=git_status_clean,
    )
    write_json(output_path, report)

    print(f"Traceability bundle decision: {decision}")
    print(f"Report written to: {output_path}")
    if reasons:
        print("Reasons:")
        for reason in reasons:
            print(f"- {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
