from __future__ import annotations

from aware_meta.graph.config.annotation.compiler import parse_discriminate_args

from .contracts import (
    AnnotationAddDiagnostic,
    AnnotationSuggestFn,
    AnnotationVerbInput,
    ResolveClassFn,
)
from .helpers import first_arg_or_verb_range


def collect_discriminate_annotation_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    resolve_class: ResolveClassFn,
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    if not ann_input.members or len(ann_input.members) != 1:
        add(
            rng=ann_input.path.range,
            message=f"Discriminate annotation must use 'TypeRef::attribute' (got: {ann_input.path.text})",
            code="aware.annotation.path_invalid",
        )
        return

    resolved = resolve_class(ann_input.type_ref.text)
    if resolved is None:
        add(
            rng=ann_input.type_ref.range,
            message=f"Class not found for annotation target: {ann_input.type_ref.text}",
            code="aware.annotation.class_not_found",
            data={"suggestions": suggest(ann_input.type_ref.text, list(ann_input.class_candidates))},
        )
        return

    _fqn, class_cfg = resolved
    cls = class_cfg.code_section_class
    if cls is None:
        return

    attr_tok = ann_input.members[0]
    attr_names = [attribute.name for attribute in cls.code_section_attributes]
    if attr_tok.text not in attr_names:
        add(
            rng=attr_tok.range,
            message=f"Attribute {attr_tok.text!r} not found on class {class_cfg.name}",
            code="aware.annotation.member_not_found",
            data={"suggestions": suggest(attr_tok.text, attr_names)},
        )
        return

    try:
        _ = parse_discriminate_args(list(ann_input.args))
    except ValueError as exc:
        data: dict[str, list[str]] | None = None
        if ann_input.args_tokens:
            data = {"suggestions": suggest(ann_input.args_tokens[0].text, ["key", "tag"])}
        add(
            rng=first_arg_or_verb_range(ann_input=ann_input),
            message=str(exc),
            code="aware.annotation.args_invalid",
            data=data,
        )
