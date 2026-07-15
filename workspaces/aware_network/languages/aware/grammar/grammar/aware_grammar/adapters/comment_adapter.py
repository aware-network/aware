"""Aware implementation of the CodeSectionCommentAdapter."""

from collections.abc import Iterable
from typing_extensions import override

# Tree-sitter
from tree_sitter import Node, Query
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_code_ontology.comment.code_section_comment_enums import CodeSectionCommentType
from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.node.node import CodeNode
from aware_code.section.comment.adapter import CodeSectionCommentAdapter


class AwareCommentAdapter(CodeSectionCommentAdapter[Node]):
    """
    Implementation of CodeSectionCommentAdapter for Aware using Tree-sitter.

    Handles three comment styles:
    - /// line comment → bound to the next sibling node at same indent level (types, enums)
    - // inline comment → bound to the same line node (attributes)
    - Triple-quoted DOCSTRING blocks (\"\"\" or $$) → bound to parent function
    """

    # Pre-compiled queries for finding comments
    LINE_DOC_QUERY: Query = AWARE_LANGUAGE.query(
        """
        (comment) @c
        """
    )

    BLOCK_DOC_QUERY: Query = AWARE_LANGUAGE.query(
        """
        (literal) @l
        """
    )

    # Query to find function blocks that might contain docstrings
    FUNCTION_BLOCK_QUERY: Query = AWARE_LANGUAGE.query(
        """
        (fn_def
          (block) @block
        )
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all comments in the Aware source code.

        This includes /// comments, inline // comments, and docstring blocks.
        For /// comments, consecutive lines are grouped into single multiline comments.

        Args:
            root: The root node of the parse tree
            source: The Aware source code as bytes

        Returns:
            Iterable of nodes representing comments (grouped for multiline ///)
        """
        # Find line comments
        captures = self.LINE_DOC_QUERY.captures(root)
        processed_starts: set[int] = set()  # Track which nodes we've already processed

        if "c" in captures:
            for comment_node in captures["c"]:
                # Skip if we've already processed this node as part of a group
                if comment_node.start_byte in processed_starts:
                    continue

                text = comment_node.text
                if text and text.startswith(b"///"):
                    # Group consecutive /// comments
                    group_start = comment_node
                    group_end = comment_node
                    processed_starts.add(comment_node.start_byte)

                    # Look for consecutive /// comments
                    current = comment_node
                    while current.next_named_sibling and current.next_named_sibling.type == "comment":
                        next_comment = current.next_named_sibling
                        if next_comment.text and next_comment.text.startswith(b"///"):
                            group_end = next_comment
                            processed_starts.add(next_comment.start_byte)
                            current = next_comment
                        else:
                            break

                    # Create a CodeNode spanning the entire group
                    yield CodeNode(node=group_start, byte_start=group_start.start_byte, byte_end=group_end.end_byte)

                elif text and text.startswith(b"//"):
                    # Single inline comments - don't group these
                    yield CodeNode(
                        node=comment_node, byte_start=comment_node.start_byte, byte_end=comment_node.end_byte
                    )

        # Find docstring blocks (triple quotes or $$ blocks)
        captures = self.BLOCK_DOC_QUERY.captures(root)
        if "l" in captures:
            for string_node in captures["l"]:
                txt = string_node.text
                if txt and (txt.startswith(b'"""') or txt.startswith(b"$$")):
                    yield CodeNode(node=string_node, byte_start=string_node.start_byte, byte_end=string_node.end_byte)

        # Find docstrings inside function blocks by parsing raw content
        import re

        function_captures = self.FUNCTION_BLOCK_QUERY.captures(root)
        if "block" in function_captures:
            for block_node in function_captures["block"]:
                block_text = block_node.text.decode("utf-8", errors="ignore") if block_node.text else None
                if not block_text:
                    continue

                # Look for triple-quoted docstrings at the start of the block
                # Match opening braces, optional whitespace, then triple quotes
                docstring_pattern = r'^\s*{\s*("""[\s\S]*?"""|$$[\s\S]*?$$)'
                match = re.match(docstring_pattern, block_text)

                if match:
                    docstring_content = match.group(1)
                    # Find the start position of the docstring within the block
                    start_offset = block_text.find(docstring_content)
                    if start_offset >= 0:
                        docstring_start = block_node.start_byte + start_offset
                        docstring_end = docstring_start + len(docstring_content.encode("utf-8"))

                        # Create a synthetic CodeNode for the docstring
                        # We'll use the block_node as the underlying node but with custom byte ranges
                        yield CodeNode(node=block_node, byte_start=docstring_start, byte_end=docstring_end)

    @override
    def get_content_segments(self, comment_node: CodeNode[Node], source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Extract comment content as multiple segments for multiline comments.

        For /// comments: yields separate segments for each line with markers stripped
        For // comments: yields single segment with markers stripped
        For docstring blocks: yields single segment with delimiters removed

        Args:
            comment_node: Node representing a comment (may span multiple lines for ///)
            source: The source code as bytes

        Returns:
            Iterable of nodes representing individual content segments
        """
        n = comment_node.node
        raw = n.text
        if raw is None:
            raise ValueError(f"Comment node {n} has no text")

        if n.type == "comment":
            if raw.startswith(b"///"):
                # Handle potentially multiline /// comments
                if comment_node.byte_end > n.end_byte:
                    # This is a grouped multiline comment - process entirely in bytes
                    full_bytes = source[comment_node.byte_start:comment_node.byte_end]
                    lines = full_bytes.split(b"\n")

                    offset = comment_node.byte_start
                    for i, line in enumerate(lines):
                        stripped = line.lstrip()
                        if stripped.startswith(b"///"):
                            # Find position of b"///" inside bytes line
                            content_start_in_line = line.find(b"///") + 3
                            # Skip ASCII spaces/tabs after ///
                            while (
                                content_start_in_line < len(line)
                                and line[content_start_in_line:content_start_in_line + 1] in b" \t"
                            ):
                                content_start_in_line += 1

                            # Calculate actual byte positions
                            content_start_byte = offset + content_start_in_line
                            content_end_byte = offset + len(line)

                            # Only yield if there's actual content after the markers
                            if content_start_byte < content_end_byte:
                                yield CodeNode(node=n, byte_start=content_start_byte, byte_end=content_end_byte)

                        # Move to next line (include newline character)
                        offset += len(line)
                        if i < len(lines) - 1:  # Not the last line
                            offset += 1  # for \n character
                else:
                    # Single line /// comment
                    start = n.start_byte + 3
                    while start < n.end_byte and source[start:start + 1] in b" \t":
                        start += 1
                    if start < n.end_byte:  # Only yield if there's content
                        yield CodeNode(node=n, byte_start=start, byte_end=n.end_byte)

            elif raw.startswith(b"//"):
                # Single inline comment - strip leading markers
                start = n.start_byte + 2
                while start < n.end_byte and source[start:start + 1] in b" \t":
                    start += 1
                if start < n.end_byte:  # Only yield if there's content
                    yield CodeNode(node=n, byte_start=start, byte_end=n.end_byte)

        elif n.type == "literal":
            # Handle docstring blocks - single segment, work in bytes
            if raw.startswith(b'"""') and raw.endswith(b'"""') and len(raw) >= 6:
                yield CodeNode(node=n, byte_start=n.start_byte + 3, byte_end=n.end_byte - 3)
            # Handle $$ delimited strings
            elif raw.startswith(b"$$") and raw.endswith(b"$$") and len(raw) >= 4:
                yield CodeNode(node=n, byte_start=n.start_byte + 2, byte_end=n.end_byte - 2)
            else:
                # Fallback - return the original node
                yield comment_node

        elif n.type == "block" and comment_node.byte_start != n.start_byte:
            # This is a synthetic docstring node extracted from a function block
            # Extract the content from the source using the custom byte ranges
            docstring_bytes = source[comment_node.byte_start:comment_node.byte_end]

            # Handle triple-quoted strings - work in bytes
            if docstring_bytes.startswith(b'"""') and docstring_bytes.endswith(b'"""') and len(docstring_bytes) >= 6:
                # Return content without the """ markers
                content_start = comment_node.byte_start + 3
                content_end = comment_node.byte_end - 3
                yield CodeNode(node=n, byte_start=content_start, byte_end=content_end)
            # Handle $$ delimited strings - work in bytes
            elif docstring_bytes.startswith(b"$$") and docstring_bytes.endswith(b"$$") and len(docstring_bytes) >= 4:
                # Return content without the $$ markers
                content_start = comment_node.byte_start + 2
                content_end = comment_node.byte_end - 2
                yield CodeNode(node=n, byte_start=content_start, byte_end=content_end)
            else:
                # If it doesn't match expected patterns, return the full range
                yield comment_node
        else:
            # Fallback - return the original node
            yield comment_node

    @override
    def get_comment_type(self, comment_node: CodeNode[Node]) -> CodeSectionCommentType:
        """
        Determine the type of Aware comment.

        Args:
            comment_node: Node representing a comment

        Returns:
            The comment type (always DOC for our use case)
        """
        return CodeSectionCommentType.doc

    @override
    def get_associated_node(self, comment_node: CodeNode[Node], source: bytes) -> CodeNode[Node] | None:
        """
        Find the node that this comment is associated with.

        Binding logic:
        - /// comments: bind to the next sibling (types, enums)
        - // inline comments: bind to the same line node (fields)
        - Docstring blocks: bind to parent function if first child

        Args:
            comment_node: Node representing a comment
            source: The source code as bytes

        Returns:
            Node that the comment is associated with, or None if standalone
        """
        n = comment_node.node

        if n.type == "comment":
            text = n.text
            if text is None:
                raise ValueError(f"Comment node {n} has no text")
            if text.startswith(b"///"):
                # /// comments bind to the *next* sibling at same level
                sib = n.next_named_sibling
                while sib and sib.type == "comment":
                    sib = sib.next_named_sibling
                if sib:
                    return CodeNode(node=sib, byte_start=sib.start_byte, byte_end=sib.end_byte)
                return None
            elif text.startswith(b"//"):
                # // inline comments: look for an attr_def on the same line
                # This is trickier - we need to find a node that shares the same line
                return self._find_same_line_node(n, source)
        elif n.type == "block" and comment_node.byte_start != n.start_byte:
            # This is a synthetic docstring node extracted from a function block
            # Associate it with the parent function of the block
            parent = n.parent
            if parent and parent.type == "fn_def":
                return CodeNode(node=parent, byte_start=parent.start_byte, byte_end=parent.end_byte)
        else:
            # Literal block - check if it's a docstring inside a function
            parent = n.parent
            if parent:
                # Check if this literal is the first statement in a function body
                if parent.type == "block":
                    # Check if this block belongs to a function
                    grandparent = parent.parent
                    if grandparent and grandparent.type == "fn_def":
                        # Check if this literal is the first meaningful child of the block
                        first_child = None
                        for child in parent.children:
                            if child.type not in ["block_start", "block_end", "{", "}"]:  # Skip structural tokens
                                first_child = child
                                break

                        if first_child == n:
                            return CodeNode(
                                node=grandparent, byte_start=grandparent.start_byte, byte_end=grandparent.end_byte
                            )

                # Original logic for functions where docstring is direct child
                elif parent.type == "fn_def" and parent.children and parent.children[0] == n:
                    return CodeNode(node=parent, byte_start=parent.start_byte, byte_end=parent.end_byte)

        return None

    def _find_same_line_node(self, comment_node: Node, source: bytes) -> CodeNode[Node] | None:
        """
        Find a node on the same line as the comment (for inline // comments).

        Args:
            comment_node: The comment node
            source: Source bytes

        Returns:
            Node on the same line, or None
        """
        # Get the line of the comment
        comment_line = source[: comment_node.start_byte].count(b"\n")

        # Look at siblings and parent's children to find an attr_def on the same line
        parent = comment_node.parent
        if parent:
            for child in parent.children:
                if child.type == "attr_def":
                    child_line = source[: child.start_byte].count(b"\n")
                    if child_line == comment_line:
                        return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

        return None

    @override
    def section_lookup_key(self, associated_node: CodeNode[Node]) -> tuple[CodeSectionType, str] | None:
        """
        Map node type to CodeSectionType and extract the name.

        Args:
            associated_node: The node that the comment is associated with

        Returns:
            Tuple of (CodeSectionType, name) or None if not mappable
        """
        kind = associated_node.node.type

        if kind in {"class_def", "edge_def"}:
            name = self._child_ident(associated_node.node)
            return (CodeSectionType.class_, name)
        if kind == "fn_def":
            func_name = self._child_ident(associated_node.node)
            # Find the parent type/edge to create qualified name for methods
            parent_name = self._find_parent_type_name(associated_node.node)
            if parent_name:
                qualified_name = f"{parent_name}.{func_name}"
            else:
                qualified_name = func_name
            return (CodeSectionType.function, qualified_name)
        if kind == "attr_def":
            field_name = self._child_ident(associated_node.node)
            # Find the parent type/edge to create qualified name
            parent_name = self._find_parent_type_name(associated_node.node)
            if parent_name:
                qualified_name = f"{parent_name}.{field_name}"
            else:
                qualified_name = field_name
            return (CodeSectionType.attribute, qualified_name)
        if kind == "enum_def":
            name = self._child_ident(associated_node.node)
            return (CodeSectionType.enum, name)
        if kind == "enum_value_def":
            enum_value_name = self._child_ident(associated_node.node)
            parent_enum_name = self._find_parent_enum_name(associated_node.node)
            if parent_enum_name:
                qualified_name = f"{parent_enum_name}.{enum_value_name}"
            else:
                qualified_name = enum_value_name
            return (CodeSectionType.enum_value, qualified_name)
        return None

    def _find_parent_type_name(self, field_node: Node) -> str | None:
        """
        Find the name of the parent class or edge that contains this attribute.

        Args:
            field_node: The field_def node

        Returns:
            The parent type/edge name, or None if not found
        """
        current = field_node.parent
        while current:
            if current.type in {"class_def", "edge_def"}:
                # Extract the name from this class/edge (preserve case)
                for child in current.children:
                    if child.type == "ident":
                        if child.text is None:
                            raise ValueError(f"Child node {child} has no text")
                        return child.text.decode("utf-8")
                break
            current = current.parent
        return None

    def _find_parent_enum_name(self, enum_value_node: Node) -> str | None:
        """
        Find the name of the parent enum that contains this enum value.

        Args:
            enum_value_node: The enum_value_def node

        Returns:
            The parent enum name, or None if not found
        """
        current = enum_value_node.parent
        while current:
            if current.type == "enum_def":
                # Extract the name from this enum (preserve case)
                for child in current.children:
                    if child.type == "ident":
                        return child.text.decode("utf-8") if child.text is not None else ""
                break
            current = current.parent
        return None

    def _child_ident(self, node: Node) -> str:
        """
        Extract the identifier name from a node's children.

        Args:
            node: The node to extract the identifier from

        Returns:
            The identifier name or a fallback based on position
        """
        for child in node.children:
            if child.type == "ident":
                name = child.text.decode("utf-8") if child.text is not None else ""
                return name
        return f"unk@{node.start_byte}"

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a unique identifier for the Aware comment.

        Args:
            node: The comment node to get the identifier for
            parent: Optional parent name to prepend

        Returns:
            Unique identifier for this comment
        """
        prefix = f"{parent}:" if parent else ""
        return f"{prefix}doc@{node.byte_start}"

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized comment content for hashing.

        This strips comment delimiters and normalizes whitespace.
        For multiline /// comments, processes each line individually.

        Args:
            node: The comment node to get content for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        import re
        import textwrap

        # Get content from segments
        content_segments = list(self.get_content_segments(node, source))
        if not content_segments:
            # Fallback to raw content if no segments
            body = source[node.byte_start:node.byte_end]
        else:
            # Combine all segments
            if len(content_segments) == 1:
                # Single segment
                content_node = content_segments[0]
                body = source[content_node.byte_start:content_node.byte_end]
            else:
                # Multiple segments - join them with newlines for multiline comments
                segment_texts: list[str] = []
                for segment in content_segments:
                    segment_text = source[segment.byte_start:segment.byte_end].decode("utf-8")
                    segment_texts.append(segment_text)
                body = "\n".join(segment_texts).encode("utf-8")

        # Handle multiline /// comments specially
        if (
            node.node.type == "comment"
            and node.node.text is not None
            and node.node.text.startswith(b"///")
            and len(content_segments) > 1
        ):
            # This is a grouped multiline /// comment
            # We need to extract each line and strip the /// markers
            full_text = source[node.byte_start:node.byte_end].decode("utf-8")
            lines = full_text.split("\n")

            cleaned_lines: list[str] = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("///"):
                    # Remove /// and any following whitespace
                    content = stripped[3:].lstrip()
                    cleaned_lines.append(content)
                elif stripped.startswith("//"):
                    # Handle case where some lines might be //
                    content = stripped[2:].lstrip()
                    cleaned_lines.append(content)
                else:
                    # Line without comment markers (shouldn't happen but handle gracefully)
                    cleaned_lines.append(stripped)

            # Join lines back together
            body = "\n".join(cleaned_lines).encode()

        # Normalize indentation
        body = textwrap.dedent(body.decode("utf-8")).encode()

        # Normalize whitespace
        body = re.sub(rb"\s+", b" ", body).strip()

        return body

    def get_comment_priority(self, comment_node: CodeNode[Node]) -> int:
        """
        Get the priority of a comment for docstring selection.

        Lower numbers = higher priority.

        Priority order:
        1. Triple-quote docstrings (priority 0)
        2. Dollar-dollar docstrings (priority 1)
        3. Triple-slash comments (priority 2)
        4. Double-slash inline comments (priority 3)

        Args:
            comment_node: Node representing a comment

        Returns:
            Priority value (lower = higher priority)
        """
        n = comment_node.node

        # Triple-quote docstrings (highest priority)
        if n.type == "literal":
            text = n.text.decode("utf-8") if n.text is not None else ""
            if text.startswith('"""'):
                return 0
            elif text.startswith("$$"):
                return 1
        elif n.type == "block" and comment_node.byte_start != n.start_byte:
            # Synthetic docstring from function block - assume it's triple-quote since that's what we extract
            return 0
        elif n.type == "comment":
            text = n.text if n.text is not None else b""
            if text.startswith(b"///"):
                return 2
            elif text.startswith(b"//"):
                return 3

        # Fallback for unknown comment types
        return 99
