from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from validators.level_b_change_control_rules import (
    build_change_control_report,
    evaluate_change_request,
    load_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Level B offline change control precheck.")
    parser.add_argument("--request", required=True, help="Path to the change request JSON file.")
    parser.add_argument("--output", default="artifacts/level_b_change_control_report_v1.json", help="Path to the output report.")
    args = parser.parse_args()

    request_path = Path(args.request)
    if not request_path.is_absolute():
        request_path = BASE_DIR / request_path

    schema = load_json(BASE_DIR / "schemas" / "level_b_change_request_schema_v1.json")
    registry = load_json(BASE_DIR / "schemas" / "level_b_change_control_registry_v1.json")
    request = load_json(request_path)

    decision, reasons, details = evaluate_change_request(
        request=request,
        schema=schema,
        registry=registry,
        base_dir=BASE_DIR,
    )
    report = build_change_control_report(
        registry=registry,
        request=request,
        decision=decision,
        reasons=reasons,
        details=details,
    )

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Change control decision: {decision}")
    print(f"Report written to: {output_path}")
    if reasons:
        print("Reasons:")
        for item in reasons:
            print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
