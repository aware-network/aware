"""Composite adapter that combines type and edge adapters."""

from collections.abc import Iterable
from typing_extensions import override
from typing import final

from tree_sitter import Node

from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.node.node import CodeNode
from aware_code.section.class_.adapter import CodeSectionClassAdapter

from aware_grammar.adapters.edge_adapter import AwareEdgeAdapter
from aware_grammar.adapters.class_adapter import AwareClassAdapter


@final
class AwareClassCompositeAdapter(CodeSectionClassAdapter[Node]):
    """
    Aggregates both 'type' and 'edge' adapters so the factory
    still sees a single CLASS adapter.
    """

    def __init__(self):
        self._class_adapter = AwareClassAdapter()
        self._edge_adapter = AwareEdgeAdapter()

    @property
    @override
    def section_type(self) -> CodeSectionType:
        """Return the section type - always CLASS for both types and edges."""
        return CodeSectionType.class_

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all type and edge definitions in the source.
        Marks edge nodes with a special attribute for later identification.
        """
        # First get all type nodes
        for type_node in self._class_adapter.match_nodes(root, source):
            yield type_node

        # Then get all edge nodes and mark them
        for edge_node in self._edge_adapter.match_nodes(root, source):
            yield edge_node

    @override
    def is_edge(self, class_node: CodeNode[Node]) -> bool:
        """
        Check if a node represents an edge definition.
        """
        edge_nodes = list(
            self._edge_adapter.match_nodes(class_node.node, source=class_node.node_text().encode("utf-8"))
        )
        if len(edge_nodes) == 1:
            return True
        if len(edge_nodes) > 1:
            node_text = class_node.node.text.decode("utf-8") if class_node.node.text is not None else "None"
            raise ValueError(f"Multiple edge nodes found for node: {node_text}")
        return False

    @override
    def is_augment(self, class_node: CodeNode[Node]) -> bool:
        return self._delegate(class_node).is_augment(class_node)

    @override
    def is_inline_value(self, class_node: CodeNode[Node]) -> bool:
        return self._delegate(class_node).is_inline_value(class_node)

    def _delegate(self, node: CodeNode[Node]) -> CodeSectionClassAdapter[Node]:
        """
        Delegate to the appropriate adapter based on node type.
        """
        return self._edge_adapter if self.is_edge(node) else self._class_adapter

    def get_class_adapter(self) -> AwareClassAdapter:
        return self._class_adapter

    def get_edge_adapter(self) -> AwareEdgeAdapter:
        return self._edge_adapter

    # Delegate all other methods to the appropriate adapter
    @override
    def get_name(self, class_node: CodeNode[Node]) -> CodeNode[Node]:
        return self._delegate(class_node).get_name(class_node)

    @override
    def get_attributes(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        return self._delegate(class_node).get_attributes(class_node)

    @override
    def get_methods(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        return self._delegate(class_node).get_methods(class_node)

    @override
    def get_modifiers(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        return self._delegate(class_node).get_modifiers(class_node)

    @override
    def get_keyword(self, class_node: CodeNode[Node]) -> CodeNode[Node] | None:
        return self._delegate(class_node).get_keyword(class_node)

    @override
    def get_bases(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        return self._delegate(class_node).get_bases(class_node)

    @override
    def get_verb(self, class_node: CodeNode[Node]) -> CodeNode[Node] | None:
        return self._delegate(class_node).get_verb(class_node)

    @override
    def get_verb_target(self, class_node: CodeNode[Node]) -> CodeNode[Node] | None:
        return self._delegate(class_node).get_verb_target(class_node)

    @override
    def get_annotations(self, class_node: CodeNode[Node]) -> list[str] | None:
        """
        Delegate annotation lookup to the underlying type/edge adapter.
        """
        return self._delegate(class_node).get_annotations(class_node)

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        return self._delegate(node).qualname(node, parent)

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        return self._delegate(node).body_bytes(node, source)

    @override
    def reference_string(self, node: CodeNode[Node], parent: str | None = None) -> str | None:
        return self._delegate(node).reference_string(node, parent)
