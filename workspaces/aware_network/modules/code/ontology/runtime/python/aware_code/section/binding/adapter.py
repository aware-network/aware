"""Interface for adapters that extract binding declarations from parsed code."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, override

from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.node.adapter import CodeNodeAdapter
from aware_code.node.node import CodeNode, T_Node


@dataclass(frozen=True, slots=True)
class BindingMapSpec(Generic[T_Node]):
    name_node: CodeNode[T_Node]
    source_node: CodeNode[T_Node]
    target_node: CodeNode[T_Node]
    body_node: CodeNode[T_Node] | None
    template_value_node: CodeNode[T_Node] | None


class CodeSectionBindingAdapter(CodeNodeAdapter[T_Node], ABC):
    """Interface for binding section adapters."""

    @property
    @override
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.binding

    @abstractmethod
    def get_source_graph(self, binding_node: CodeNode[T_Node]) -> CodeNode[T_Node]:
        raise NotImplementedError

    @abstractmethod
    def get_target_graph(self, binding_node: CodeNode[T_Node]) -> CodeNode[T_Node]:
        raise NotImplementedError

    @abstractmethod
    def get_maps(self, binding_node: CodeNode[T_Node]) -> list[BindingMapSpec[T_Node]]:
        raise NotImplementedError
