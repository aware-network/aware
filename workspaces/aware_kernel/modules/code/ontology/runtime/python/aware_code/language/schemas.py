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
class CodeSchema:
    """Schema information within a domain."""

    name: str
    path: str  # Relative path within domain (e.g., "identity" or "aware_identity/identity")


@dataclass
class CodeDomain:
    """Domain information with its schemas."""

    name: str
    path: str  # Relative path to domain (e.g., "domains/identity")
    schemas: list[CodeSchema]


@dataclass
class CodeDomainSchema:
    """Domain and schema information extracted from a file path."""

    domain_name: str
    domain_path: str  # Relative path to domain (e.g., "domains/identity")
    schema_name: str
    schema_path: str  # Relative path within domain (e.g., "identity" or "aware_identity/identity")


class StructuralFilterDecision(Enum):
    STRUCTURAL = "structural"
    NON_STRUCTURAL = "non_structural"
    UNKNOWN = "unknown"
