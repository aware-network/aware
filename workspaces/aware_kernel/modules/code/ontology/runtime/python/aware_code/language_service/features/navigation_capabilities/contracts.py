from __future__ import annotations

from pathlib import Path
from typing import Protocol

from tree_sitter import Node

from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_code_ontology.enum.code_section_enum_value import CodeSectionEnumValue
from aware_code_ontology.function.code_section_function import CodeSectionFunction
from aware_code.language_service.position import ByteRange
from aware_code.language_service.types import DefinitionTarget, ResolvedSymbol
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig


class CursorInRangeMatcher(Protocol):
    def __call__(self, *, byte_offset: int, start: int, end: int) -> bool: ...


class NodeTextReader(Protocol):
    def __call__(self, node: Node | None) -> str: ...


class ProjectionTargetResolver(Protocol):
    def __call__(self, *, uri: str, symbol: str) -> list[DefinitionTarget]: ...


class SymbolTargetResolver(Protocol):
    def __call__(self, *, uri: str, symbol: str) -> list[DefinitionTarget]: ...


class ExperienceNodeTargetResolver(Protocol):
    def __call__(
        self,
        *,
        uri: str,
        experience_symbol: str,
        node_symbol: str,
    ) -> list[DefinitionTarget]: ...


class ClassDefinitionTargetResolver(Protocol):
    def __call__(self, class_cfg: ClassConfig) -> DefinitionTarget | None: ...


class EnumDefinitionTargetResolver(Protocol):
    def __call__(self, enum_cfg: EnumConfig) -> DefinitionTarget | None: ...


class AttributeDefinitionTargetResolver(Protocol):
    def __call__(self, attr: CodeSectionAttribute) -> DefinitionTarget | None: ...


class FunctionDefinitionTargetResolver(Protocol):
    def __call__(self, fn: CodeSectionFunction) -> DefinitionTarget | None: ...


class UriToPathResolver(Protocol):
    def __call__(self, uri: str) -> Path: ...


class PathToUriResolver(Protocol):
    def __call__(self, path: Path) -> str: ...


class UriDocumentTextReader(Protocol):
    def __call__(self, uri: str) -> str: ...


class EnumValueDefinitionTargetResolver(Protocol):
    def __call__(self, val: CodeSectionEnumValue) -> DefinitionTarget | None: ...


class AnnotationPathSegmentFinder(Protocol):
    def __call__(self, *, byte_offset: int, document_bytes: bytes) -> ByteRange | None: ...


class SymbolAtOffsetResolver(Protocol):
    def __call__(
        self,
        *,
        uri: str,
        byte_offset: int,
        document_bytes: bytes,
        document_text: str,
    ) -> ResolvedSymbol | None: ...
