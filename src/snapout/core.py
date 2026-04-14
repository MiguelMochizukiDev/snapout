"""
core.py
Core SnapOut backend operations.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
from typing import Iterable


@dataclass(frozen=True)
class SnapRow:
    name: str
    version: str
    revision: str
    notes: str


def _run_capture(args: list[str]) -> str:
    completed = subprocess.run(args, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return ""
    return completed.stdout


def _run_passthrough(args: list[str]) -> int:
    completed = subprocess.run(args, check=False)
    return completed.returncode


def _parse_snap_rows(output: str) -> list[SnapRow]:
    rows: list[SnapRow] = []
    for raw_line in output.splitlines()[1:]:
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        rows.append(SnapRow(parts[0], parts[1], parts[2], parts[-1]))
    return rows


def snap_rows() -> list[SnapRow]:
    output = _run_capture(["snap", "list", "--all", "--color=never"])
    return _parse_snap_rows(output)


def active_snap_rows() -> list[SnapRow]:
    return [row for row in snap_rows() if row.notes != "disabled"]


def old_snap_rows() -> list[SnapRow]:
    return [row for row in snap_rows() if row.notes == "disabled"]


def _with_sudo_if_needed(args: Iterable[str]) -> list[str]:
    if os.geteuid() == 0:
        return list(args)
    return ["sudo", *args]


def _format_command(args: list[str]) -> str:
    return " ".join(args)


def remove_revision(name: str, revision: str, dry_run: bool = False) -> int:
    cmd = _with_sudo_if_needed(["snap", "remove", "--revision", revision, name])
    if dry_run:
        print(f"[DRY RUN] {_format_command(cmd)}")
        return 0
    return _run_passthrough(cmd)


def remove_package(name: str, dry_run: bool = False) -> int:
    cmd = _with_sudo_if_needed(["snap", "remove", name])
    if dry_run:
        print(f"[DRY RUN] {_format_command(cmd)}")
        return 0
    return _run_passthrough(cmd)
