from __future__ import annotations

from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_meta.fqn_resolver import FqnScope

from aware_code.language_service.position import Utf16PositionMapper

from ..contracts import AwareDiagnostic
from .contracts import TypeMirrorSuggestFn


def collect_mirror_target_diagnostics(
    *,
    code: Code,
    mapper: Utf16PositionMapper,
    scope: FqnScope,
    quickfix_candidates: list[str],
    suggest: TypeMirrorSuggestFn,
) -> list[AwareDiagnostic]:
    diagnostics: list[AwareDiagnostic] = []

    for section in code.code_sections:
        if section.type != CodeSectionType.mirror:
            continue
        mirror = section.code_section_mirror
        if mirror is None:
            continue
        segment = mirror.target_segment
        if segment.byte_start is None or segment.byte_end is None:
            continue
        if segment.byte_end <= segment.byte_start:
            continue

        target = (mirror.target_text or "").strip()
        if not target:
            continue

        if scope.try_resolve_enum(target) is not None:
            continue
        if scope.try_resolve_class_with_fqn(target) is not None:
            continue

        start = mapper.byte_offset_to_position(segment.byte_start)
        end = mapper.byte_offset_to_position(segment.byte_end)
        diagnostics.append(
            {
                "message": f"Mirror target not found: {target}",
                "severity": 1,
                "source": "aware",
                "code": "aware.mirror.target_not_found",
                "range": {
                    "start": {"line": start.line, "character": start.character},
                    "end": {"line": end.line, "character": end.character},
                },
                "data": {
                    "targetText": target,
                    "suggestions": suggest(target, quickfix_candidates),
                },
            }
        )

    return diagnostics
