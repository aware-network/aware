from __future__ import annotations

from re import Pattern

from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_meta.fqn_resolver import FqnScope
from aware_meta.attribute.config.type_descriptor_builder import build_type_descriptor

from aware_code.language_service.position import Utf16PositionMapper

from ..contracts import AwareDiagnostic
from .contracts import TypeMirrorPluginContract, TypeMirrorSuggestFn


def collect_attribute_type_diagnostics(
    *,
    code: Code,
    mapper: Utf16PositionMapper,
    plugin: TypeMirrorPluginContract,
    scope: FqnScope,
    class_not_found_rx: Pattern[str],
    optional_list_rx: Pattern[str],
    quickfix_candidates: list[str],
    suggest: TypeMirrorSuggestFn,
) -> list[AwareDiagnostic]:
    diagnostics: list[AwareDiagnostic] = []

    for section in code.code_sections:
        if section.type != CodeSectionType.attribute:
            continue
        attr = section.code_section_attribute
        if attr is None:
            continue
        if attr.type_text is None or attr.type_segment is None:
            continue
        segment = attr.type_segment
        if segment.byte_start is None or segment.byte_end is None:
            continue
        if segment.byte_end <= segment.byte_start:
            continue

        try:
            _ = build_type_descriptor(
                plugin.type_descriptor_adapter,
                plugin.primitive_codec,
                scope,
                attr.type_text,
            )
        except Exception as exc:
            message = str(exc)
            start = mapper.byte_offset_to_position(segment.byte_start)
            end = mapper.byte_offset_to_position(segment.byte_end)
            diagnostic: AwareDiagnostic = {
                "message": message,
                "severity": 1,
                "source": "aware",
                "range": {
                    "start": {"line": start.line, "character": start.character},
                    "end": {"line": end.line, "character": end.character},
                },
            }
            optional_list_match = optional_list_rx.match(message)
            if optional_list_match is not None:
                diagnostic["code"] = "aware.type.optional_list_not_allowed"
                type_text = optional_list_match.group("type_text")
                suggestion = None
                if type_text.endswith("[]?"):
                    suggestion = f"{type_text[:-3]}?[]"
                diagnostic["data"] = {
                    "typeText": type_text,
                    "suggestedTypeText": suggestion,
                }
            else:
                class_not_found_match = class_not_found_rx.match(message)
                if class_not_found_match is not None:
                    diagnostic["code"] = "aware.type.class_not_found"
                    identifier = class_not_found_match.group("identifier")
                    type_text = class_not_found_match.group("type_text")
                    rewritten_suggestions: list[str] = []
                    for candidate in suggest(identifier, quickfix_candidates):
                        rewritten_suggestions.append(
                            rewrite_type_text(
                                type_text=type_text,
                                identifier=identifier,
                                replacement=candidate,
                            )
                        )
                    diagnostic["data"] = {
                        "identifier": identifier,
                        "typeText": type_text,
                        "suggestions": rewritten_suggestions,
                    }
            diagnostics.append(diagnostic)

    return diagnostics


def rewrite_type_text(
    *,
    type_text: str,
    identifier: str,
    replacement: str,
) -> str:
    raw = (type_text or "").strip()
    ident = (identifier or "").strip()
    repl = (replacement or "").strip()
    if not raw or not ident or not repl:
        return repl or raw
    if raw == ident:
        return repl
    if ident in raw:
        return raw.replace(ident, repl, 1)
    return repl
