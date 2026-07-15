from __future__ import annotations

from aware_meta.graph.config.annotation.compiler import parse_load_args

from .contracts import (
    AnnotationAddDiagnostic,
    AnnotationSuggestFn,
    AnnotationVerbInput,
    ResolveClassFn,
)
from .helpers import first_arg_or_verb_range


def collect_load_annotation_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    resolve_class: ResolveClassFn,
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    if not ann_input.members:
        add(
            rng=ann_input.path.range,
            message=f"Load annotation must use 'TypeRef::attribute' (got: {ann_input.path.text})",
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
    attr = next(
        (candidate for candidate in cls.code_section_attributes if candidate.name == attr_tok.text),
        None,
    )
    if attr is None:
        add(
            rng=attr_tok.range,
            message=f"Attribute {attr_tok.text!r} not found on class {class_cfg.name}",
            code="aware.annotation.member_not_found",
            data={
                "suggestions": suggest(
                    attr_tok.text,
                    [candidate.name for candidate in cls.code_section_attributes],
                )
            },
        )
        return

    if len(ann_input.members) >= 2:
        edge_tok = ann_input.members[1]
        resolved_edge = resolve_class(edge_tok.text)
        if resolved_edge is None:
            add(
                rng=edge_tok.range,
                message=f"Class not found for edge reference: {edge_tok.text}",
                code="aware.annotation.class_not_found",
                data={"suggestions": suggest(edge_tok.text, list(ann_input.class_candidates))},
            )

    try:
        _ = parse_load_args(list(ann_input.args))
    except ValueError as exc:
        add(
            rng=first_arg_or_verb_range(ann_input=ann_input),
            message=str(exc),
            code="aware.annotation.args_invalid",
        )
