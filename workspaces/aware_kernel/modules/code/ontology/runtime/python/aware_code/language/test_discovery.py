"""Language-owned code test discovery contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType


@dataclass(frozen=True, slots=True)
class CodeTestDiscoverySection:
    """Resolved section truth available to language test discovery."""

    code_section_id: UUID
    section_key: str
    qualname: str
    section_type: CodeSectionType


@dataclass(frozen=True, slots=True)
class CodeTestDiscoveryCode:
    """One package-owned Code snapshot available to test discovery."""

    relative_path: str
    content_text: str
    sections: tuple[CodeTestDiscoverySection, ...] = ()


@dataclass(frozen=True, slots=True)
class CodeTestDiscoveryContext:
    """Package scope passed to a language-owned test discovery plugin."""

    package_name: str
    language: CodeLanguage
    manifest_kind: str
    manifest_relative_path: str
    package_root: str
    sources_root: str | None
    manifest_text: str | None
    codes: tuple[CodeTestDiscoveryCode, ...] = ()

    @property
    def manifest_name(self) -> str:
        return Path(self.manifest_relative_path).name


@dataclass(frozen=True, slots=True)
class CodeTestFrameworkDiscoveryDescriptor:
    """Framework identity plus package declaration provenance."""

    name: str
    title: str | None = None
    declaration_kind: str = "unknown"
    declaration_ref: str | None = None


@dataclass(frozen=True, slots=True)
class CodeTestUnitDiscoveryDescriptor:
    """One runnable unit attached to existing CodeSection truth."""

    framework_name: str
    relative_path: str
    code_section_id: UUID
    unit_key: str
    selector: str
    kind: str = "function"
    name: str | None = None


@dataclass(frozen=True, slots=True)
class CodeTestDiscoveryResult:
    """Language-owned framework and test-unit discovery output."""

    frameworks: tuple[CodeTestFrameworkDiscoveryDescriptor, ...] = ()
    units: tuple[CodeTestUnitDiscoveryDescriptor, ...] = ()


class CodeLanguageTestDiscovery(ABC):
    """Base contract for package-scoped language test discovery."""

    @abstractmethod
    def discover(self, context: CodeTestDiscoveryContext) -> CodeTestDiscoveryResult:
        """Discover declared frameworks and runnable units for one code package."""
        raise NotImplementedError


EMPTY_CODE_TEST_DISCOVERY_RESULT = CodeTestDiscoveryResult()


__all__ = [
    "CodeLanguageTestDiscovery",
    "CodeTestDiscoveryCode",
    "CodeTestDiscoveryContext",
    "CodeTestDiscoveryResult",
    "CodeTestDiscoverySection",
    "CodeTestFrameworkDiscoveryDescriptor",
    "CodeTestUnitDiscoveryDescriptor",
    "EMPTY_CODE_TEST_DISCOVERY_RESULT",
]
