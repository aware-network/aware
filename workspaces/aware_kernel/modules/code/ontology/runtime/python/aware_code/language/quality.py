"""Generic language quality-gate execution helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import os
from pathlib import Path
import subprocess
from time import perf_counter

from aware_code.language.plugin import CodeLanguageQualityGate


@dataclass(frozen=True, slots=True)
class CodeLanguageQualityGateRunRequest:
    """Run one language-owned quality gate against resolved targets."""

    gate: CodeLanguageQualityGate
    targets: Sequence[Path] = ()
    cwd: Path | None = None
    env: Mapping[str, str] = field(default_factory=dict)
    timeout_s: float | None = None


@dataclass(frozen=True, slots=True)
class CodeLanguageQualityGateRunResult:
    """Receipt for one language quality-gate execution."""

    gate_id: str
    command: tuple[str, ...]
    target_mode: str
    target_count: int
    cwd: Path | None
    returncode: int | None
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool = False

    @property
    def status(self) -> str:
        if self.timed_out:
            return "timed_out"
        if self.returncode == 0:
            return "succeeded"
        return "failed"


def run_code_language_quality_gate(
    request: CodeLanguageQualityGateRunRequest,
) -> CodeLanguageQualityGateRunResult:
    """Execute a language-owned quality gate without shell-specific behavior."""

    command = _build_quality_gate_command(request.gate, tuple(request.targets))
    started_at = perf_counter()
    env = {**os.environ, **dict(request.env)}
    cwd = request.cwd.resolve() if request.cwd is not None else None
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd is not None else None,
            env=env,
            text=True,
            capture_output=True,
            timeout=request.timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CodeLanguageQualityGateRunResult(
            gate_id=request.gate.gate_id,
            command=tuple(command),
            target_mode=request.gate.target_mode,
            target_count=len(request.targets),
            cwd=cwd,
            returncode=None,
            stdout=_text_output(exc.stdout),
            stderr=_text_output(exc.stderr),
            duration_s=round(perf_counter() - started_at, 6),
            timed_out=True,
        )

    return CodeLanguageQualityGateRunResult(
        gate_id=request.gate.gate_id,
        command=tuple(command),
        target_mode=request.gate.target_mode,
        target_count=len(request.targets),
        cwd=cwd,
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
        duration_s=round(perf_counter() - started_at, 6),
    )


def _build_quality_gate_command(
    gate: CodeLanguageQualityGate,
    targets: tuple[Path, ...],
) -> list[str]:
    command = [str(part) for part in gate.command]
    if gate.target_mode == "paths":
        command.extend(str(path) for path in targets)
    return command


def _text_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


__all__ = [
    "CodeLanguageQualityGateRunRequest",
    "CodeLanguageQualityGateRunResult",
    "run_code_language_quality_gate",
]
