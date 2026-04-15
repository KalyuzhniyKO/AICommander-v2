"""AICommander v2 backend CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .artifacts import collect_execution_inputs, save_json
from .config import load_config
from .final_auditor import run_final_auditor
from .health import print_health_json
from .pipeline import resolve_terminal_stage


def _cmd_run_final_audit(run_folder: Path) -> int:
    config = load_config()
    payload = collect_execution_inputs(run_folder)

    result = run_final_auditor(config.roles["final_auditor"], payload)
    result["pipeline_terminal_stage"] = resolve_terminal_stage(result.get("final_verdict")).value

    out_path = run_folder / "final_audit.json"
    save_json(out_path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _cmd_health_check(run_folder: Path) -> int:
    config = load_config()
    print_health_json(config, run_folder)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AICommander v2 backend orchestration CLI")
    parser.add_argument("--run-folder", default="runs/current", help="Path to current run folder")
    parser.add_argument("--run-final-audit", action="store_true", help="Run final_auditor role and write final_audit.json")
    parser.add_argument("--health-check", action="store_true", help="Run provider/role/workspace health check")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    run_folder = Path(args.run_folder)

    if args.run_final_audit:
        return _cmd_run_final_audit(run_folder)
    if args.health_check:
        return _cmd_health_check(run_folder)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
