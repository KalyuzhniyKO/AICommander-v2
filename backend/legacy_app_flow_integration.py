"""Backward-compatible wrappers for legacy AICommander app-flow integration.

New code should import from `backend.main_app_integration`. This module exists
only to preserve older migration-pack references while the app migrates to the
canonical entrypoints.
"""

from __future__ import annotations

from .main_app_integration import get_gui_status_model_for_app, run_after_judge_and_resolve_next_step

__all__ = ["run_after_judge_and_resolve_next_step", "get_gui_status_model_for_app"]
