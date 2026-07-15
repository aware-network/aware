"""Dart implementation of the CodeSectionFunctionAdapter."""

from collections.abc import Iterable
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query

# Aware Kernel Graph Ontology
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.function.adapter import CodeSectionFunctionAdapter

# Dart Grammar
from dart_grammar._tree_sitter_dart import DART_LANGUAGE


class DartFunctionAdapter(CodeSectionFunctionAdapter[Node]):
    """Extract top-level functions and class methods in Dart."""

    # Match any function_signature at top-level or inside class bodies
    FUNCTION_SIGNATURES_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (function_signature) @sig
        (class_definition body: (class_body (method_signature) @sig))
        """
    )

    # Names are on function_signature. When inside method_signature, descend to function_signature
    SIGNATURE_NAME_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (function_signature name: (identifier) @name)
        (method_signature (function_signature name: (identifier) @name))
        """
    )

    # Return types: capture named type nodes present at the beginning of function_signature
    RETURN_TYPE_QUERY: Query = DART_LANGUAGE.query(
        r"""
        (function_signature (void_type) @ret)
        (function_signature (function_type) @ret)
        (function_signature (record_type) @ret)
        (function_signature (type_identifier) @ret)
        (method_signature (function_signature (void_type) @ret))
        (method_signature (function_signature (function_type) @ret))
        (method_signature (function_signature (record_type) @ret))
        (method_signature (function_signature (type_identifier) @ret))
        """
    )

    @property
    @override
    def section_type(self) -> CodeSectionType:
        return CodeSectionType.function

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        return source[node.byte_start:node.byte_end]

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        caps = self.FUNCTION_SIGNATURES_QUERY.captures(root)
        for sig in caps.get("sig", []):
            yield CodeNode(node=sig, byte_start=sig.start_byte, byte_end=sig.end_byte)

    @override
    def get_name(self, function_node: CodeNode[Node]) -> CodeNode[Node]:
        caps = self.SIGNATURE_NAME_QUERY.captures(function_node.node)
        vals = caps.get("name", [])
        if vals:
            n = vals[0]
            return CodeNode(node=n, byte_start=n.start_byte, byte_end=n.end_byte)
        return function_node

    @override
    def get_signature(self, function_node: CodeNode[Node]) -> CodeNode[Node]:
        return function_node

    @override
    def get_body(self, function_node: CodeNode[Node]) -> CodeNode[Node] | None:
        # heuristic: body often follows signature in same parent
        parent = function_node.node.parent
        if parent:
            siblings = list(parent.children)
            try:
                idx = siblings.index(function_node.node)
                if idx + 1 < len(siblings) and siblings[idx + 1].type == "function_body":
                    b = siblings[idx + 1]
                    return CodeNode(node=b, byte_start=b.start_byte, byte_end=b.end_byte)
            except ValueError:
                pass
        return None

    @override
    def get_parameters(self, function_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        # If node is a method_signature, find nested function_signature first
        node = function_node.node
        if node.type == "method_signature":
            for ch in node.children:
                if ch.type == "function_signature":
                    node = ch
                    break
        for ch in node.children:
            if ch.type in {"_formal_parameter_part", "formal_parameter_list"}:
                yield CodeNode(node=ch, byte_start=ch.start_byte, byte_end=ch.end_byte)

    @override
    def get_return_type(self, function_node: CodeNode[Node]) -> CodeNode[Node] | None:
        caps = self.RETURN_TYPE_QUERY.captures(function_node.node)
        vals = caps.get("ret", [])
        if vals:
            r = vals[0]
            return CodeNode(node=r, byte_start=r.start_byte, byte_end=r.end_byte)
        return None

    @override
    def is_async(self, function_node: CodeNode[Node]) -> bool:
        for ch in function_node.node.children:
            if ch.text == b"async":
                return True
        return False

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        name_node = self.get_name(node)
        text = name_node.node_text()
        return (f"{parent}." if parent else "") + text

    # --- Optional helpers with conservative defaults ---
    @override
    def is_public(self, function_node: CodeNode[Node]) -> bool:
        # Conservative default: consider public unless name starts with underscore
        text = self.get_name(function_node).node_text()
        return not text.startswith("_")

    @override
    def reference_string(self, node: CodeNode[Node], parent: str | None = None) -> str | None:
        """Return a reference string for a Dart function."""
        return self.qualname(node, parent)
