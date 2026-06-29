from dataclasses import dataclass

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorKind

from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info

from aware_utils.string_transform import to_snake_case


@dataclass(frozen=True)
class PostgresDialect:
    """Postgres-first dialect mapping."""

    def quote_ident(self, ident: str) -> str:
        # Conservative: quote only when needed later. For now, avoid quoting for readability.
        return ident

    def table_name(self, cls: ClassConfig) -> str:
        return to_snake_case(cls.name)

    def enum_type_name(self, enum: EnumConfig) -> str:
        return to_snake_case(enum.name)

    def emit_enum(self, type_name: str, values: list[str]) -> str:
        if not values:
            # Empty enum: emit as a comment so this stays stable but doesn't break DDL.
            return f"-- enum {type_name} had no values\n"
        joined = ", ".join([f"'{v}'" for v in sorted(values)])
        return f"CREATE TYPE {type_name} AS ENUM ({joined});\n"

    def type_for_enum(self, enum_type_name: str) -> str:
        return enum_type_name

    def type_for_json(self) -> str:
        return "JSONB"

    def array_of(self, element_type: str) -> str:
        t = (element_type or "").strip()
        if t.endswith("[]"):
            return t
        return f"{t}[]"

    def type_for_attribute(self, attr: AttributeConfig) -> str:
        info = resolve_type_info(attr)
        if info.kind == AttributeTypeDescriptorKind.primitive and info.primitive_config is not None:
            prim = info.primitive_config.primitive_type
            # Map CodePrimitiveBaseType -> Postgres DDL tokens
            bt = prim.base_type
            if bt == CodePrimitiveBaseType.uuid:
                return "UUID"
            if bt == CodePrimitiveBaseType.string:
                return "TEXT"
            if bt == CodePrimitiveBaseType.integer:
                return "INTEGER"
            if bt == CodePrimitiveBaseType.float:
                return "NUMERIC"
            if bt == CodePrimitiveBaseType.boolean:
                return "BOOLEAN"
            if bt == CodePrimitiveBaseType.json:
                return "JSONB"
            if bt == CodePrimitiveBaseType.datetime:
                return "TIMESTAMPTZ"
            if bt == CodePrimitiveBaseType.bytes:
                return "BYTEA"
            # Fallback
            return "TEXT"
        # Runtime IR should not leave CLASS pointers as physical columns.
        return "TEXT"
