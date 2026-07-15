"""Aware implementation of the CodeSectionClassAdapter for Class."""

from collections.abc import Iterable
import re
from typing_extensions import override
from typing import final

# Tree-sitter
from tree_sitter import Node
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

# Aware Primitive Code
from aware_code.section.class_.adapter import CodeSectionClassAdapter
from aware_code.node.node import CodeNode

# Aware Modifiers
from aware_grammar.modifiers import TypeModifier


@final
class AwareClassAdapter(CodeSectionClassAdapter[Node]):
    """
    Implementation of CodeSectionClassAdapter for Aware language using Tree-sitter.

    Maps `class` definitions in Aware to class sections.
    """

    # Pre-compiled queries for finding class definitions
    TYPE_QUERY = AWARE_LANGUAGE.query(
        """
        (class_def) @class
        """
    )

    TYPE_NAME_QUERY = AWARE_LANGUAGE.query(
        """
        (class_def
          name: (ident) @class_name)
        """
    )

    FIELD_QUERY = AWARE_LANGUAGE.query(
        """
        (class_def
          (attr_def) @attr)
        """
    )

    FN_QUERY = AWARE_LANGUAGE.query(
        """
        (class_def
          (fn_def) @function)
        """
    )

    # Add new query for class modifiers
    TYPE_MODS_QUERY = AWARE_LANGUAGE.query(
        """
        (class_def
          modifiers: (class_mods
            (class_attr) @class_attr))
        """
    )

    TYPE_VERB_QUERY = AWARE_LANGUAGE.query(
        """
        (class_def
          verb: (class_verb) @class_verb)
        """
    )

    VERB_TARGET_QUERY = AWARE_LANGUAGE.query(
        """
        (class_def
          verb_target: (type_ref) @verb_target)
        """
    )
    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all type definitions in the Aware source.

        Args:
            root: The root node of the parse tree
            source: The source code as bytes

        Returns:
            Iterable of nodes representing type definitions
        """
        # Use pre-compiled query
        captures = self.TYPE_QUERY.captures(root)
        for cls_node in captures.get("class", []):
            yield CodeNode(node=cls_node, byte_start=cls_node.start_byte, byte_end=cls_node.end_byte)

    @override
    def get_name(self, class_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the type name from a type definition.

        Args:
            class_node: Node representing a type definition

        Returns:
            Node representing the type name
        """
        # Use pre-compiled query
        captures = self.TYPE_NAME_QUERY.captures(class_node.node)
        if "class_name" in captures and captures["class_name"]:
            name_node = captures["class_name"][0]
            return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)

        # Fallback - should not happen with valid syntax
        raise ValueError(f"No class name found in class definition, on Node: {class_node.node_text()}")

    @override
    def get_attributes(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract field definitions as attributes.

        Args:
            class_node: Node representing a type definition

        Returns:
            Iterable of nodes representing field definitions
        """
        # Use pre-compiled query
        captures = self.FIELD_QUERY.captures(class_node.node)
        for attr_node in captures.get("attr", []):
            yield CodeNode(node=attr_node, byte_start=attr_node.start_byte, byte_end=attr_node.end_byte)

    @override
    def get_methods(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract function definitions as methods.

        Args:
            class_node: Node representing a type definition

        Returns:
            Iterable of nodes representing function definitions
        """
        captures = self.FN_QUERY.captures(class_node.node)
        if "function" in captures:
            for fn_node in sorted(captures["function"], key=lambda node: node.start_byte):
                yield CodeNode(node=fn_node, byte_start=fn_node.start_byte, byte_end=fn_node.end_byte)

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a fully-qualified name for an Aware type.

        Args:
            node: The class node to get the qualified name for
            parent: Optional parent namespace

        Returns:
            Qualified name string
        """
        # Get type name
        name_node = self.get_name(node)
        name_text = name_node.node_text()

        # If we have a parent namespace, prepend it
        if parent:
            return f"{parent}.{name_text}"

        return name_text

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for an Aware type definition.

        This strips comments and normalizes whitespace to create a consistent
        hash regardless of formatting changes.

        Args:
            node: The type node to get body bytes for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        # Extract the node's bytes
        node_bytes = source[node.byte_start:node.byte_end]

        # Remove comments
        normalized = re.sub(
            b"//[^\n]*",  # Remove single-line comments
            b"",  # Replace with empty string
            node_bytes,  # Input
            flags=re.MULTILINE,  # Multi-line mode
        )

        # Normalize whitespace
        normalized = re.sub(b"\\s+", b" ", normalized)

        # Remove trailing/leading whitespace
        normalized = normalized.strip()

        return normalized

    def get_typed_modifiers(self, class_node: CodeNode[Node]) -> TypeModifier:
        """
        Extract typed modifiers from a type definition.

        Args:
            class_node: Node representing a type definition

        Returns:
            TypeModifier containing typed modifiers
        """
        modifiers: list[CodeNode[Node]] = list(self.get_modifiers(class_node))
        mod_strings: list[str] = [mod_node.node_text() for mod_node in modifiers]
        return TypeModifier.from_strings(mod_strings)

    @override
    def get_modifiers(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract modifiers nodes from a type definition.

        Args:
            class_node: Node representing a type definition

        Returns:
            Iterable of nodes representing type modifiers
        """
        captures = self.TYPE_MODS_QUERY.captures(class_node.node)

        for mod_node in captures.get("class_attr", []) or []:
            yield CodeNode(node=mod_node, byte_start=mod_node.start_byte, byte_end=mod_node.end_byte)

    @override
    def get_verb(self, class_node: CodeNode[Node]) -> CodeNode[Node] | None:
        """
        Extract the verb/operator node (e.g., 'augment') from a type definition, if present.

        Args:
            class_node: Node representing a type definition

        Returns:
            Node representing the verb/operator or None if absent
        """
        captures = self.TYPE_VERB_QUERY.captures(class_node.node)
        verbs = captures.get("class_verb") if captures else None
        if verbs:
            verb_node = verbs[0]
            return CodeNode(node=verb_node, byte_start=verb_node.start_byte, byte_end=verb_node.end_byte)
        return None

    @override
    def get_verb_target(self, class_node: CodeNode[Node]) -> CodeNode[Node] | None:
        """Return the verb target (e.g., class being augmented), if any."""
        captures = self.VERB_TARGET_QUERY.captures(class_node.node)
        targets = captures.get("verb_target") if captures else None
        if targets:
            node = targets[0]
            return CodeNode(node=node, byte_start=node.start_byte, byte_end=node.end_byte)
        return None

    @override
    def is_augment(self, class_node: CodeNode[Node]) -> bool:
        """
        Return True if the type definition declares the `augment` verb.
        """
        verb_node = self.get_verb(class_node)
        if not verb_node:
            return False
        verb_text = verb_node.node_text()
        return verb_text == "augment"

    @override
    def get_keyword(self, class_node: CodeNode[Node]) -> CodeNode[Node] | None:
        """
        Extract the 'type' keyword node from a type definition.

        Args:
            class_node: Node representing a type definition

        Returns:
            Node representing the 'type' keyword
        """
        # The first child of a class_def should be the 'class' keyword
        for child in class_node.node.children:
            if child.type == "class":
                return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
        return None

    @override
    def get_bases(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract base class nodes from a type definition.

        Canonical Aware:
        - There is no inheritance syntax (`class Foo extends Bar`) today.
        - `augment` is treated as a base relationship for downstream OCG (Foo augments Bar),
          so we surface the verb target as a base node when present.

        Args:
            class_node: Node representing a type definition

        Returns:
            Iterable of nodes representing the base classes (augment target only)
        """
        if self.is_augment(class_node):
            target = self.get_verb_target(class_node)
            if target is not None:
                yield target
        return

    # Inline value mode (type/value semantics)
    @override
    def is_inline_value(self, class_node: CodeNode[Node]) -> bool:
        """
        Check if a type is marked as inline_value.

        Inline-value classes are SSOT type nodes but do not participate in the
        Object Instance Graph; they are serialized inline (e.g., function args/returns).
        """
        modifiers = self.get_typed_modifiers(class_node)
        return modifiers.inline_value

    # Ownership is not a topology grammar concept; removed.

    @override
    def reference_string(self, node: CodeNode[Node], parent: str | None = None) -> str | None:
        """
        Return a reference string for this type that can be used to match comments.

        Args:
            node: The type node
            parent: Optional parent context

        Returns:
            Reference string for comment matching
        """
        # Delegate to qualname method for consistent lookup keys
        return self.qualname(node, parent)

    @override
    def get_annotations(self, class_node: CodeNode[Node]) -> list[str] | None:
        """
        Return annotations associated with this type definition, if any.

        Annotation collection will be implemented once the Aware grammar
        and object graph builders are wired for `ann` statements.
        """
        return None
