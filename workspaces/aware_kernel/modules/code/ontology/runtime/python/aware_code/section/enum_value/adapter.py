"""Interface for adapters that extract enum value information from parsed code."""

from abc import ABC, abstractmethod
from typing import override

from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.node.node import CodeNode, T_Node
from aware_code.node.adapter import CodeNodeAdapter


class CodeSectionEnumValueAdapter(CodeNodeAdapter[T_Node], ABC):
    """
    Interface for enum value adapters.

    Enum values are modeled as first-class CodeSections (CodeSectionType.enum_value).
    """

    @property
    @override
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.enum_value

    @abstractmethod
    def get_name(self, enum_value_node: CodeNode[T_Node]) -> CodeNode[T_Node]:
        """Return the ident node for the enum value name."""
        pass

    @override
    def reference_string(self, node: CodeNode[T_Node], parent: str | None = None) -> str | None:
        return self.qualname(node, parent)
