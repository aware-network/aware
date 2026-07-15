"""Interface for adapters that extract mirror directives from parsed code."""

from abc import ABC, abstractmethod
from typing import override

from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.node.node import CodeNode, T_Node
from aware_code.node.adapter import CodeNodeAdapter


class CodeSectionMirrorAdapter(CodeNodeAdapter[T_Node], ABC):
    """Interface for mirror section adapters."""

    @property
    @override
    def section_type(self) -> CodeSectionType:
        """Return the type of section."""
        return CodeSectionType.mirror

    @abstractmethod
    def get_target(self, mirror_node: CodeNode[T_Node]) -> CodeNode[T_Node]:
        """Extract the target type reference node from a mirror statement."""
        raise NotImplementedError
