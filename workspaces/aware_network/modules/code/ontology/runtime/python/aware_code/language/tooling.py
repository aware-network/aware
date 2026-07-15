"""Language-owned tooling contracts for workspace execution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from aware_code_ontology.code.code_enums import CodeLanguage

CodeLanguageToolRole = Literal[
    "formatter",
    "dependency_resolver",
    "code_generator",
    "analyzer",
    "package_builder",
    "package_checker",
    "publisher",
]
CodeLanguageToolBackend = Literal[
    "python_api",
    "cli",
    "workspace_tool",
]
CodeLanguageToolTargetMode = Literal[
    "paths",
    "package_root",
    "repo_root",
    "none",
]
CodeLanguageToolStateKind = Literal[
    "home",
    "cache",
    "config",
]


@dataclass(frozen=True, slots=True)
class CodeLanguageToolStateRequirement:
    """State root a language tool needs to run without leaking into user/global state."""

    key: str
    kind: CodeLanguageToolStateKind
    env_var: str | None = None
    default_subdir: str | None = None
    required: bool = True


@dataclass(frozen=True, slots=True)
class CodeLanguageToolSpec:
    """Language plugin declaration for a formatter, resolver, generator, or analyzer."""

    tool_id: str
    language: CodeLanguage
    role: CodeLanguageToolRole
    description: str
    backend: CodeLanguageToolBackend
    target_mode: CodeLanguageToolTargetMode = "paths"
    command: tuple[str, ...] = ()
    module: str | None = None
    callable_name: str | None = None
    version_package: str | None = None
    default_timeout_s: float | None = None
    default_batch_size: int | None = None
    mutates_targets: bool = False
    network: bool = False
    state_requirements: tuple[CodeLanguageToolStateRequirement, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)
