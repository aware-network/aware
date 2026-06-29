"""SectionSpec: explicit writer↔assembler contract (free-function friendly).

This replaces the old "closed" assembler interface with an explicit, typed spec:
- the writer knows the section_type (for identity + storage)
- the caller provides an assemble() function (segments/nested → domain object)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeAlias

from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType

AssembleFn: TypeAlias = Callable[
    [
        CodeSection,
        dict[str, ContentPartTextSegment | list[ContentPartTextSegment]],
        dict[str, CodeSection | list[CodeSection]],
    ],
    object,
]


@dataclass(frozen=True, slots=True)
class SectionSpec:
    section_type: CodeSectionType
    assemble: AssembleFn
