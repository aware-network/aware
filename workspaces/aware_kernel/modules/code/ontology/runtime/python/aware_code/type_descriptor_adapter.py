from __future__ import annotations

from abc import ABC, abstractmethod

from aware_code.type_descriptor_nodes import TypeNode


class CodeTypeDescriptorAdapter(ABC):
    """
    Language-layer adapter that parses a raw type annotation string into a language-agnostic TypeNode tree.
    """

    @abstractmethod
    def parse_type(self, type_text: str | None) -> TypeNode:
        """
        Parse a raw type annotation string into a TypeNode tree.

        Implementations should normalize Optional[T] into Union[T, None] and preserve IDENT nodes (including Self
        and quoted forward references) with flags when possible. Primitive recognition should rely on the language's
        primitive mapping.
        """
        raise NotImplementedError
