from __future__ import annotations

import keyword

from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.enum.enum_option import EnumOption

from aware_meta.reserved_keyword_policy import ReservedKeywordEntityPolicy, ReservedKeywordPolicies


_PYTHON_RESERVED_IDENTIFIERS: frozenset[str] = frozenset(keyword.kwlist)
# Avoid Enum member names that collide with Enum attribute accessors.
_PYTHON_RESERVED_ENUM_OPTION_IDENTIFIERS: frozenset[str] = _PYTHON_RESERVED_IDENTIFIERS | frozenset(
    {"name", "value"}
)


def _python_attribute_rendered_name(attr: AttributeConfig) -> str:
    return attr.name


def _python_attribute_wire_name(attr: AttributeConfig, _rendered_name: str) -> str | None:
    return attr.name


def _python_enum_option_rendered_name(opt: EnumOption) -> str:
    return opt.label or opt.value


def _python_enum_option_wire_name(opt: EnumOption, _rendered_name: str) -> str | None:
    return opt.value


PYTHON_RESERVED_KEYWORD_POLICIES: ReservedKeywordPolicies = {
    CodeSectionAnnotationOverlayEntity.attribute: ReservedKeywordEntityPolicy(
        reserved_identifiers=_PYTHON_RESERVED_IDENTIFIERS,
        default_rendered_name=_python_attribute_rendered_name,
        default_wire_name=_python_attribute_wire_name,
    ),
    CodeSectionAnnotationOverlayEntity.enum_option: ReservedKeywordEntityPolicy(
        reserved_identifiers=_PYTHON_RESERVED_ENUM_OPTION_IDENTIFIERS,
        default_rendered_name=_python_enum_option_rendered_name,
        default_wire_name=_python_enum_option_wire_name,
    ),
}
