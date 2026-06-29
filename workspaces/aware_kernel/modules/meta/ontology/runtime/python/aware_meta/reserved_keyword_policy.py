from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, TypeAlias

from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)


ReservedKeywordDefaultRenderedName: TypeAlias = Callable[[Any], str]
ReservedKeywordDefaultWireName: TypeAlias = Callable[[Any, str], str | None]


@dataclass(frozen=True, slots=True)
class ReservedKeywordEntityPolicy:
    """
    Per-entity identifier policy for reserved keyword handling.

    - `default_rendered_name` must match what the language renderer would emit when no overlay exists.
    - `default_wire_name` (when provided) must match the stable serialized name when no overlay exists.
    """

    reserved_identifiers: frozenset[str]
    default_rendered_name: ReservedKeywordDefaultRenderedName
    default_wire_name: ReservedKeywordDefaultWireName | None = None


ReservedKeywordPolicies: TypeAlias = Mapping[CodeSectionAnnotationOverlayEntity, ReservedKeywordEntityPolicy]
