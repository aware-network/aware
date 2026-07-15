"""Determine relationship loading strategies for Python attributes."""

import re

from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipSideLoadingStrategy,
)

from aware_content.builder import get_segment_text

_FIELD_PATTERN = re.compile(r"Field\s*\((?P<body>[^)]*)\)", re.IGNORECASE | re.DOTALL)
_EXCLUDE_TRUE_PATTERN = re.compile(r"exclude\s*=\s*True", re.IGNORECASE)


def determine_loading_from_attribute(
    attribute: CodeSectionAttribute,
) -> ClassConfigRelationshipSideLoadingStrategy:
    """Return loading strategy for a Python attribute."""
    default = ClassConfigRelationshipSideLoadingStrategy.eager
    raw_text = get_segment_text(attribute.code_section.content_part_text_segment)

    if not raw_text:
        return default

    matches = list(_FIELD_PATTERN.finditer(raw_text))
    if not matches:
        return default

    for match in matches:
        body = match.group("body")
        if body and _EXCLUDE_TRUE_PATTERN.search(body):
            return ClassConfigRelationshipSideLoadingStrategy.lazy

    return default
