from __future__ import annotations

from aware_meta.graph.config.annotation.compiler import parse_reference_args

from .contracts import (
    AnnotationAddDiagnostic,
    AnnotationSuggestFn,
    AnnotationVerbInput,
    ResolveClassFn,
)
from .helpers import first_arg_or_verb_range


def collect_reference_annotation_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    resolve_class: ResolveClassFn,
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    if not ann_input.members:
        add(
            rng=ann_input.path.range,
            message=f"Reference annotation must use 'TypeRef::attribute' (got: {ann_input.path.text})",
            code="aware.annotation.path_invalid",
        )
        return
    if len(ann_input.members) != 1:
        add(
            rng=ann_input.path.range,
            message=f"Reference annotation must use 'TypeRef::attribute' (got: {ann_input.path.text})",
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
    attr_names = [attribute.name for attribute in cls.code_section_attributes if attribute.is_public]
    if attr_tok.text not in attr_names:
        add(
            rng=attr_tok.range,
            message=f"Attribute {attr_tok.text!r} not found on class {class_cfg.name}",
            code="aware.annotation.member_not_found",
            data={"suggestions": suggest(attr_tok.text, attr_names)},
        )
        return

    try:
        mode, bind_target_path = parse_reference_args(list(ann_input.args))
    except ValueError as exc:
        data: dict[str, list[str]] | None = None
        if ann_input.args_tokens:
            data = {"suggestions": suggest(ann_input.args_tokens[0].text, ["port", "bind"])}
        add(
            rng=first_arg_or_verb_range(ann_input=ann_input),
            message=str(exc),
            code="aware.annotation.args_invalid",
            data=data,
        )
        return

    if str(mode.value).lower() != "bind":
        return

    target_token = ann_input.args_tokens[1] if len(ann_input.args_tokens) >= 2 else None
    target_range = target_token.range if target_token is not None else ann_input.verb_token.range
    target_path = (bind_target_path or "").strip()
    if not target_path or "::" not in target_path:
        add(
            rng=target_range,
            message=(
                "reference bind annotation target must use 'TypeRef::attribute' "
                f"(got: {bind_target_path})"
            ),
            code="aware.annotation.args_invalid",
        )
        return

    target_type_ref, target_attr = [part.strip() for part in target_path.split("::", 1)]
    if not target_type_ref or not target_attr:
        add(
            rng=target_range,
            message=(
                "reference bind annotation target must use 'TypeRef::attribute' "
                f"(got: {bind_target_path})"
            ),
            code="aware.annotation.args_invalid",
        )
        return

    resolved_target = resolve_class(target_type_ref)
    if resolved_target is None:
        add(
            rng=target_range,
            message=f"Class not found for reference bind target: {target_type_ref}",
            code="aware.annotation.class_not_found",
            data={"suggestions": suggest(target_type_ref, list(ann_input.class_candidates))},
        )
        return

    _target_fqn, target_cfg = resolved_target
    target_cls = target_cfg.code_section_class
    if target_cls is None:
        return

    target_attr_names = [attribute.name for attribute in target_cls.code_section_attributes if attribute.is_public]
    if target_attr not in target_attr_names:
        add(
            rng=target_range,
            message=f"Attribute {target_attr!r} not found on class {target_cfg.name}",
            code="aware.annotation.member_not_found",
            data={"suggestions": suggest(target_attr, target_attr_names)},
        )
