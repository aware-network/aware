from __future__ import annotations

from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_meta.fqn_resolver import FqnScope

from aware_code.language_service.position import Utf16PositionMapper

from ..contracts import AwareDiagnostic


def collect_augment_base_diagnostics(
    *,
    code: Code,
    mapper: Utf16PositionMapper,
    scope: FqnScope,
) -> list[AwareDiagnostic]:
    diagnostics: list[AwareDiagnostic] = []

    for section in code.code_sections:
        if section.type != CodeSectionType.class_:
            continue
        cls = section.code_section_class
        if cls is None:
            continue
        for base in cls.code_section_class_bases:
            if not base.is_augment:
                continue
            segment = base.segment
            if segment is None or segment.byte_start is None or segment.byte_end is None:
                continue
            if segment.byte_end <= segment.byte_start:
                continue
            if scope.try_resolve_class_with_fqn(base.base_ref) is not None:
                continue

            start = mapper.byte_offset_to_position(segment.byte_start)
            end = mapper.byte_offset_to_position(segment.byte_end)
            diagnostics.append(
                {
                    "message": f"Class {base.base_ref} not found (augment base)",
                    "severity": 1,
                    "source": "aware",
                    "range": {
                        "start": {"line": start.line, "character": start.character},
                        "end": {"line": end.line, "character": end.character},
                    },
                }
            )

    return diagnostics
