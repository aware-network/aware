"""SQL implementation of the CodeSectionCommentAdapter."""

from enum import Enum
from collections.abc import Iterable

# Tree-sitter
from tree_sitter import Node, Query
from typing_extensions import override

# Kernel Graph Ontology
from aware_code_ontology.comment.code_section_comment_enums import CodeSectionCommentType
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.node.node import CodeNode
from aware_code.section.comment.adapter import CodeSectionCommentAdapter


from sql_grammar._tree_sitter_sql import SQL_LANGUAGE


class SQLCommentTargetType(str, Enum):
    """Type of SQL entity that a comment is associated with."""

    UNKNOWN = "unknown"
    TABLE = "table"
    COLUMN = "column"
    FUNCTION = "function"
    TYPE = "type"
    SCHEMA = "schema"


class SQLCommentAdapter(CodeSectionCommentAdapter[Node]):
    """
    Implementation of CodeSectionCommentAdapter for SQL using Tree-sitter.

    Extracts comments from SQL parse trees.
    """

    # Pre-compiled queries for finding comments
    COMMENT_QUERY: Query = SQL_LANGUAGE.query(
        """
        (comment) @comment
        """
    )

    # Query to find COMMENT ON statements, which are special in SQL
    COMMENT_ON_QUERY: Query = SQL_LANGUAGE.query(
        """
        (comment_statement) @comment_on
        """
    )

    # Queries for specific comment types
    COMMENT_ON_TABLE_QUERY: Query = SQL_LANGUAGE.query(
        """
        (comment_statement
          (keyword_table)
          (object_reference) @table_ref)
        """
    )

    COMMENT_ON_COLUMN_QUERY: Query = SQL_LANGUAGE.query(
        """
        (comment_statement
          (keyword_column)
          (object_reference) @column_ref)
        """
    )

    COMMENT_ON_FUNCTION_QUERY: Query = SQL_LANGUAGE.query(
        """
        (comment_statement
          (keyword_function)
          (object_reference) @function_ref)
        """
    )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all comments in the SQL source code.

        This includes both standard comments (--) and COMMENT ON statements.

        Args:
            root: The root node of the parse tree
            source: The SQL source code as bytes

        Returns:
            Iterable of nodes representing comments
        """
        # Find standard comments
        captures = self.COMMENT_QUERY.captures(root)
        if "comment" in captures:
            for comment_node in captures["comment"]:
                yield CodeNode(node=comment_node, byte_start=comment_node.start_byte, byte_end=comment_node.end_byte)

        # Find COMMENT ON statements
        captures = self.COMMENT_ON_QUERY.captures(root)
        if "comment_on" in captures:
            for comment_on_node in captures["comment_on"]:
                yield CodeNode(
                    node=comment_on_node, byte_start=comment_on_node.start_byte, byte_end=comment_on_node.end_byte
                )

    @override
    def get_content_segments(self, comment_node: CodeNode[Node], source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Extract comment content as segments for SQL comments.

        SQL comments are typically single segments:
        - Standard comments (--): single segment with -- markers stripped
        - COMMENT ON statements: single segment with quotes removed from literal
        - Block comments (/* */): single segment with delimiters removed

        Args:
            comment_node: Node representing a comment
            source: The source code as bytes

        Returns:
            Iterable of nodes representing individual content segments (usually just one)
        """
        if comment_node.node.type == "comment":
            # For standard comments, the content is the entire node
            # In a real implementation, you'd strip the leading '--'
            if comment_node.byte_start < comment_node.byte_end:
                yield comment_node

        elif comment_node.node.type == "comment_statement":
            # For COMMENT ON statements, find the literal content
            for child in comment_node.node.children:
                if child.type == "literal":
                    # Get the text content
                    text = child.text.decode("utf-8") if child.text else ""

                    # Strip enclosing quotes from SQL string literals
                    # Handle both single quotes ('text') and double quotes ("text")
                    if (text.startswith("'") and text.endswith("'")) or (text.startswith('"') and text.endswith('"')):
                        # Create a new CodeNode with adjusted start/end to exclude quotes
                        content_start = child.start_byte + 1  # +1 to skip opening quote
                        content_end = child.end_byte - 1  # -1 to exclude closing quote
                        if content_start < content_end:
                            yield CodeNode(
                                node=child,
                                byte_start=content_start,
                                byte_end=content_end,
                            )
                    else:
                        # No quotes to strip
                        if child.start_byte < child.end_byte:
                            yield CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)
                    break

    @override
    def get_comment_type(self, comment_node: CodeNode[Node]) -> CodeSectionCommentType:
        """
        Determine the type of SQL comment.

        Args:
            comment_node: Node representing a comment

        Returns:
            The comment type
        """
        if comment_node.node.type == "comment_statement":
            return CodeSectionCommentType.doc
        if comment_node.node.type == "comment":
            return CodeSectionCommentType.line
        return CodeSectionCommentType.line

    @override
    def get_associated_node(self, comment_node: CodeNode[Node], source: bytes) -> CodeNode[Node] | None:
        """
        Find the node that this comment is associated with, if any.

        For COMMENT ON statements, this would be the referenced object.
        For standard comments, this looks at nearby definitions.

        Args:
            comment_node: Node representing a comment
            source: The source code as bytes

        Returns:
            Node that the comment is associated with, or None if standalone
        """
        if comment_node.node.type == "comment_statement":
            # For COMMENT ON statements, look for the table, column, or function reference
            for child in comment_node.node.children:
                if child.type == "object_reference":
                    return CodeNode(node=child, byte_start=child.start_byte, byte_end=child.end_byte)

        # For now, return None to indicate no clear association
        return None

    @override
    def section_lookup_key(self, associated_node: CodeNode[Node]) -> tuple[CodeSectionType, str] | None:
        ref = associated_node.node_text()

        # Need to check the parent comment_statement node
        parent_node = associated_node.node.parent
        if not parent_node or parent_node.type != "comment_statement":
            return None

        # Use the pre-compiled queries to determine the comment type
        if self.COMMENT_ON_TABLE_QUERY.captures(parent_node):
            return (CodeSectionType.class_, ref)
        if self.COMMENT_ON_FUNCTION_QUERY.captures(parent_node):
            return (CodeSectionType.function, ref)
        if self.COMMENT_ON_COLUMN_QUERY.captures(parent_node):
            return (CodeSectionType.attribute, ref)

        # Look for type keywords in the comment statement
        for child in parent_node.children:
            if child.type == "keyword_table":
                return (CodeSectionType.class_, ref)
            elif child.type == "keyword_column":
                return (CodeSectionType.attribute, ref)
            elif child.type == "keyword_function":
                return (CodeSectionType.function, ref)

        return None

    def get_comment_target_info(
        self, comment_node: CodeNode[Node]
    ) -> tuple[SQLCommentTargetType, str | None, str | None]:
        """
        Get information about what a SQL comment is targeting.

        Args:
            comment_node: Node representing a comment

        Returns:
            Tuple of (target_type, qualified_name, simple_name)
            - target_type: Type of entity (table, column, function, etc.)
            - qualified_name: Full qualified name (schema.object)
            - simple_name: Just the object name without schema
        """
        if comment_node.node.type != "comment_statement":
            return SQLCommentTargetType.UNKNOWN, None, None

        for query, target_type in (
            (self.COMMENT_ON_TABLE_QUERY, SQLCommentTargetType.TABLE),
            (self.COMMENT_ON_COLUMN_QUERY, SQLCommentTargetType.COLUMN),
            (self.COMMENT_ON_FUNCTION_QUERY, SQLCommentTargetType.FUNCTION),
        ):
            ref_nodes = query.captures(comment_node.node).get("ref", [])
            if ref_nodes:
                ref_text = ref_nodes[0].text
                if ref_text is None:
                    continue
                ref = ref_text.decode("utf-8")
                return target_type, ref, ref.split(".")[-1]
        return SQLCommentTargetType.UNKNOWN, None, None

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return a unique identifier for the SQL comment.

        For COMMENT ON statements, use the object reference.
        For regular comments, use position-based identifier.

        Args:
            node: The comment node to get the identifier for
            parent: Optional parent name to prepend

        Returns:
            Unique identifier for this comment
        """
        # Get the target type and qualified name if available
        _, qualified_name, _ = self.get_comment_target_info(node)
        if qualified_name:
            return f"{qualified_name}__comment__"

        # For regular comments, use position-based fallback
        # Add parent prefix if available
        prefix = f"{parent}:" if parent else ""
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
            # Regular SQL comment
            content = source[node.byte_start:node.byte_end]

            # Strip SQL comment markers
            content = re.sub(b"^\\s*--\\s*|^\\s*/\\*|\\*/\\s*$", b"", content)

        elif node.node.type == "comment_statement":
            # COMMENT ON statement
            # Find the literal/string part
            content_segments = list(self.get_content_segments(node, source))
            if content_segments:
                content_node = content_segments[0]  # Take first segment
                content = source[content_node.byte_start:content_node.byte_end]
            else:
                # Fallback to raw content
                content = source[node.byte_start:node.byte_end]

            # Strip SQL string delimiters if present
            content = re.sub(b"^\\s*'|'\\s*$|^\\s*\"|\"\\s*$", b"", content)
        else:
            # Fallback - just use the raw content
            content = source[node.byte_start:node.byte_end]

        # Normalize whitespace
        normalized = re.sub(b"\\s+", b" ", content)

        # Remove trailing/leading whitespace
        normalized = normalized.strip()

        return normalized
