from __future__ import annotations

from aware_meta.graph.config.annotation.compiler import (
    parse_override_fk_args,
    parse_override_relationship_args,
)

from .contracts import (
    AnnotationAddDiagnostic,
    AnnotationSuggestFn,
    AnnotationVerbInput,
    ResolveClassFn,
)
from .helpers import first_arg_or_verb_range


def collect_override_annotation_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    resolve_class: ResolveClassFn,
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    if not ann_input.members:
        add(
            rng=ann_input.path.range,
            message=f"Override annotation must use 'TypeRef::attribute' (got: {ann_input.path.text})",
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

    kind_token = (ann_input.args[0] if ann_input.args else "").strip().lower()
    if kind_token not in {"fk", "relationship"}:
        add(
            rng=first_arg_or_verb_range(ann_input=ann_input),
            message="Override annotation must specify kind 'fk' or 'relationship' as first arg",
            code="aware.annotation.args_invalid",
            data={"suggestions": suggest(kind_token, ["fk", "relationship"])},
        )
        return

    try:
        if kind_token == "fk":
            _ = parse_override_fk_args(list(ann_input.args[1:]))
        else:
            _ = parse_override_relationship_args(list(ann_input.args[1:]))
    except ValueError as exc:
        add(
            rng=first_arg_or_verb_range(ann_input=ann_input),
            message=str(exc),
            code="aware.annotation.args_invalid",
        )
