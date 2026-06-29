from __future__ import annotations

from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_meta.fqn_resolver import FqnResolver, FqnScope

from aware_code.language_service.position import ByteRange
from aware_code.language_service.text import (
    parse_annotation_statement_tokens,
    split_double_colon_parts,
)

from .contracts import (
    AnnotationAddDiagnostic,
    AnnotationSuggestFn,
    AnnotationVerbInput,
)
from .discriminate import collect_discriminate_annotation_diagnostics
from .identity import collect_identity_annotation_diagnostics
from .load import collect_load_annotation_diagnostics
from .oneof import collect_oneof_annotation_diagnostics
from .overlay import collect_overlay_annotation_diagnostics
from .override import collect_override_annotation_diagnostics
from .project import collect_project_annotation_diagnostics
from .reference import collect_reference_annotation_diagnostics

_ANNOTATION_VERBS: tuple[str, ...] = (
    "load",
    "project",
    "overlay",
    "override",
    "discriminate",
    "identity",
    "oneof",
    "reference",
)


def collect_annotation_diagnostics(
    *,
    code: Code,
    document_bytes: bytes,
    resolver: FqnResolver,
    scope: FqnScope,
    class_candidates: list[str],
    enum_candidates: list[str],
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    doc_bytes = document_bytes
    class_suggestion_candidates = tuple(class_candidates)
    enum_suggestion_candidates = tuple(enum_candidates)

    def _resolve_class(token: str):
        return scope.try_resolve_class_with_fqn(token)

    def _resolve_enum(token: str):
        return scope.try_resolve_enum_with_fqn(token)

    for section in code.code_sections:
        if section.type != CodeSectionType.annotation:
            continue
        annotation = section.code_section_annotation
        segment = section.content_part_text_segment
        if annotation is None:
            continue
        if segment.byte_start is None:
            continue

        line_start = doc_bytes.rfind(b"\n", 0, segment.byte_start)
        line_start = 0 if line_start == -1 else line_start + 1
        line_end = doc_bytes.find(b"\n", segment.byte_start)
        if line_end == -1:
            line_end = len(doc_bytes)

        statement = parse_annotation_statement_tokens(
            document_bytes=doc_bytes,
            segment_start=line_start,
            segment_end=line_end,
        )
        if statement is None:
            continue

        if statement.path is None:
            add(
                rng=ByteRange(start=line_start, end=line_end),
                message="Annotation missing path (expected: ann <path> <verb> ...)",
                code="aware.annotation.missing_path",
            )
            continue

        if statement.verb is None:
            add(
                rng=statement.path.range,
                message="Annotation missing verb (expected: ann <path> <verb> ...)",
                code="aware.annotation.missing_verb",
            )
            continue

        verb_raw = statement.verb.text
        verb = verb_raw.strip().lower()
        if verb not in _ANNOTATION_VERBS:
            add(
                rng=statement.verb.range,
                message=f"Unknown annotation verb: {verb_raw!r}",
                code="aware.annotation.unknown_verb",
                data={"suggestions": suggest(verb_raw, list(_ANNOTATION_VERBS))},
            )
            continue

        path_bytes = doc_bytes[statement.path.range.start:statement.path.range.end]
        parts = split_double_colon_parts(
            token_bytes=path_bytes,
            token_range=statement.path.range,
        )
        if not parts:
            add(
                rng=statement.path.range,
                message=f"Invalid annotation path: {statement.path.text!r}",
                code="aware.annotation.path_invalid",
            )
            continue

        ann_input = AnnotationVerbInput(
            path=statement.path,
            verb_token=statement.verb,
            args_tokens=statement.args,
            type_ref=parts[0],
            members=tuple(parts[1:]),
            args=tuple(token.text for token in statement.args),
            class_candidates=class_suggestion_candidates,
            enum_candidates=enum_suggestion_candidates,
        )

        if verb == "load":
            collect_load_annotation_diagnostics(
                ann_input=ann_input,
                resolve_class=_resolve_class,
                add=add,
                suggest=suggest,
            )
            continue
        if verb == "project":
            collect_project_annotation_diagnostics(
                ann_input=ann_input,
                add=add,
            )
            continue
        if verb == "discriminate":
            collect_discriminate_annotation_diagnostics(
                ann_input=ann_input,
                resolve_class=_resolve_class,
                add=add,
                suggest=suggest,
            )
            continue
        if verb == "identity":
            collect_identity_annotation_diagnostics(
                ann_input=ann_input,
                resolve_class=_resolve_class,
                resolver=resolver,
                workspace_language=code.language,
                add=add,
                suggest=suggest,
            )
            continue
        if verb == "oneof":
            collect_oneof_annotation_diagnostics(
                ann_input=ann_input,
                resolve_class=_resolve_class,
                add=add,
                suggest=suggest,
            )
            continue
        if verb == "reference":
            collect_reference_annotation_diagnostics(
                ann_input=ann_input,
                resolve_class=_resolve_class,
                add=add,
                suggest=suggest,
            )
            continue
        if verb == "overlay":
            collect_overlay_annotation_diagnostics(
                ann_input=ann_input,
                resolve_class=_resolve_class,
                resolve_enum=_resolve_enum,
                add=add,
                suggest=suggest,
            )
            continue
        if verb == "override":
            collect_override_annotation_diagnostics(
                ann_input=ann_input,
                resolve_class=_resolve_class,
                add=add,
                suggest=suggest,
            )
