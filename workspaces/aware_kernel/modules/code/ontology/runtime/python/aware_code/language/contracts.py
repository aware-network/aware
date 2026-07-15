"""Public contracts shared by Code language plugins."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from aware_code_ontology.code.code_enums import CodeLanguage


@dataclass(frozen=True)
class CodeDiscoveryFile:
    """Neutral file snapshot for code-owned discovery orchestration."""

    relative_path: str
    file_content: str
    language: CodeLanguage | None = None


@dataclass
class CodeNamespaceEntry:
    """Leaf namespace information within a grouped code layout."""

    name: str
    path: str  # Relative path within the namespace group.


@dataclass
class CodeNamespaceGroup:
    """Grouped code namespace information discovered from paths."""

    name: str
    path: str  # Relative path to the namespace group.
    entries: list[CodeNamespaceEntry]


@dataclass
class CodeNamespacePath:
    """Namespace group and entry information extracted from a file path."""

    group_name: str
    group_path: str
    entry_name: str
    entry_path: str


class StructuralFilterDecision(Enum):
    STRUCTURAL = "structural"
    NON_STRUCTURAL = "non_structural"
    UNKNOWN = "unknown"
