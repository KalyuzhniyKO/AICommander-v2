"""AICommander v2 backend CLI."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .artifacts import collect_execution_inputs, save_json
from .bridge import build_bridge_plan
from .config import load_config
from .final_auditor import run_final_auditor
from .health import print_health_json
from .pipeline import resolve_terminal_stage


def _cmd_run_final_audit(run_folder: Path, execution_mode: str | None) -> int:
    config = load_config(strict=False, mode_override=execution_mode)
    payload = collect_execution_inputs(run_folder)

    result = run_final_auditor(config.roles["final_auditor"], payload)
    result["pipeline_terminal_stage"] = resolve_terminal_stage(result.get("final_verdict")).value
    result["execution_mode"] = config.execution_mode

    out_path = run_folder / "final_audit.json"
    save_json(out_path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _cmd_health_check(run_folder: Path, execution_mode: str | None) -> int:
    config = load_config(strict=False, mode_override=execution_mode)
    print_health_json(config, run_folder)
    return 0


def _cmd_bridge_status(run_folder: Path) -> int:
    print(json.dumps(build_bridge_plan(run_folder), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AICommander v2 backend orchestration CLI")
    parser.add_argument("--run-folder", default="runs/current", help="Path to current run folder")
    parser.add_argument("--execution-mode", choices=["cheap", "balanced", "premium"], help="Role/model profile mode")
    parser.add_argument("--run-final-audit", action="store_true", help="Run final_auditor role and write final_audit.json")
    parser.add_argument("--health-check", action="store_true", help="Run provider/role/workspace health check")
    parser.add_argument("--bridge-status", action="store_true", help="Print bridge contract for legacy GUI flow integration")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.execution_mode:
        os.environ["AICOMMANDER_EXECUTION_MODE"] = args.execution_mode

    run_folder = Path(args.run_folder)

    if args.run_final_audit:
        return _cmd_run_final_audit(run_folder, args.execution_mode)
    if args.health_check:
        return _cmd_health_check(run_folder, args.execution_mode)
    if args.bridge_status:
        return _cmd_bridge_status(run_folder)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
