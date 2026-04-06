"""Helpers for safe subprocess execution on Windows-friendly Python code paths."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(slots=True)
class CommandResult:
    """Captured subprocess result data."""

    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        """Return whether the command completed successfully."""
        return not self.timed_out and self.returncode == 0

    @property
    def command_display(self) -> str:
        """Return the command in a shell-friendly display form."""
        return subprocess.list2cmdline(self.command)


def find_executable(candidates: Sequence[str | Path]) -> Path | None:
    """Return the first available executable path from a list of candidates."""
    for candidate in candidates:
        candidate_str = str(candidate)
        candidate_path = Path(candidate_str).expanduser()

        if candidate_path.is_absolute() and candidate_path.exists():
            return candidate_path.resolve()

        resolved = shutil.which(candidate_str)
        if resolved:
            return Path(resolved).resolve()

    return None


def run_command(
    command: Sequence[str | Path],
    *,
    cwd: Path | None = None,
    timeout_seconds: int | None = None,
) -> CommandResult:
    """Run a subprocess safely and capture stdout/stderr."""
    normalized_command = [str(part) for part in command]

    try:
        completed = subprocess.run(
            normalized_command,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return CommandResult(
            command=normalized_command,
            returncode=-1,
            stdout=stdout,
            stderr=stderr or f"Command timed out after {timeout_seconds} seconds.",
            timed_out=True,
        )

    return CommandResult(
        command=normalized_command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
