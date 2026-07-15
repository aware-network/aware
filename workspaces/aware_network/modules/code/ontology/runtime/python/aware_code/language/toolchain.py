"""Shared language toolchain contracts.

The Code module owns this generic contract only. Language-specific packages own
their concrete providers, such as cargo for Rust.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import os
from pathlib import Path
import shutil
import subprocess
from time import perf_counter
from typing import Literal, Protocol


CodeToolchainCommandRole = Literal[
    "version",
    "build",
    "check",
    "test",
    "format",
    "lint",
    "run",
    "custom",
]
CodeToolchainStateKind = Literal[
    "home",
    "cache",
    "target",
    "config",
    "temp",
    "other",
]


class CodeToolchainUnavailable(RuntimeError):
    """Raised when a requested toolchain executable cannot be resolved."""


@dataclass(frozen=True, slots=True)
class CodeToolchainStateRoot:
    key: str
    kind: CodeToolchainStateKind
    path: Path
    env_var: str | None = None
    required: bool = True

    def env_binding(self) -> tuple[str, str] | None:
        if self.env_var is None:
            return None
        return (self.env_var, self.path.expanduser().resolve().as_posix())


@dataclass(frozen=True, slots=True)
class CodeToolchainResolution:
    provider_key: str
    toolchain_key: str
    executable_name: str
    executable_path: Path
    version: str | None = None
    state_roots: tuple[CodeToolchainStateRoot, ...] = ()
    env: Mapping[str, str] = field(default_factory=dict)
    metadata: Mapping[str, str] = field(default_factory=dict)

    @property
    def command_prefix(self) -> tuple[str, ...]:
        return (_absolute_path_without_symlink_resolution(self.executable_path).as_posix(),)

    def receipt_metadata(self) -> dict[str, object]:
        return {
            "provider_key": self.provider_key,
            "toolchain_key": self.toolchain_key,
            "executable_name": self.executable_name,
            "executable_path": _absolute_path_without_symlink_resolution(
                self.executable_path
            ).as_posix(),
            "version": self.version,
            "state_roots": [
                {
                    "key": root.key,
                    "kind": root.kind,
                    "path": root.path.expanduser().resolve().as_posix(),
                    "env_var": root.env_var,
                    "required": root.required,
                }
                for root in self.state_roots
            ],
            "env": dict(self.env),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class CodeToolchainCommandSpec:
    provider_key: str
    toolchain_key: str
    role: CodeToolchainCommandRole
    command: tuple[str, ...]
    cwd: Path | None = None
    env: Mapping[str, str] = field(default_factory=dict)
    timeout_s: float | None = None
    mutates_targets: bool = False
    network: bool = False
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CodeToolchainCommandResult:
    provider_key: str
    toolchain_key: str
    role: str
    command: tuple[str, ...]
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


@dataclass(frozen=True, slots=True)
class CodePreparedBinaryPlan:
    provider_key: str
    toolchain_key: str
    binary_name: str
    profile: str
    manifest_path: Path
    output_path: Path
    command: CodeToolchainCommandSpec
    toolchain: CodeToolchainResolution
    metadata: Mapping[str, str] = field(default_factory=dict)

    def receipt_metadata(self) -> dict[str, object]:
        return {
            "provider_key": self.provider_key,
            "toolchain_key": self.toolchain_key,
            "binary_name": self.binary_name,
            "profile": self.profile,
            "manifest_path": self.manifest_path.expanduser().resolve().as_posix(),
            "output_path": self.output_path.expanduser().resolve().as_posix(),
            "command": list(self.command.command),
            "cwd": (
                self.command.cwd.expanduser().resolve().as_posix()
                if self.command.cwd is not None
                else None
            ),
            "env": dict(self.command.env),
            "metadata": dict(self.metadata),
            "toolchain": self.toolchain.receipt_metadata(),
        }


@dataclass(frozen=True, slots=True)
class CodePreparedBinaryReceipt:
    plan: CodePreparedBinaryPlan
    result: CodeToolchainCommandResult
    artifact_path: Path

    @property
    def artifact_exists(self) -> bool:
        return self.artifact_path.expanduser().resolve().is_file()

    @property
    def status(self) -> str:
        if self.result.status != "succeeded":
            return self.result.status
        if self.artifact_exists:
            return "succeeded"
        return "missing_artifact"

    def to_mapping(self) -> dict[str, object]:
        return {
            "status": self.status,
            "artifact_exists": self.artifact_exists,
            "artifact_path": self.artifact_path.expanduser().resolve().as_posix(),
            "result": {
                "returncode": self.result.returncode,
                "stdout": self.result.stdout,
                "stderr": self.result.stderr,
                "duration_s": self.result.duration_s,
                "timed_out": self.result.timed_out,
                "status": self.result.status,
            },
            "plan": self.plan.receipt_metadata(),
        }


class CodeToolchainProvider(Protocol):
    provider_key: str
    toolchain_key: str

    def resolve(self) -> CodeToolchainResolution:
        """Resolve the provider-specific toolchain executable and environment."""


def resolve_toolchain_executable(
    executable_name: str,
    *,
    explicit_path: Path | None = None,
) -> Path:
    if explicit_path is not None:
        resolved = _absolute_path_without_symlink_resolution(explicit_path)
        if not resolved.is_file():
            raise CodeToolchainUnavailable(
                f"Toolchain executable does not exist: {resolved.as_posix()}"
            )
        return resolved

    discovered = shutil.which(executable_name)
    if discovered:
        return _absolute_path_without_symlink_resolution(Path(discovered))
    raise CodeToolchainUnavailable(
        f"Toolchain executable is not available on PATH: {executable_name}"
    )


def read_toolchain_version(
    executable_path: Path,
    *,
    version_args: tuple[str, ...] = ("--version",),
    env: Mapping[str, str] | None = None,
    timeout_s: float = 10.0,
) -> str | None:
    result = run_code_toolchain_command(
        CodeToolchainCommandSpec(
            provider_key="toolchain",
            toolchain_key=executable_path.name,
            role="version",
            command=(executable_path.as_posix(), *version_args),
            env=dict(env or {}),
            timeout_s=timeout_s,
        )
    )
    if result.status != "succeeded":
        return None
    text = (result.stdout or result.stderr).strip()
    if not text:
        return None
    return text.splitlines()[0].strip()


def env_from_state_roots(
    state_roots: tuple[CodeToolchainStateRoot, ...],
) -> dict[str, str]:
    env: dict[str, str] = {}
    for root in state_roots:
        binding = root.env_binding()
        if binding is not None:
            env[binding[0]] = binding[1]
    return env


def run_code_toolchain_command(
    spec: CodeToolchainCommandSpec,
    *,
    extra_env: Mapping[str, str] | None = None,
) -> CodeToolchainCommandResult:
    command = tuple(str(part) for part in spec.command)
    cwd = spec.cwd.expanduser().resolve() if spec.cwd is not None else None
    env = {**os.environ, **dict(spec.env), **dict(extra_env or {})}
    started_at = perf_counter()
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd) if cwd is not None else None,
            env=env,
            text=True,
            capture_output=True,
            timeout=spec.timeout_s,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CodeToolchainUnavailable(
            f"Toolchain command executable not found: {command[0]}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        return CodeToolchainCommandResult(
            provider_key=spec.provider_key,
            toolchain_key=spec.toolchain_key,
            role=spec.role,
            command=command,
            cwd=cwd,
            returncode=None,
            stdout=_text_output(exc.stdout),
            stderr=_text_output(exc.stderr),
            duration_s=round(perf_counter() - started_at, 6),
            timed_out=True,
        )

    return CodeToolchainCommandResult(
        provider_key=spec.provider_key,
        toolchain_key=spec.toolchain_key,
        role=spec.role,
        command=command,
        cwd=cwd,
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
        duration_s=round(perf_counter() - started_at, 6),
    )


def _text_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _absolute_path_without_symlink_resolution(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_absolute():
        return expanded
    return Path.cwd() / expanded


__all__ = [
    "CodePreparedBinaryPlan",
    "CodePreparedBinaryReceipt",
    "CodeToolchainCommandResult",
    "CodeToolchainCommandRole",
    "CodeToolchainCommandSpec",
    "CodeToolchainProvider",
    "CodeToolchainResolution",
    "CodeToolchainStateKind",
    "CodeToolchainStateRoot",
    "CodeToolchainUnavailable",
    "env_from_state_roots",
    "read_toolchain_version",
    "resolve_toolchain_executable",
    "run_code_toolchain_command",
]
