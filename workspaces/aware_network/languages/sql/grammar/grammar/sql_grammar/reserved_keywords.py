from __future__ import annotations

from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig

from aware_meta.reserved_keyword_policy import ReservedKeywordEntityPolicy, ReservedKeywordPolicies

from aware_utils.string_transform import to_snake_case


# Minimal, Postgres-first keyword set for identifiers.
# Keep this conservative to avoid unexpected schema churn; expand as needed.
_SQL_RESERVED_IDENTIFIERS: frozenset[str] = frozenset(
    {
        "select",
        "from",
        "where",
        "group",
        "order",
        "having",
        "join",
        "union",
        "limit",
        "offset",
        "insert",
        "update",
        "delete",
        "create",
        "alter",
        "drop",
        "table",
        "type",
        "enum",
        "primary",
        "foreign",
        "references",
        "constraint",
        "and",
        "or",
        "not",
        "null",
        "true",
        "false",
        # Postgres: WINDOW clause / window functions.
        "window",
        # SQLite/SQL: TRANSACTION keyword (breaks unquoted CREATE TABLE transaction).
        "transaction",
    }
)


def _sql_class_rendered_name(cls: ClassConfig) -> str:
    # Matches current PostgresDialect.table_name behavior.
    return to_snake_case(cls.name)


def _sql_enum_rendered_name(enum: EnumConfig) -> str:
    # Matches current PostgresDialect.enum_type_name behavior.
    return to_snake_case(enum.name)


def _sql_attribute_rendered_name(attr: AttributeConfig) -> str:
    # Matches current SQLRenderer column naming (no transform).
    return attr.name


def _sql_attribute_wire_name(attr: AttributeConfig, _rendered_name: str) -> str | None:
    return attr.name


SQL_RESERVED_KEYWORD_POLICIES: ReservedKeywordPolicies = {
    CodeSectionAnnotationOverlayEntity.class_: ReservedKeywordEntityPolicy(
        reserved_identifiers=_SQL_RESERVED_IDENTIFIERS,
        default_rendered_name=_sql_class_rendered_name,
    ),
    CodeSectionAnnotationOverlayEntity.enum: ReservedKeywordEntityPolicy(
        reserved_identifiers=_SQL_RESERVED_IDENTIFIERS,
        default_rendered_name=_sql_enum_rendered_name,
    ),
    CodeSectionAnnotationOverlayEntity.attribute: ReservedKeywordEntityPolicy(
        reserved_identifiers=_SQL_RESERVED_IDENTIFIERS,
        default_rendered_name=_sql_attribute_rendered_name,
        default_wire_name=_sql_attribute_wire_name,
    ),
}
