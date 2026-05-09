"""Lightweight request validation helpers for the REST API."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TaskCreate:
    description: str


@dataclass
class RoundCreate:
    user_comment: str = ""
