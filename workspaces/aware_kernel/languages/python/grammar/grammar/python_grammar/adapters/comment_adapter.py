"""Python implementation of the CodeSectionCommentAdapter."""

from __future__ import annotations
from enum import Enum
from collections.abc import Iterable
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query

# Kernel Graph Ontology
from aware_code_ontology.comment.code_section_comment_enums import CodeSectionCommentType

# Code Runtime
from aware_code.section.comment.adapter import CodeSectionCommentAdapter
from aware_code.node.node import CodeNode
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Tree-sitter Python
from python_grammar._tree_sitter_python import PYTHON_LANGUAGE

from aware_utils.logging import logger


class PythonCommentTargetType(str, Enum):
    """Type of Python entity that a comment is associated with."""

    UNKNOWN = "unknown"
    CLASS = "class"
    METHOD = "method"
    FUNCTION = "function"
    ATTRIBUTE = "attribute"
    MODULE = "module"
    DECORATOR = "decorator"


def _decode_node_text(node: Node) -> str:
    text = node.text
    if text is None:
        return ""
    return text.decode("utf-8")


def debug_children(node: Node, src: bytes, depth: int = 0) -> None:
    indent = " " * (2 * depth)
    for child in node.children:
        child_text = child.text.decode("utf-8") if child.text else ""
        child_bytes = src[child.start_byte:child.end_byte]
        logger.info(
            f"{indent}Child: {child_text}:{child.type}  {child_bytes!r}"
        )
        debug_children(child, src, depth + 1)


def debug_parent(node: Node, src: bytes, depth: int = 0) -> None:
    if node.parent:
        indent = " " * (2 * depth)
        logger.info(f"{indent}Parent: {node.parent.type}")
        debug_parent(node.parent, src, depth + 1)


