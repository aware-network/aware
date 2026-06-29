"""Interface for adapters that extract projection declarations from parsed code."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, override

from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.node.node import CodeNode, T_Node
from aware_code.node.adapter import CodeNodeAdapter


@dataclass(frozen=True, slots=True)
class ProjectionOptionSpec(Generic[T_Node]):
    """Raw projection option nodes for lossless segment capture."""

    keyword: str
    value_node: CodeNode[T_Node] | None


@dataclass(frozen=True, slots=True)
class ProjectionViewSpec(Generic[T_Node]):
    """Flattened view definition with resolved full key."""

    key_node: CodeNode[T_Node]
    full_key: str
    kind_node: CodeNode[T_Node]
    kind: str
    is_default: bool
    body_node: CodeNode[T_Node]


class CodeSectionProjectionAdapter(CodeNodeAdapter[T_Node], ABC):
    """Interface for projection section adapters."""

    @property
    @override
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.projection

    @abstractmethod
    def get_name(self, projection_node: CodeNode[T_Node]) -> CodeNode[T_Node]:
        raise NotImplementedError

    @abstractmethod
    def get_options(self, projection_node: CodeNode[T_Node]) -> list[ProjectionOptionSpec[T_Node]]:
        raise NotImplementedError

    @abstractmethod
    def get_root_type(self, projection_node: CodeNode[T_Node]) -> CodeNode[T_Node] | None:
        raise NotImplementedError

    @abstractmethod
    def get_edges(self, projection_node: CodeNode[T_Node]) -> list[CodeNode[T_Node]]:
        raise NotImplementedError

    @abstractmethod
    def get_edge_type(self, edge_node: CodeNode[T_Node]) -> CodeNode[T_Node]:
        raise NotImplementedError

    @abstractmethod
    def get_edge_member(self, edge_node: CodeNode[T_Node]) -> CodeNode[T_Node]:
        raise NotImplementedError

    @abstractmethod
    def get_edge_target(self, edge_node: CodeNode[T_Node]) -> CodeNode[T_Node] | None:
        raise NotImplementedError

    @abstractmethod
    def get_views(self, projection_node: CodeNode[T_Node]) -> list[ProjectionViewSpec[T_Node]]:
        raise NotImplementedError
