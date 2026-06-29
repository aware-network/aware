"""SQL language plugin for the code processing system."""

from pathlib import Path

# Kernel Graph Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.language.plugin import CodeLanguagePlugin
from aware_code.language.schemas import StructuralFilterDecision
from aware_code.tree.tree_sitter_adapter import CodeTreeSitterAdapter
from tree_sitter import Node
from typing_extensions import override

from sql_grammar.primitive_codec import SqlPrimitiveCodec
from sql_grammar.type_descriptor_adapter import SqlTypeDescriptorAdapter
from sql_grammar.type_parser import SqlTypeParser

# SQL Code Section Adapters
from sql_grammar.adapters.attribute_adapter import SQLAttributeAdapter
from sql_grammar.adapters.class_adapter import SQLClassAdapter
from sql_grammar.adapters.comment_adapter import SQLCommentAdapter
from sql_grammar.adapters.enum_adapter import SQLEnumAdapter
from sql_grammar.adapters.enum_value_adapter import SQLEnumValueAdapter
from sql_grammar.adapters.function_adapter import SQLFunctionAdapter

# SQL Metadata
from sql_grammar.metadata.table_metadata import SQLTableMetadata
from sql_grammar.metadata.function_metadata import SQLFunctionMetadata
from sql_grammar.metadata.column_metadata import SQLColumnMetadata
from sql_grammar.materialization_outputs import SQL_MATERIALIZATION_ARTIFACT_OUTPUTS

from sql_grammar._tree_sitter_sql import SQL_LANGUAGE


class SQLCodeLanguagePlugin(CodeLanguagePlugin[Node]):
    """SQL language plugin with structural filtering capabilities."""

    @override
    def is_structural(self, relative_path: str, file_content: str | None = None) -> bool:
        """
        Determine if a SQL file should be considered structural.

        Structural SQL files include:
        - DDL files (CREATE TABLE, ALTER TABLE, etc.)
        - Schema definitions
        - Function/procedure definitions
        - Type definitions
        - Index definitions

        Non-structural SQL files include:
        - DML files (INSERT, UPDATE, DELETE without schema changes)
        - Data migration files (seed data)
        - Query files
        - Test data files
        """
        # Respect kernel-injected structural filter if present
        if self.injected_structural_filter is not None:
            try:
                decision = self.injected_structural_filter(relative_path, file_content)
                if decision == StructuralFilterDecision.STRUCTURAL:
                    return True
                elif decision == StructuralFilterDecision.NON_STRUCTURAL:
                    return False
                # UNKNOWN → fall through to SQL-specific heuristics
            except Exception:
                # Ignore injection errors to avoid blocking discovery
                pass

        path = Path(relative_path)

        # Path-based classifications
        path_str = str(path).lower()

        # Content-based analysis takes precedence if available
        if file_content:
            content_upper = file_content.upper()

            # Structural indicators (DDL)
            structural_patterns = [
                "CREATE TABLE",
                "ALTER TABLE",
                "DROP TABLE",
                "CREATE TYPE",
                "ALTER TYPE",
                "DROP TYPE",
                "CREATE FUNCTION",
                "CREATE OR REPLACE FUNCTION",
                "CREATE PROCEDURE",
                "CREATE OR REPLACE PROCEDURE",
                "CREATE VIEW",
                "CREATE OR REPLACE VIEW",
                "ALTER VIEW",
                "CREATE INDEX",
                "CREATE UNIQUE INDEX",
                "CREATE TRIGGER",
                "CREATE OR REPLACE TRIGGER",
                "CREATE SEQUENCE",
                "CREATE OR REPLACE SEQUENCE",
                "ADD COLUMN",
                "DROP COLUMN",
                "MODIFY COLUMN",
                "ADD CONSTRAINT",
                "DROP CONSTRAINT",
                "FOREIGN KEY",
                "PRIMARY KEY",
                "CREATE SCHEMA",
                "CREATE DATABASE",
            ]

            # Non-structural indicators (DML, queries)
            non_structural_patterns = [
                "INSERT INTO",
                "UPDATE ",
                "DELETE FROM",
                "SELECT ",
                " FROM ",
                " WHERE ",
                "BEGIN TRANSACTION",
                "COMMIT",
                "ROLLBACK",
                "COPY ",
                "BULK INSERT",
                "-- TEST",
                "-- SEED",
                "-- SAMPLE",
            ]

            # Count occurrences
            structural_count = sum(1 for pattern in structural_patterns if pattern in content_upper)
            non_structural_count = sum(1 for pattern in non_structural_patterns if pattern in content_upper)

            # Strong bias towards structural if DDL is present
            if structural_count > 0:
                return True

            # If only DML and no DDL, likely non-structural
            if non_structural_count > 0 and structural_count == 0:
                return False

        # Path-based classifications for unclear content
        # Strong indicators for non-structural files (data-focused)
        if any(
            pattern in path_str
            for pattern in [
                "data/",
                "seed",
                "fixtures/",
                "sample",
                "examples/",
                "query",
                "queries/",
                "report",
                "reports/",
                "backup",
                "dump",
                "/test_",
                "_test.sql",
                "tests/",
            ]
        ):
            return False

        # Strong indicators for structural files
        if any(
            pattern in path_str
            for pattern in [
                "schema",
                "ddl",
                "structure",
                "create",
                "definition",
                "definitions/",
                "type",
                "types/",
                "function",
                "functions/",
                "procedure",
                "procedures/",
                "view",
                "views/",
                "trigger",
                "triggers/",
            ]
        ):
            return True

        # Default: lean towards structural for SQL files
        # Migration files, unclear content, and empty files default to structural
        # since schema files are more critical to track than query files
        return True


# Create the SQL language plugin
_SQL_TYPE_PARSER = SqlTypeParser()
_SQL_PRIMITIVE_CODEC = SqlPrimitiveCodec(parser=_SQL_TYPE_PARSER)
_SQL_TYPE_DESCRIPTOR_ADAPTER = SqlTypeDescriptorAdapter(parser=_SQL_TYPE_PARSER, primitive_codec=_SQL_PRIMITIVE_CODEC)

SQL_CODE_PLUGIN = SQLCodeLanguagePlugin(
    language=CodeLanguage.sql,
    primitive_codec=_SQL_PRIMITIVE_CODEC,
    tree_sitter_adapter=CodeTreeSitterAdapter(language=SQL_LANGUAGE),
    node_adapters={
        CodeSectionType.attribute: SQLAttributeAdapter(),
        CodeSectionType.class_: SQLClassAdapter(),
        CodeSectionType.comment: SQLCommentAdapter(),
        CodeSectionType.enum: SQLEnumAdapter(),
        CodeSectionType.enum_value: SQLEnumValueAdapter(),
        CodeSectionType.function: SQLFunctionAdapter(),
    },
    metadata_adapters={
        CodeSectionType.attribute: SQLColumnMetadata,
        CodeSectionType.class_: SQLTableMetadata,
        CodeSectionType.function: SQLFunctionMetadata,
    },
    extensions=[".sql"],
    comment_prefix="--",  # SQL uses double-dash comments
    type_descriptor_adapter=_SQL_TYPE_DESCRIPTOR_ADAPTER,
    materialization_artifact_outputs=SQL_MATERIALIZATION_ARTIFACT_OUTPUTS,
)
