"""Determine relationship loading strategies for Dart attributes."""

import re

from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipSideLoadingStrategy,
)
from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute

from aware_content.builder import get_text


_JSONKEY_PATTERN = re.compile(r"@JsonKey\s*\((?P<body>[^)]*)\)", re.IGNORECASE | re.DOTALL)
_INCLUDE_FROM_JSON_FALSE = re.compile(r"includeFromJson\s*:\s*false", re.IGNORECASE)
_INCLUDE_TO_JSON_FALSE = re.compile(r"includeToJson\s*:\s*false", re.IGNORECASE)


def determine_loading_from_attribute(
    attribute: CodeSectionAttribute,
) -> ClassConfigRelationshipSideLoadingStrategy:
    """Return (interface, network) loading strategies for a Dart attribute."""

    # Default behaviour: eager in both contexts
    default = ClassConfigRelationshipSideLoadingStrategy.eager

    segment = attribute.code_section.content_part_text_segment
    # IMPORTANT: We need access to the full file content to look back for @JsonKey annotations.
    # Segment text is only the slice for the attribute declaration, so lookback would be empty.
    full_text = get_text(segment.content_part_text)

    start = segment.byte_start or 0
    lookback_start = max(0, start - 256)
    window = full_text[lookback_start:start]

    matches = list(_JSONKEY_PATTERN.finditer(window))
    if not matches:
        return default

    for match in matches:
        body = match.group("body")
        if body and (_INCLUDE_FROM_JSON_FALSE.search(body) or _INCLUDE_TO_JSON_FALSE.search(body)):
            return ClassConfigRelationshipSideLoadingStrategy.lazy

    return default
