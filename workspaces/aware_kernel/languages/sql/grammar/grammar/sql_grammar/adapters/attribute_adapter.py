"""SQL implementation of the CodeAttributeSectionAdapter."""

from collections.abc import Iterable

# Tree-sitter
from tree_sitter import Node, Query
from typing_extensions import override

# Aware Primitive Code
from aware_code.node.node import CodeNode
from aware_code.section.attribute.adapter import CodeSectionAttributeAdapter

# Aware SQL
from sql_grammar.primitive_codec import PRIMITIVE_TYPE_NODES

from sql_grammar._tree_sitter_sql import SQL_LANGUAGE

# Logging
from aware_utils.logging import logger


def debug_node(node: Node, src: bytes, depth: int = 0) -> None:
    indent = " " * (2 * depth)
    node_text = node.text.decode("utf-8") if node.text else ""
    logger.info(f"{indent}{node_text:<25}:{node.type}  {src[node.start_byte:node.end_byte]!r}")
    for child in node.children:
        debug_node(child, src, depth + 1)


class SQLAttributeAdapter(CodeSectionAttributeAdapter[Node]):
    """
    Implementation of CodeSectionAttributeAdapter for SQL using Tree-sitter.

    Extracts column definitions and function parameters as attributes from SQL parse trees.
    """

    # Pre-compiled queries for column name and parameter name
    COLUMN_NAME_QUERY: Query = SQL_LANGUAGE.query(
        """
        (column_definition
          (identifier) @column_name)
    """
    )

    # Using function_argument instead of parameter based on actual SQL tree structure
    PARAM_NAME_QUERY: Query = SQL_LANGUAGE.query(
        """
        (function_argument
          (identifier) @param_name)
    """
    )

    # Pre-compiled queries for default values - column version
    COLUMN_DEFAULT_LITERAL_QUERY: Query = SQL_LANGUAGE.query(
        """
        (column_definition
          (keyword_default) @default_kw
          (literal) @default_value)
    """
    )

    COLUMN_DEFAULT_INVOCATION_QUERY: Query = SQL_LANGUAGE.query(
        """
        (column_definition
          (keyword_default) @default_kw
          (invocation) @default_value)
    """
    )

    COLUMN_DEFAULT_KW_QUERY: Query = SQL_LANGUAGE.query(
        """
        (column_definition
          (keyword_default) @default_kw)
    """
    )

    # Fixed parameter default value queries to use function_argument
    PARAM_DEFAULT_LITERAL_QUERY: Query = SQL_LANGUAGE.query(
        """
        (function_argument
          (keyword_default) @default_kw
          (literal) @default_value)
    """
    )

    # Column NOT NULL constraint query
    COLUMN_NOT_NULL_QUERY: Query = SQL_LANGUAGE.query(
        """
        (column_definition
          (identifier) @col_name
          (keyword_not)
          (keyword_null))
        """
    )

    UNIQUE_QUERY: Query = SQL_LANGUAGE.query(
        """
        (column_definition
          (keyword_unique)) @unique
    """
    )

    PRIMARY_KEY_QUERY: Query = SQL_LANGUAGE.query(
        """
        (column_definition
          (keyword_primary)) @primary_key
    """
    )

    # Query for extracting foreign keys from a single column
    FOREIGN_KEY_QUERY: Query = SQL_LANGUAGE.query(
        """
        (column_definition
          (identifier) @col_name
          ._
          (keyword_references)
          (object_reference) @fk_table
          [(
            (identifier) @fk_ref_col
           )
           ;
           ((
             (identifier) @fk_ref_col
           ))
          ]?)
        """
    )

    @override
    def get_name(self, attribute_node: CodeNode[Node], is_parameter: bool) -> CodeNode[Node]:
        """
        Extract the name from a column definition or parameter.

        Args:
            attribute_node: Node representing a column or parameter
            is_parameter: Flag indicating if this is a parameter (vs column)

        Returns:
            Node representing the attribute name
        """
        # Use pre-compiled queries
        query = self.PARAM_NAME_QUERY if is_parameter else self.COLUMN_NAME_QUERY
        captures = query.captures(attribute_node.node)

        capture_name = "param_name" if is_parameter else "column_name"
        if capture_name in captures and captures[capture_name]:
            name_node = captures[capture_name][0]
            return CodeNode(node=name_node, byte_start=name_node.start_byte, byte_end=name_node.end_byte)
        node_kind = "parameter" if is_parameter else "column"
        raise ValueError(
            f"Could not find name in {node_kind} node: {attribute_node.node.type}. "
            + f"Attribute node: {attribute_node.node_text()}"
        )

    @override
    def match_nodes(self, root: Node, source: bytes) -> Iterable[CodeNode[Node]]:
        """
        Find all top-level attributes in SQL.

        For SQL, standalone attributes might be sequences, variables, etc.
        Most attributes in SQL are columns within tables or parameters within functions,
        which are discovered through their parent containers.

        Args:
            root: The root node of the parse tree
            source: The SQL source code as bytes

        Returns:
            Iterable of nodes representing top-level attributes
        """
        # For most SQL dialects, there aren't many top-level attributes
        # Sequences might be considered top-level attributes
        sequence_query = SQL_LANGUAGE.query(
            """
            (create_sequence) @sequence
            """
        )

        captures = sequence_query.captures(root)
        if "sequence" in captures:
            for seq_node in captures["sequence"]:
                yield CodeNode(node=seq_node, byte_start=seq_node.start_byte, byte_end=seq_node.end_byte)

    @override
    def get_type(self, attribute_node: CodeNode[Node], is_parameter: bool) -> CodeNode[Node]:
        """
        Extract the type from a column definition or parameter.

        Args:
            attribute_node: Node representing a column or parameter
            is_parameter: Flag indicating if this is a parameter (vs column)

        Returns:
            Node representing the attribute type
        """
        # Get the name node first
        name_node = self.get_name(attribute_node, is_parameter)

        # Find type node position
        type_start = -1
        type_end = -1

        # Examine each child to find the type and any potential array suffix
        found_name = False
        type_node = None
        for child in attribute_node.node.children:
            # Skip to children after the name node
            if not found_name:
                if child.start_byte == name_node.node.start_byte:
                    found_name = True
                continue

            # Check if this child is a type node
            if child.type in PRIMITIVE_TYPE_NODES:
                type_node = child
                type_start = child.start_byte
                type_end = child.end_byte

                # In case of vector attribute, we need to include the dimension information
                if child.type == "vector" and not is_parameter:
                    # The vector node should have children for the parentheses and dimension
                    if len(child.children) >= 3:  # vector, (, dimension, )
                        # Last child should be the closing parenthesis
                        type_end = child.children[-1].end_byte
                    # Fallback: look for siblings that might contain the dimension info
                    else:
                        for i, sibling in enumerate(attribute_node.node.children):
                            if sibling.start_byte > child.end_byte and sibling.text == b"(":
                                # Find closing parenthesis
                                for j, closing in enumerate(attribute_node.node.children[i + 1:]):
                                    if closing.text == b")":
                                        type_end = closing.end_byte
                                        break
                                break

                # Look ahead for array suffix after type
                for sibling in attribute_node.node.children:
                    if sibling.start_byte > child.end_byte and sibling.type == "array_size_definition":
                        type_end = sibling.end_byte  # Extend type to include array
                        break
                    # Skip if we find a keyword_default - it's the end of the type
                    if sibling.start_byte > child.end_byte and sibling.type in ("keyword_default", "keyword_check"):
                        break
                if type_start >= 0:
                    break

            # Some types are nested (e.g., timestamp with time zone or int under keyword_int)
            if child.type in ["timestamp", "int", "float"]:
                type_node = child
                type_start = child.start_byte
                type_end = child.end_byte

                # Look for multi-word types like "timestamp with time zone"
                for i, sibling in enumerate(attribute_node.node.children):
                    if sibling.start_byte == child.start_byte:
                        # Check if we have more keywords after this one that form a unit
                        next_siblings = attribute_node.node.children[i + 1:i + 5]  # Check next few siblings
                        for j, next_sib in enumerate(next_siblings):
                            if next_sib.type.startswith("keyword_"):
                                type_end = next_sib.end_byte
                            # Stop if we hit something that doesn't look like part of a type
                            elif not next_sib.type.startswith("keyword_") and j > 0:
                                break

                # Look ahead for array suffix after type
                for sibling in attribute_node.node.children:
                    if sibling.start_byte > type_end and sibling.type == "array_size_definition":
                        type_end = sibling.end_byte  # Extend type to include array
                        break
                    if sibling.start_byte > type_end and sibling.type == "keyword_check":
                        break
                if type_start >= 0:
                    break

        if type_start >= 0 and type_end >= type_start:
            # Robustly include PostgreSQL array suffix "[]" even when not exposed as a dedicated node
            attr_abs_start = attribute_node.node.start_byte
            full = attribute_node.node.text  # bytes for entire column/param definition
            if full:
                local_pos = max(0, type_end - attr_abs_start)
                # Skip whitespace between base type and any trailing []
                while local_pos < len(full) and full[local_pos:local_pos + 1] in (b" ", b"\t", b"\n", b"\r"):
                    local_pos += 1
                # Accumulate contiguous [] segments (e.g., type[][])
                extended = 0
                while local_pos + 1 < len(full) and full[local_pos:local_pos + 2] == b"[]":
                    extended += 2
                    local_pos += 2
                    # Skip any whitespace between repeated []
                    while local_pos < len(full) and full[local_pos:local_pos + 1] in (b" ", b"\t", b"\n", b"\r"):
                        local_pos += 1
                if extended:
                    type_end += extended

            # Build node covering the full type span (base + array suffix if present)
            if type_node:
                return CodeNode(node=type_node, byte_start=type_start, byte_end=type_end)
            else:
                raise Exception(f"Could not find type node for {name_node.node_text()} on: {attribute_node.node.type}")

        # If everything fails, raise an exception
        debug_node(attribute_node.node, attribute_node.node_text().encode("utf-8"))
        raise Exception(f"Could not find type for {name_node.node_text()} on: {attribute_node.node.type}")

    @override
    def get_default_value(self, attribute_node: CodeNode[Node], is_parameter: bool) -> CodeNode[Node] | None:
        """
        Extract the default value from a column definition or parameter if present.

        Args:
            attribute_node: Node representing a column or parameter
            is_parameter: Flag indicating if this is a parameter (vs column)

        Returns:
            Node representing the default value if present, None otherwise
        """
        # Use pre-compiled queries based on parameter flag
        if is_parameter:
            # For function parameters
            try:
                # First check for literal defaults (most common)
                captures = self.PARAM_DEFAULT_LITERAL_QUERY.captures(attribute_node.node)
                if "default_value" in captures and captures["default_value"]:
                    default_node = captures["default_value"][0]
                    return CodeNode(
                        node=default_node, byte_start=default_node.start_byte, byte_end=default_node.end_byte
                    )
            except Exception as e:
                logger.error(f"Parameter default query failed: {e}")
                # Continue to fallback mechanism
        else:
            # For column definitions
            try:
                # First check for literal defaults
                captures = self.COLUMN_DEFAULT_LITERAL_QUERY.captures(attribute_node.node)
                if "default_value" in captures and captures["default_value"]:
                    default_node = captures["default_value"][0]
                    return CodeNode(
                        node=default_node, byte_start=default_node.start_byte, byte_end=default_node.end_byte
                    )

                # Then check for function call defaults
                captures = self.COLUMN_DEFAULT_INVOCATION_QUERY.captures(attribute_node.node)
                if "default_value" in captures and captures["default_value"]:
                    default_node = captures["default_value"][0]
                    return CodeNode(
                        node=default_node, byte_start=default_node.start_byte, byte_end=default_node.end_byte
                    )
            except Exception as e:
                logger.error(f"Column default query failed: {e}")
                # Continue to fallback mechanism

        # Fallback approach - find DEFAULT keyword and get the next non-default node
        default_pos = None
        for i, child in enumerate(attribute_node.node.children):
            if child.type == "keyword_default":
                default_pos = i
                break

        if default_pos is not None and default_pos + 1 < len(attribute_node.node.children):
            logger.debug(
                "Found DEFAULT keyword at position "
                + f"{default_pos} with text {attribute_node.node.children[default_pos + 1].text}"
            )
            # Get the node after DEFAULT
            default_value_node = attribute_node.node.children[default_pos + 1]
            return CodeNode(
                node=default_value_node, byte_start=default_value_node.start_byte, byte_end=default_value_node.end_byte
            )

        return None

    @override
    def qualname_for_role(self, node: CodeNode[Node], is_parameter: bool, parent: str | None = None) -> str:
        """
        Return a fully-qualified name for a SQL column or parameter.

        For columns: table.column_name
        For parameters: function_name.param_name

        Args:
            node: The attribute node to get the qualified name for
            is_parameter: Whether the node is a parameter (vs column)
            parent: Optional parent name (table/function name)

        Returns:
            Qualified name string
        """
        # Get the attribute name
        name_node = self.get_name(node, is_parameter=is_parameter)
        name = name_node.node_text()

        # Combine with parent if available
        if parent:
            return f"{parent}.{name}"

        # Fallback - just use name or a position-based identifier if empty
        return name if name else f"attr@{node.byte_start}"

    @override
    def body_bytes(self, node: CodeNode[Node], source: bytes) -> bytes:
        """
        Return normalized body bytes for a SQL column or parameter.

        This normalizes the definition to ensure consistent hashing
        regardless of whitespace or comment differences.

        Args:
            node: The attribute node to get bytes for
            source: Source code bytes

        Returns:
            Normalized bytes for hashing
        """
        import re

        # Extract the node's bytes
        node_bytes = source[node.byte_start:node.byte_end]

        # Remove SQL comments
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
    def reference_string_for_role(
        self,
        node: CodeNode[Node],
        is_parameter: bool,
        parent: str | None = None,
    ) -> str | None:
        """
        Return a reference string for a SQL column or parameter.
        """
        # Reuse qualname method
        return self.qualname_for_role(node, is_parameter, parent)

    @override
    def has_unique(self, attribute_node: CodeNode[Node], is_parameter: bool) -> bool:
        """
        Check if an attribute has a unique constraint.

        For SQL columns, this checks for UNIQUE or PRIMARY KEY constraints.
        Parameters are never unique by default.

        Args:
            attribute_node: Node representing a column or parameter
            is_parameter: Flag indicating if this is a parameter (vs column)

        Returns:
            True if the attribute has a unique constraint, False otherwise
        """
        if is_parameter:
            # Parameters are never unique by default
            return False

        try:
            # Check for UNIQUE constraint
            unique_captures = self.UNIQUE_QUERY.captures(attribute_node.node)
            has_unique = "unique" in unique_captures and len(unique_captures["unique"]) > 0

            # Check for PRIMARY KEY constraint
            is_primary = self.is_primary(attribute_node, is_parameter=False)

            return has_unique or is_primary
        except Exception as e:
            logger.error(f"Error checking unique constraints: {e}")
            return False

    @override
    def is_primary(self, attribute_node: CodeNode[Node], is_parameter: bool) -> bool:
        """
        Check if an attribute is a primary key.
        """
        if is_parameter:
            return False
        try:
            captures = self.PRIMARY_KEY_QUERY.captures(attribute_node.node)
            return bool(captures.get("primary_key"))
        except Exception as e:
            logger.error(f"Error checking primary key constraint: {e}")
            return False

    @override
    def is_required(self, attribute_node: CodeNode[Node], is_parameter: bool) -> bool:
        """
        Check if an attribute is required (not nullable).

        For SQL columns, this checks for NOT NULL constraint.
        For parameters, this checks if there's no default value.

        Args:
            attribute_node: Node representing a column or parameter
            is_parameter: Flag indicating if this is a parameter (vs column)

        Returns:
            True if the attribute is required, False otherwise
        """
        if is_parameter:
            # For parameters, check if there's no default value
            return self.get_default_value(attribute_node, is_parameter=True) is None

        # For columns, check for NOT NULL constraint
        try:
            captures = self.COLUMN_NOT_NULL_QUERY.captures(attribute_node.node)
            return "col_name" in captures and len(captures["col_name"]) > 0
        except Exception as e:
            logger.error(f"Error checking NOT NULL constraint: {e}")
            return False

    def get_foreign_key_target(self, attribute_node: CodeNode[Node]) -> dict[str, str] | None:
        """
        Extract foreign key information from a column definition.

        If this column_definition contains "REFERENCES schema.table(col)",
        return a dictionary with target_schema, target_table, target_column.

        Args:
            attribute_node: Node representing a column definition

        Returns:
            Dictionary with foreign key information or None if no foreign key
        """
        try:
            captures = self.FOREIGN_KEY_QUERY.captures(attribute_node.node)

            # Check if we have a foreign key reference
            if "fk_table" not in captures or not captures["fk_table"]:
                return None

            # Get target table reference (schema.table)
            table_node_text = captures["fk_table"][0].text
            if table_node_text is None:
                return None
            table_ref = table_node_text.decode("utf-8")
            parts = table_ref.split(".")

            if len(parts) == 2:
                schema_name, table_name = parts
            else:
                schema_name = "public"  # Default schema
                table_name = parts[0]

            # Get target column
            target_column = "id"  # Default to id if not specified
            if "fk_ref_col" in captures and captures["fk_ref_col"]:
                ref_col_node = captures["fk_ref_col"][0]
                ref_col_text = ref_col_node.text
                if ref_col_text is not None:
                    target_column = ref_col_text.decode("utf-8")

            return {
                "target_schema": schema_name,
                "target_table": table_name,
                "target_column": target_column,
            }

        except Exception as e:
            logger.error(f"Error extracting foreign key: {e}")
            return None
