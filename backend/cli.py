"""AICommander v2 backend CLI."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .app_flow_bridge import gui_health_status_payload, load_post_judge_route, run_post_judge_flow
from .artifacts import load_json_if_exists
from .bridge import build_bridge_plan
from .config import load_config
from .health import print_health_json


def _cmd_run_final_audit(run_folder: Path, execution_mode: str | None) -> int:
    # Kept for backward compatibility: this is now the post-judge integration flow.
    outcome = run_post_judge_flow(run_folder=run_folder, execution_mode=execution_mode)
    final_audit = load_json_if_exists(run_folder / "final_audit.json", default={})

    print(json.dumps({"integration_outcome": outcome, "final_audit": final_audit}, ensure_ascii=False, indent=2))
    return 0


def _cmd_health_check(run_folder: Path, execution_mode: str | None) -> int:
    config = load_config(strict=False, mode_override=execution_mode)
    print_health_json(config, run_folder)
    return 0


def _cmd_bridge_status(run_folder: Path) -> int:
    print(json.dumps(build_bridge_plan(run_folder), ensure_ascii=False, indent=2))
    return 0


def _cmd_gui_health_status(run_folder: Path, execution_mode: str | None) -> int:
    payload = gui_health_status_payload(run_folder=run_folder, execution_mode=execution_mode)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _cmd_read_final_audit_route(run_folder: Path) -> int:
    print(json.dumps(load_post_judge_route(run_folder), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AICommander v2 backend orchestration CLI")
    parser.add_argument("--run-folder", default="runs/current", help="Path to current run folder")
    parser.add_argument("--execution-mode", choices=["cheap", "balanced", "premium"], help="Role/model profile mode")
    parser.add_argument("--run-final-audit", action="store_true", help="Run post-judge final audit and write final_audit.json")
    parser.add_argument(
        "--run-post-judge-transition",
        action="store_true",
        help="Canonical post-judge transition: run final_auditor and write route",
    )
    parser.add_argument("--health-check", action="store_true", help="Run provider/role/workspace health check")
    parser.add_argument("--bridge-status", action="store_true", help="Print bridge contract for legacy GUI flow integration")
    parser.add_argument("--gui-health-status", action="store_true", help="Print GUI-facing health status model payload")
    parser.add_argument("--read-final-audit-route", action="store_true", help="Read final_audit.json and map next route")
    parser.add_argument(
        "--read-post-judge-route",
        action="store_true",
        help="Canonical route reader for post-judge transition output",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.execution_mode:
        os.environ["AICOMMANDER_EXECUTION_MODE"] = args.execution_mode

    run_folder = Path(args.run_folder)

    if args.run_final_audit or args.run_post_judge_transition:
        return _cmd_run_final_audit(run_folder, args.execution_mode)
    if args.health_check:
        return _cmd_health_check(run_folder, args.execution_mode)
    if args.bridge_status:
        return _cmd_bridge_status(run_folder)
    if args.gui_health_status:
        return _cmd_gui_health_status(run_folder, args.execution_mode)
    if args.read_final_audit_route or args.read_post_judge_route:
        return _cmd_read_final_audit_route(run_folder)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