class PythonCommentAdapter(CodeSectionCommentAdapter[Node]):
    """
    Implementation of CodeSectionCommentAdapter for Python using Tree-sitter.

    Extracts comments from Python parse trees.
    """

    # Pre-compiled query for finding comments
    COMMENT_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (comment) @comment
        """
    )

    # Query to find docstrings in different contexts
    MODULE_DOCSTRING_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (module
          (expression_statement
            (string) @docstring))
        """
    )

    CLASS_NAME_QUERY: Query = PYTHON_LANGUAGE.query("(class_definition name: (identifier) @name)")

    CLASS_DOCSTRING_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (class_definition
          body: (block
            (expression_statement
              (string) @docstring)))
        """
    )

    FUNCTION_DOCSTRING_QUERY: Query = PYTHON_LANGUAGE.query(
        """
        (function_definition
          body: (block
            (expression_statement
              (string) @docstring)))
        """
    )

    FUNCTION_NAME_QUERY: Query = PYTHON_LANGUAGE.query("(function_definition name: (identifier) @name)")

    ASSIGNMENT_LEFT_QUERY: Query = PYTHON_LANGUAGE.query("(assignment left: (identifier) @name)")

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all comments in the Python source code.

        Args:
            root: The root node of the parse tree
            source: The Python source code as bytes

        Returns:
            Iterable of nodes representing comments
        """
        # Find standard comments (# ...) throughout the entire tree
        captures = self.COMMENT_QUERY.captures(root)
        if "comment" in captures:
            for comment_node in captures["comment"]:
                yield CodeNode(node=comment_node, byte_start=comment_node.start_byte, byte_end=comment_node.end_byte)

        # Find module docstrings
        captures = self.MODULE_DOCSTRING_QUERY.captures(root)
        if "docstring" in captures:
            for docstring_node in captures["docstring"]:
                # Only consider the first string at module level as a docstring
                if docstring_node.start_byte == self._find_first_string_position(root):
                    yield CodeNode(
                        node=docstring_node, byte_start=docstring_node.start_byte, byte_end=docstring_node.end_byte
                    )

        # Find all class docstrings
        captures = self.CLASS_DOCSTRING_QUERY.captures(root)
        if "docstring" in captures:
            for docstring_node in captures["docstring"]:
                yield CodeNode(
                    node=docstring_node, byte_start=docstring_node.start_byte, byte_end=docstring_node.end_byte
                )

        # Find all function docstrings
        captures = self.FUNCTION_DOCSTRING_QUERY.captures(root)
        if "docstring" in captures:
            for docstring_node in captures["docstring"]:
                yield CodeNode(
                    node=docstring_node, byte_start=docstring_node.start_byte, byte_end=docstring_node.end_byte
                )

    def _find_first_string_position(self, root: Node) -> int:
        """
        Find the position of the first string in the module.

        Args:
            root: The root node of the parse tree

        Returns:
            The byte position of the first string, or -1 if not found
        """
        for child in root.children:
            if child.type == "expression_statement":
                for grandchild in child.children:
                    if grandchild.type == "string":
                        return grandchild.start_byte
        return -1

    @override
    def get_content_segments(self, comment_node: CodeNode[Node], source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Extract comment content as segments for Python comments.

        For regular comments (#), this strips the leading # and any whitespace.
        For docstrings, it removes the quotes and yields single segment.

        Args:
            comment_node: Node representing a comment
            source: The source code as bytes

        Returns:
            Iterable of nodes representing individual content segments
        """
        if comment_node.node.type == "comment":
            # For regular comments, we need to strip the leading '#' and whitespace
            content = comment_node.node.text
            if content and content.startswith(b"#"):
                # Skip the # and any following whitespace
                i = 1
                while i < len(content) and content[i:i + 1].isspace():
                    i += 1

                # Only yield if there's actual content after the markers
                adjusted_start = comment_node.byte_start + i
                if adjusted_start < comment_node.byte_end:
                    yield CodeNode(node=comment_node.node, byte_start=adjusted_start, byte_end=comment_node.byte_end)

        elif comment_node.node.type == "string":
            # For docstrings, return the content without the quotes
            # This is an approximation since we don't have direct access to string content
            # A more accurate approach would process the actual bytes
            if comment_node.node.text and comment_node.node.text.startswith((b'"""', b"'''")):
                # Triple quoted string
                content_start = comment_node.byte_start + 3
                content_end = comment_node.byte_end - 3
            else:
                # Single quoted string
                content_start = comment_node.byte_start + 1
                content_end = comment_node.byte_end - 1

            # Only yield if there's actual content
            if content_start < content_end:
                yield CodeNode(
                    node=comment_node.node,
                    byte_start=content_start,
                    byte_end=content_end,
                )

    @override
    def get_comment_type(self, comment_node: CodeNode[Node]) -> CodeSectionCommentType:
        """
        Determine the type of Python comment.

        Args:
            comment_node: Node representing a comment

        Returns:
            The comment type (line, block, doc, metadata)
        """
        if comment_node.node.type == "comment":
            # Standard Python comment (#) is a line comment
            return CodeSectionCommentType.line
        elif comment_node.node.type == "string":
            # String expressions at the beginning of a module, class, or function are docstrings
            return CodeSectionCommentType.doc

        # Default
        return CodeSectionCommentType.line

    @override
    def get_associated_node(self, comment_node: CodeNode[Node], source: bytes) -> CodeNode[Node] | None:
        """
        Find the node that this comment is associated with, if any.

        This looks at the code structure to determine what the comment is likely documenting.
        For comments followed by a class, function, method, or assignment, we associate the comment with that entity.

        Args:
            comment_node: Node representing a comment
            source: The source code as bytes

        Returns:
            Node that the comment is associated with, or None if standalone
        """
        # If it's a docstring, associate with its parent
        if comment_node.node.type == "string":
            parent = comment_node.node.parent
            if parent:
                # Associate with the appropriate containing node
                if parent.type == "expression_statement":
                    # Check if this is a module docstring
                    if parent.parent and parent.parent.type == "module":
                        return CodeNode(
                            node=parent.parent, byte_start=parent.parent.start_byte, byte_end=parent.parent.end_byte
                        )

                    # Check if this is a class docstring
                    if (
                        parent.parent
                        and parent.parent.type == "block"
                        and parent.parent.parent
                        and parent.parent.parent.type == "class_definition"
                    ):
                        class_node = parent.parent.parent
                        return CodeNode(node=class_node, byte_start=class_node.start_byte, byte_end=class_node.end_byte)

                    # Check if this is a function docstring
                    if (
                        parent.parent
                        and parent.parent.type == "block"
                        and parent.parent.parent
                        and parent.parent.parent.type == "function_definition"
                    ):
                        function_node = parent.parent.parent
                        return CodeNode(
                            node=function_node, byte_start=function_node.start_byte, byte_end=function_node.end_byte
                        )

            return None

        # For regular comments, find what they're associated with
        parent = comment_node.node.parent
        if parent:
            # Case 1: Comment inside a function block - associate with function
            if parent.type == "block" and parent.parent and parent.parent.type == "function_definition":
                function_node = parent.parent
                return CodeNode(
                    node=function_node, byte_start=function_node.start_byte, byte_end=function_node.end_byte
                )

            # Case 2: Comment inside a class block but not in a method - associate with class
            if parent.type == "block" and parent.parent and parent.parent.type == "class_definition":
                class_node = parent.parent
                return CodeNode(node=class_node, byte_start=class_node.start_byte, byte_end=class_node.end_byte)

            # Case 3: Look for next node after comment (traditional approach)
            next_node = self._find_next_node(comment_node.node)
            if next_node:
                # Check the node type to see what it's likely documenting
                if next_node.type == "class_definition":
                    return CodeNode(node=next_node, byte_start=next_node.start_byte, byte_end=next_node.end_byte)
                elif next_node.type == "function_definition":
                    return CodeNode(node=next_node, byte_start=next_node.start_byte, byte_end=next_node.end_byte)
                elif next_node.type == "expression_statement":
                    for child in next_node.children:
                        if child.type == "assignment":
                            return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
                elif next_node.type == "decorator":
                    return CodeNode(node=next_node, byte_start=next_node.start_byte, byte_end=next_node.end_byte)
                elif next_node.type == "return_statement":
                    return CodeNode(node=next_node, byte_start=next_node.start_byte, byte_end=next_node.end_byte)

        return None

    @override
    def section_lookup_key(self, associated_node: CodeNode[Node]) -> tuple[CodeSectionType, str] | None:
        """
        Provide a deterministic ref-based lookup key for comment association.

        This avoids needing the comment builder fallback path to infer parent context
        (e.g., async methods wrapped in decorated_definition nodes).
        """
        n = associated_node.node

        # Class docstrings
        if n.type == "class_definition":
            captures = self.CLASS_NAME_QUERY.captures(n)
            if "name" in captures and captures["name"]:
                class_name = _decode_node_text(captures["name"][0])

                # Detect enum classes so we map to the same section type as the enum adapter.
                # This avoids ref mismatches for e.g. `class AccessLevelType(Enum): ...`
                is_enum = False
                for ch in n.children:
                    if ch.type == "argument_list" and ch.text:
                        bases_text = _decode_node_text(ch)
                        if "Enum" in bases_text:
                            is_enum = True
                            break
                if is_enum:
                    return CodeSectionType.enum, class_name
                return CodeSectionType.class_, class_name
            return None

        # Function / method docstrings (tree-sitter-python represents both sync and async as function_definition)
        if n.type == "function_definition":
            captures = self.FUNCTION_NAME_QUERY.captures(n)
            if "name" not in captures or not captures["name"]:
                return None
            fn_name = _decode_node_text(captures["name"][0])

            # Walk ancestors to see if this function is inside a class
            cur = n.parent
            while cur is not None:
                if cur.type == "function_definition":
                    # Nested function: treat as non-method for lookup purposes
                    break
                if cur.type == "class_definition":
                    cls_caps = self.CLASS_NAME_QUERY.captures(cur)
                    if "name" in cls_caps and cls_caps["name"]:
                        cls_name = _decode_node_text(cls_caps["name"][0])
                        return CodeSectionType.function, f"{cls_name}.{fn_name}"
                    break
                cur = cur.parent
            return CodeSectionType.function, fn_name

        # Assignment comments (module/class attributes)
        if n.type == "assignment":
            captures = self.ASSIGNMENT_LEFT_QUERY.captures(n)
            if "name" in captures and captures["name"]:
                return CodeSectionType.attribute, _decode_node_text(captures["name"][0])

        return None

    def _find_next_node(self, node: Node) -> Node | None:
        """
        Find the next sibling node after the given node.

        Args:
            node: The node to find the sibling for

        Returns:
            The next sibling node, or None if not found
        """
        if not node.parent:
            return None

        siblings = node.parent.children
        for i, sibling in enumerate(siblings):
            if sibling.id == node.id and i + 1 < len(siblings):
                return siblings[i + 1]

        return None

    def get_comment_target_info(self, comment_node: CodeNode[Node]) -> tuple[PythonCommentTargetType, str | None]:
        """
        Get information about what a Python comment is targeting.

        Args:
            comment_node: Node representing a comment

        Returns:
            Tuple of (target_type, target_name)
            - target_type: Type of entity (class, function, etc.)
            - target_name: Name of the entity if available
        """
        associated_node = self.get_associated_node(comment_node, b"")
        if not associated_node:
            return PythonCommentTargetType.UNKNOWN, None

        if associated_node.node.type == "class_definition":
            # Find the class name
            captures = self.CLASS_NAME_QUERY.captures(associated_node.node)
            if "name" in captures and captures["name"]:
                name_node = captures["name"][0]
                return PythonCommentTargetType.CLASS, _decode_node_text(name_node)
            return PythonCommentTargetType.CLASS, None

        elif associated_node.node.type == "function_definition":
            # Find the function name
            captures = self.FUNCTION_NAME_QUERY.captures(associated_node.node)
            if "name" in captures and captures["name"]:
                name_node = captures["name"][0]
                return PythonCommentTargetType.FUNCTION, _decode_node_text(name_node)
            return PythonCommentTargetType.FUNCTION, None

        elif associated_node.node.type == "assignment":
            # Find the assignment target
            captures = self.ASSIGNMENT_LEFT_QUERY.captures(associated_node.node)
            if "name" in captures and captures["name"]:
                name_node = captures["name"][0]
                return PythonCommentTargetType.ATTRIBUTE, _decode_node_text(name_node)
            return PythonCommentTargetType.ATTRIBUTE, None

        elif associated_node.node.type == "decorator":
            return PythonCommentTargetType.DECORATOR, None

        return PythonCommentTargetType.UNKNOWN, None

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a unique identifier for the Python comment.

        For docstrings, use the qualified name of the entity.
        For regular comments, use position-based identifier.

        Args:
            node: The comment node to get the identifier for
            parent: Optional parent name to prepend

        Returns:
            Unique identifier for this comment
        """
        # If we have a parent, construct a prefix
        prefix = f"{parent}:" if parent else ""

        # For docstrings, use the entity qualified name
        if node.node.type == "string":
            associated = self.get_associated_node(node, b"")
            if associated:
                target_type, target_name = self.get_comment_target_info(node)
                if target_name:
                    return f"{prefix}{target_type.value}:{target_name}:docstring"

        # For regular comments, use position-based identifier
        return f"{prefix}comment@{node.byte_start}"

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized comment content for hashing.

        This strips comment delimiters and normalizes whitespace.

        Args:
            node: The comment node to get content for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        import re

        if node.node.type == "comment":
            # Extract comment text
            content = source[node.byte_start:node.byte_end]

            # Strip Python comment marker and leading whitespace
            content = re.sub(b"^\\s*#\\s*", b"", content)

        elif node.node.type == "string":
            # Extract string content
            content = source[node.byte_start:node.byte_end]

            # Strip string delimiters (both single and triple quotes)
            if content.startswith(b'"""') and content.endswith(b'"""'):
                content = content[3:-3]
            elif content.startswith(b"'''") and content.endswith(b"'''"):
                content = content[3:-3]
            elif content.startswith(b'"') and content.endswith(b'"'):
                content = content[1:-1]
            elif content.startswith(b"'") and content.endswith(b"'"):
                content = content[1:-1]
        else:
            # Fallback to raw content
            content = source[node.byte_start:node.byte_end]

        # Normalize whitespace
        normalized = re.sub(b"\\s+", b" ", content)

        # Remove trailing/leading whitespace
        normalized = normalized.strip()

        return normalized
