from __future__ import annotations

from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.enum.enum_option import EnumOption

from aware_meta.reserved_keyword_policy import ReservedKeywordEntityPolicy, ReservedKeywordPolicies

from aware_utils.string_transform import to_camel_case, to_snake_case


_DART_RESERVED_IDENTIFIERS: frozenset[str] = frozenset(
    {
        # Keywords / built-in identifiers (keep lower-case; enum/field names are camelCase)
        "abstract",
        "as",
        "assert",
        "async",
        "await",
        "base",
        "break",
        "case",
        "catch",
        "class",
        "const",
        "continue",
        "covariant",
        "default",
        "deferred",
        "do",
        "else",
        "enum",
        "export",
        "extends",
        "extension",
        "external",
        "factory",
        "false",
        "final",
        "finally",
        "for",
        "get",
        "hide",
        "if",
        "implements",
        "import",
        "in",
        "interface",
        "is",
        "late",
        "library",
        "mixin",
        "new",
        "null",
        "on",
        "operator",
        "part",
        "required",
        "rethrow",
        "return",
        "sealed",
        "set",
        "show",
        "static",
        "super",
        "switch",
        "sync",
        "this",
        "throw",
        "true",
        "try",
        "typedef",
        "var",
        "void",
        "while",
        "with",
        "yield",
        # Built-in types commonly used as identifiers in source enums
        "bool",
        "double",
        "dynamic",
        "int",
        "num",
    }
)

# Enum *value* names become static members on the enum type; Dart forbids declaring a member that
# conflicts with inherited members on `Enum`/`Object` (e.g. `Enum.index`).
#
# Keep this list narrowly scoped to enum options to avoid renaming common attribute names.
_DART_RESERVED_ENUM_OPTION_IDENTIFIERS: frozenset[str] = frozenset(
    {*_DART_RESERVED_IDENTIFIERS, "index", "name", "values"}
)


def _dart_enum_option_rendered_name(opt: EnumOption) -> str:
    return to_camel_case(opt.value)


def _dart_enum_option_wire_name(_opt: EnumOption, rendered_name: str) -> str | None:
    return to_snake_case(rendered_name)


def _dart_attribute_rendered_name(attr: AttributeConfig) -> str:
    return to_camel_case(attr.name)


def _dart_attribute_wire_name(_attr: AttributeConfig, rendered_name: str) -> str | None:
    return to_snake_case(rendered_name)


DART_RESERVED_KEYWORD_POLICIES: ReservedKeywordPolicies = {
    CodeSectionAnnotationOverlayEntity.enum_option: ReservedKeywordEntityPolicy(
        reserved_identifiers=_DART_RESERVED_ENUM_OPTION_IDENTIFIERS,
        default_rendered_name=_dart_enum_option_rendered_name,
        default_wire_name=_dart_enum_option_wire_name,
    ),
    CodeSectionAnnotationOverlayEntity.attribute: ReservedKeywordEntityPolicy(
        reserved_identifiers=_DART_RESERVED_IDENTIFIERS,
        default_rendered_name=_dart_attribute_rendered_name,
        default_wire_name=_dart_attribute_wire_name,
    ),
}

# Public read-only alias for renderer/module consumers.
DART_RESERVED_IDENTIFIERS: frozenset[str] = _DART_RESERVED_IDENTIFIERS
