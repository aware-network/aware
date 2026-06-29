from dataclasses import dataclass

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorKind

from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info

from aware_utils.string_transform import to_snake_case


@dataclass(frozen=True)
class SqliteDialect:
    """SQLite dialect mapping for canonical DDL emission."""

    def quote_ident(self, ident: str) -> str:
        # Conservative: avoid quoting for readability. Overlays handle reserved keywords.
        return ident

    def table_name(self, cls: ClassConfig) -> str:
        return to_snake_case(cls.name)

    def enum_type_name(self, enum: EnumConfig) -> str:
        # Used for stable documentation comments only (SQLite has no CREATE TYPE).
        return to_snake_case(enum.name)

    def emit_enum(self, type_name: str, values: list[str]) -> str:
        if not values:
            return f"-- enum {type_name} had no values\n"
        joined = ", ".join([f"'{v}'" for v in sorted(values)])
        return f"-- enum {type_name}: {joined}\n"

    def type_for_enum(self, enum_type_name: str) -> str:
        _ = enum_type_name
        return "TEXT"

    def type_for_json(self) -> str:
        return "TEXT"

    def array_of(self, element_type: str) -> str:
        _ = element_type
        # SQLite has no array types; store collections as JSON-encoded TEXT.
        return "TEXT"

    def type_for_attribute(self, attr: AttributeConfig) -> str:
        info = resolve_type_info(attr)
        if info.kind == AttributeTypeDescriptorKind.primitive and info.primitive_config is not None:
            prim = info.primitive_config.primitive_type
            bt = prim.base_type
            if bt == CodePrimitiveBaseType.uuid:
                return "TEXT"
            if bt == CodePrimitiveBaseType.string:
                return "TEXT"
            if bt == CodePrimitiveBaseType.integer:
                return "INTEGER"
            if bt == CodePrimitiveBaseType.float:
                return "REAL"
            if bt == CodePrimitiveBaseType.boolean:
                return "INTEGER"
            if bt == CodePrimitiveBaseType.json:
                return "TEXT"
            if bt == CodePrimitiveBaseType.datetime:
                return "TEXT"
            if bt == CodePrimitiveBaseType.bytes:
                return "BLOB"
            return "TEXT"
        # Runtime IR should not leave ENUM/CLASS pointers as physical columns; SQLRenderer
        # handles ENUM separately to preserve overlays, and SQLite stores them as TEXT.
        return "TEXT"


__all__ = ["SqliteDialect"]
