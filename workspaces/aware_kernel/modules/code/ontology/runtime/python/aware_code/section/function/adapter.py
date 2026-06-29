"""Interface for adapters that extract function information from parsed code."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import override

from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.node.node import CodeNode, T_Node
from aware_code.node.adapter import CodeNodeAdapter


class CodeSectionFunctionAdapter(CodeNodeAdapter[T_Node], ABC):
    """
    Interface for function section adapters.

    Implementations will extract function-related information from language-specific
    parse trees while maintaining consistent positional information.
    """

    @property
    @override
    def section_type(self) -> CodeSectionType:
        """Return the type of section."""
        return CodeSectionType.function

    @abstractmethod
    def get_name(self, function_node: CodeNode[T_Node]) -> CodeNode[T_Node]:
        pass

    @abstractmethod
    def get_signature(self, function_node: CodeNode[T_Node]) -> CodeNode[T_Node]:
        pass

    @abstractmethod
    def get_body(self, function_node: CodeNode[T_Node]) -> CodeNode[T_Node] | None:
        pass

    @abstractmethod
    def get_parameters(self, function_node: CodeNode[T_Node]) -> Iterable[CodeNode[T_Node]]:
        pass

    @abstractmethod
    def get_return_type(self, function_node: CodeNode[T_Node]) -> CodeNode[T_Node] | None:
        pass

    @abstractmethod
    def is_async(self, function_node: CodeNode[T_Node]) -> bool:
        pass

    # --- Language-agnostic defaults (optional helpers) ---
    def is_classmethod(self, _function_node: CodeNode[T_Node]) -> bool:
        """
        Return whether the function is a class method.
        Default: False. Language adapters can override for accuracy.
        """
        return False

    def is_staticmethod(self, _function_node: CodeNode[T_Node]) -> bool:
        """
        Return whether the function is a static method.
        Default: False. Language adapters can override for accuracy.
        """
        return False

    def is_public(self, _function_node: CodeNode[T_Node]) -> bool:
        """
        Return whether the function should be considered public. Default: True.
        Language adapters can override with language-specific rules.
        """
        return True

    def get_verb(self, _function_node: CodeNode[T_Node]) -> str | None:
        """
        Optional verb modifier (e.g., constructor verbs). Default: None.
        Language adapters may override to surface verb metadata.
        """
        return None

    def get_return_parameters(self, _function_node: CodeNode[T_Node]) -> Iterable[CodeNode[T_Node]] | None:
        """
        Return the return parameters for a function.
        Language adapters may override if they support named return parameters.
        """
        return None
