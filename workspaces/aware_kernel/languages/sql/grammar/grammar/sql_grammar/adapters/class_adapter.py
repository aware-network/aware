"""SQL implementation of the CodeSectionClassAdapter."""

from collections.abc import Iterable
import re

# Tree-sitter
from tree_sitter import Node, Query
from typing_extensions import override

# Aware Primitive Code
from aware_code.node.node import CodeNode
from aware_code.section.class_.adapter import CodeSectionClassAdapter

from sql_grammar._tree_sitter_sql import SQL_LANGUAGE


# Logging
from aware_utils.logging import logger


class SQLClassAdapter(CodeSectionClassAdapter[Node]):
    """
    Implementation of CodeSectionClassAdapter for SQL using Tree-sitter.

    Extracts table definitions as class equivalents from SQL parse trees.
    """

    TABLE_QUERY: Query = SQL_LANGUAGE.query(
        """
        (create_table) @table
    """
    )

    TABLE_NAME_QUERY: Query = SQL_LANGUAGE.query(
        """
        (create_table
          (object_reference
            (identifier) @schema_name
            .
            (identifier) @table_name))
        """
    )

    COLUMN_QUERY: Query = SQL_LANGUAGE.query(
        """
        (create_table
          (column_definitions
            (column_definition) @column))
    """
    )

    COMMENT_QUERY: Query = SQL_LANGUAGE.query(
        """
        (comment_statement
          (keyword_comment)
          (keyword_on)
          (keyword_table)
          (object_reference) @table
          (keyword_is)
          (literal) @comment_text)
    """
    )

    @override
    def get_methods(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Tables don't have methods directly - could be implemented
        to return related functions/procedures in the future.

        Args:
            class_node: Node representing a CREATE TABLE statement

        Returns:
            Empty iterable for now
        """
        return []

    @override
    def qualname(self, node: CodeNode[Node], parent: str | None = None) -> str:
        """
        Return the fully qualified name for a SQL table.

        For SQL tables, this is schema.table_name

        Args:
            class_node: The class node to get the qualified name for
            parent: Optional parent name (unused for SQL tables)

        Returns:
            Qualified name string
        """
        # Get table name
        name_node = self.get_name(node)
        name = name_node.node_text()

        # Try to get schema name
        schema = "public"  # Default schema
        captures = self.TABLE_NAME_QUERY.captures(node.node)
        if "schema_name" in captures and captures["schema_name"]:
            schema_node = captures["schema_name"][0]
            schema_text = schema_node.text
            if schema_text is not None:
                schema = schema_text.decode("utf-8")

        # If we got raw bytes for name, decode it
        if isinstance(name, bytes):
            name = name.decode("utf-8")

        return f"{schema}.{name}"

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for a SQL table definition.

        This strips comments and normalizes whitespace.

        Args:
            node: The class node to get body bytes for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        # Extract the node's bytes
        node_bytes = source[node.byte_start:node.byte_end]

        # Remove SQL comments and normalize whitespace
        normalized = re.sub(
            b"--.*?$|/\\*.*?\\*/",  # Remove single-line and multi-line comments
            b"",  # Replace with empty string
            node_bytes,  # Input
            flags=re.MULTILINE | re.DOTALL,  # Multi-line mode
        )

        # Normalize whitespace
        normalized = re.sub(b"\\s+", b" ", normalized)

        # Remove trailing/leading whitespace
        normalized = normalized.strip()

        return normalized

    @override
    def reference_string(self, node: CodeNode[Node], parent: str | None = None) -> str | None:
        """Return a language-specific reference like 'public.permission' or None."""
        return self.get_schema_table_name(node)

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all CREATE TABLE statements in the SQL.

        Args:
            root: The root node of the parse tree
            source: The SQL source code as bytes

        Returns:
            Iterable of nodes representing table definitions
        """
        # Use pre-compiled query
        captures = self.TABLE_QUERY.captures(root)
        if "table" in captures:
            for table_node in captures["table"]:
                yield CodeNode(node=table_node, byte_start=table_node.start_byte, byte_end=table_node.end_byte)

    @override
    def get_name(self, class_node: CodeNode[Node]) -> CodeNode[Node]:
        """
        Extract the table name (without schema) from a CREATE TABLE statement.

        Args:
            class_node: Node representing a CREATE TABLE statement

        Returns:
            Node representing just the table name (without schema)
        """
        # First try with the specific query that separates schema and table name
        captures = self.TABLE_NAME_QUERY.captures(class_node.node)
        if "table_name" in captures and captures["table_name"]:
            name_node = captures["table_name"][0]
            return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)
        captures = self.TABLE_QUERY.captures(class_node.node)
        if "table" in captures and captures["table"]:
            table_node = captures["table"][0]
            return CodeNode(node=table_node, byte_start=table_node.start_byte, byte_end=table_node.end_byte)

        raise ValueError("No table name found in CREATE TABLE statement")

    def get_schema_name(self, class_node: CodeNode[Node]) -> str:
        """
        Get the schema name from a CREATE TABLE statement.

        Args:
            class_node: Node representing a CREATE TABLE statement

        Returns:
            The schema name, or "public" as default
        """
        schema = "public"  # Default schema
        captures = self.TABLE_NAME_QUERY.captures(class_node.node)
        if "schema_name" in captures and captures["schema_name"]:
            schema_node = captures["schema_name"][0]
            schema_text = schema_node.text
            if schema_text is not None:
                schema = schema_text.decode("utf-8")
        return schema

    def get_schema_table_name(self, class_node: CodeNode[Node]) -> str:
        """
        Helper method to extract the full table name including schema.

        Args:
            class_node: Node representing a CREATE TABLE statement

        Returns:
            Full table name as string
        """
        # Try to get schema name
        schema = self.get_schema_name(class_node)
        name = self.get_table_name(class_node)

        return f"{schema}.{name}"

    def get_table_name(self, class_node: CodeNode[Node]) -> str:
        name_node = self.get_name(class_node)
        return name_node.node_text()

    @override
    def get_attributes(self, class_node: CodeNode[Node]) -> Iterable[CodeNode[Node]]:
        """
        Extract column definitions as attributes.

        Args:
            class_node: Node representing a CREATE TABLE statement

        Returns:
            Iterable of nodes representing column definitions
        """
        # Use pre-compiled query
        captures = self.COLUMN_QUERY.captures(class_node.node)
        yielded: set[tuple[int, int]] = set()
        found_nodes: list[CodeNode[Node]] = []
        # Primary path: query-based capture
        if "column" in captures:
            for column_node in captures["column"]:
                span = (column_node.start_byte, column_node.end_byte)
                yielded.add(span)
                found_nodes.append(
                    CodeNode(node=column_node, byte_start=column_node.start_byte, byte_end=column_node.end_byte)
                )

        # Fallback path: enumerate children under column_definitions to catch edge cases
        # where the query misses nodes due to intermediate wrappers or constraints.
        try:

            def walk(n: Node) -> Iterable[CodeNode[Node]]:
                added_local = 0
                for ch in n.children:
                    if ch.type == "column_definition":
                        span = (ch.start_byte, ch.end_byte)
                        if span not in yielded:
                            yielded.add(span)
                            added_local += 1
                            yield CodeNode(node=ch, byte_start=ch.start_byte, byte_end=ch.end_byte)
                    # Recurse
                    yield from walk(ch)
                # Track added count on this branch
                if added_local:
                    try:
                        tbl = self.get_schema_table_name(class_node)
                    except Exception:
                        tbl = "<unknown>"
                    logger.info(
                        f"SQLClassAdapter DIAG: discovered {added_local} extra column_definition nodes under {tbl}",
                    )

            # Walk entire subtree of this create_table
            for extra in walk(class_node.node):
                found_nodes.append(extra)
        except Exception:
            # Do not fail attribute discovery on fallback issues
            pass

        # Emit results and perform post-diagnostics if we likely missed columns
        # 1) Yield discovered nodes
        for n in found_nodes:
            yield n

        # 2) Post-diagnostics: compare names discovered via AST vs names heuristically from text
        try:
            # Extract names from AST (first identifier child under column_definition)
            ast_names: set[str] = set()
            for n in found_nodes:
                try:
                    for ch in n.node.children:
                        if ch.type == "identifier":
                            ast_names.add(ch.text.decode("utf-8", errors="ignore") if ch.text else "")
                            break
                except Exception:
                    continue

            # Heuristic parse from raw text for potential column names at top-level
            raw = class_node.node_text().encode("utf-8", errors="ignore")
            # Find the parenthesized section after first '('
            start = raw.find(b"(")
            end = raw.rfind(b")")
            text_names: set[str] = set()
            if start != -1 and end != -1 and end > start:
                body = raw[start + 1:end]
                body_text = body.decode("utf-8", errors="ignore")
                # Split by commas at depth 0 respecting parentheses
                parts: list[str] = []
                depth = 0
                cur: list[str] = []
                for ch in body_text:
                    if ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth = max(0, depth - 1)
                    if ch == "," and depth == 0:
                        parts.append("".join(cur).strip())
                        cur = []
                    else:
                        cur.append(ch)
                if cur:
                    parts.append("".join(cur).strip())

                # Extract name as first token before whitespace for lines that look like column defs
                for p in parts:
                    if not p:
                        continue
                    # Skip likely table-level constraints
                    low = p.strip().lower()
                    if low.startswith("constraint ") or low.startswith("primary key") or low.startswith("unique "):
                        continue
                    # First token
                    token = p.split()[0]
                    # Be conservative: must start with letter or underscore
                    if token and (token[0].isalpha() or token[0] == "_"):
                        text_names.add(token)

            if text_names and (missing := sorted(text_names - ast_names)):
                try:
                    tbl = self.get_schema_table_name(class_node)
                except Exception:
                    tbl = "<unknown>"
                logger.debug(
                    "SQLClassAdapter: AST found "
                    + f"{len(ast_names)} columns but text suggests {len(text_names)}. "
                    + f"Missing (heuristic): {', '.join(missing)} for {tbl}",
                )
        except Exception:
            pass
