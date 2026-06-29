"""Language-owned operational workspace contract for code packages."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Mapping, Protocol

from aware_code_ontology.code.code_enums import CodeLanguage


CodeOperationalPackageRole = Literal["platform_runtime", "workspace_revision"]
CodeLanguageOperationalWorkspaceStatus = Literal["empty", "ready"]


@dataclass(frozen=True, slots=True)
class CodeLanguageOperationalPackageRef:
    """One committed language package selected into an operational workspace."""

    package_name: str
    language: CodeLanguage
    role: CodeOperationalPackageRole
    source_root: Path | None = None
    manifest_path: Path | None = None
    authority: str | None = None
    required: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CodeLanguageOperationalWorkspaceRequest:
    """Request to materialize a language-specific workspace manifest."""

    workspace_key: str
    language: CodeLanguage
    output_root: Path
    packages: tuple[CodeLanguageOperationalPackageRef, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CodeLanguageOperationalWorkspaceResult:
    """Materialized operational workspace description."""

    workspace_key: str
    language: CodeLanguage
    status: CodeLanguageOperationalWorkspaceStatus
    output_root: Path
    manifest_path: Path
    packages: tuple[CodeLanguageOperationalPackageRef, ...]
    project_path: Path | None = None
    command_prefix: tuple[str, ...] = ()
    environment: Mapping[str, str] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)


class CodeLanguageOperationalWorkspaceBuilder(Protocol):
    """Language plugin hook for materializing operational workspace manifests."""

    def materialize_operational_workspace(
        self,
        request: CodeLanguageOperationalWorkspaceRequest,
    ) -> CodeLanguageOperationalWorkspaceResult:
        """Materialize the operational workspace and return its contract."""
        ...


__all__ = [
    "CodeLanguageOperationalPackageRef",
    "CodeLanguageOperationalWorkspaceBuilder",
    "CodeLanguageOperationalWorkspaceRequest",
    "CodeLanguageOperationalWorkspaceResult",
    "CodeLanguageOperationalWorkspaceStatus",
    "CodeOperationalPackageRole",
]
