"""Language-owned execution closure contract for code packages."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Mapping, Protocol


CodeExecutionPackageRole = Literal["platform_runtime", "workspace_revision"]


@dataclass(frozen=True, slots=True)
class CodeLanguageExecutionPackageRef:
    """One language package selected into an execution closure."""

    package_name: str
    role: CodeExecutionPackageRole
    source_root: Path | None = None
    manifest_path: Path | None = None
    authority: str | None = None
    copy_to_closure: bool = False
    required: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CodeLanguageExecutionLauncher:
    """Runtime module entrypoint expected to be launchable from the closure."""

    launcher_key: str
    module: str
    package_name: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class CodeLanguageExecutionClosureRequest:
    """Request to materialize a language-specific execution closure."""

    closure_key: str
    output_root: Path
    packages: tuple[CodeLanguageExecutionPackageRef, ...]
    launchers: tuple[CodeLanguageExecutionLauncher, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CodeLanguageExecutionClosureResult:
    """Materialized execution closure description."""

    closure_key: str
    output_root: Path
    project_path: Path
    manifest_path: Path
    packages: tuple[CodeLanguageExecutionPackageRef, ...]
    launchers: tuple[CodeLanguageExecutionLauncher, ...] = ()
    command_prefix: tuple[str, ...] = ()
    environment: Mapping[str, str] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)


class CodeLanguageExecutionClosureBuilder(Protocol):
    """Language plugin hook for materializing executable package closures."""

    def materialize_execution_closure(
        self,
        request: CodeLanguageExecutionClosureRequest,
    ) -> CodeLanguageExecutionClosureResult:
        """Materialize the closure and return its runnable contract."""
        ...


__all__ = [
    "CodeExecutionPackageRole",
    "CodeLanguageExecutionClosureBuilder",
    "CodeLanguageExecutionClosureRequest",
    "CodeLanguageExecutionClosureResult",
    "CodeLanguageExecutionLauncher",
    "CodeLanguageExecutionPackageRef",
]
