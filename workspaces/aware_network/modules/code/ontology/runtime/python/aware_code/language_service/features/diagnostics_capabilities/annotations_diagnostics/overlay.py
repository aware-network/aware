from __future__ import annotations

from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta.graph.config.annotation.compiler import parse_overlay_args
from aware_code_ontology.class_.code_section_class import CodeSectionClass

from .contracts import (
    AnnotationAddDiagnostic,
    AnnotationSuggestFn,
    AnnotationVerbInput,
    ResolveClassFn,
    ResolveEnumFn,
)
from .helpers import first_arg_or_verb_range


def collect_overlay_annotation_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    resolve_class: ResolveClassFn,
    resolve_enum: ResolveEnumFn,
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    try:
        entity, _language, _rename, _wire_name = parse_overlay_args(list(ann_input.args))
    except ValueError as exc:
        add(
            rng=first_arg_or_verb_range(ann_input=ann_input),
            message=str(exc),
            code="aware.annotation.args_invalid",
        )
        return

    if entity is None:
        add(
            rng=first_arg_or_verb_range(ann_input=ann_input),
            message="Overlay annotation must specify 'entity' and 'language'",
            code="aware.annotation.args_invalid",
        )
        return

    if entity == CodeSectionAnnotationOverlayEntity.class_:
        _collect_overlay_class_diagnostics(
            ann_input=ann_input,
            resolve_class=resolve_class,
            add=add,
            suggest=suggest,
        )
        return

    if entity == CodeSectionAnnotationOverlayEntity.enum:
        _collect_overlay_enum_diagnostics(
            ann_input=ann_input,
            resolve_enum=resolve_enum,
            add=add,
            suggest=suggest,
        )
        return

    if entity == CodeSectionAnnotationOverlayEntity.enum_option:
        _collect_overlay_enum_option_diagnostics(
            ann_input=ann_input,
            resolve_enum=resolve_enum,
            add=add,
            suggest=suggest,
        )
        return

    resolved_src = resolve_class(ann_input.type_ref.text)
    if resolved_src is None:
        add(
            rng=ann_input.type_ref.range,
            message=f"Class not found for annotation target: {ann_input.type_ref.text}",
            code="aware.annotation.class_not_found",
            data={"suggestions": suggest(ann_input.type_ref.text, list(ann_input.class_candidates))},
        )
        return

    _src_fqn, src_cfg = resolved_src
    src_cls = src_cfg.code_section_class
    if src_cls is None:
        return

    if entity == CodeSectionAnnotationOverlayEntity.function:
        _collect_overlay_function_diagnostics(
            ann_input=ann_input,
            src_class_name=src_cfg.name,
            src_functions=[function.name for function in src_cls.code_section_functions],
            add=add,
            suggest=suggest,
        )
        return

    if entity == CodeSectionAnnotationOverlayEntity.attribute:
        _collect_overlay_attribute_diagnostics(
            ann_input=ann_input,
            src_cfg_name=src_cfg.name,
            src_cls=src_cls,
            resolve_class=resolve_class,
            add=add,
            suggest=suggest,
        )
        return


def _collect_overlay_class_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    resolve_class: ResolveClassFn,
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    if ann_input.members:
        add(
            rng=ann_input.path.range,
            message=f"Overlay class path must be 'TypeRef' (got: {ann_input.path.text})",
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


def _collect_overlay_enum_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    resolve_enum: ResolveEnumFn,
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    if ann_input.members:
        add(
            rng=ann_input.path.range,
            message=f"Overlay enum path must be 'TypeRef' (got: {ann_input.path.text})",
            code="aware.annotation.path_invalid",
        )
        return
    resolved = resolve_enum(ann_input.type_ref.text)
    if resolved is None:
        add(
            rng=ann_input.type_ref.range,
            message=f"Enum not found for annotation target: {ann_input.type_ref.text}",
            code="aware.annotation.enum_not_found",
            data={"suggestions": suggest(ann_input.type_ref.text, list(ann_input.enum_candidates))},
        )


def _collect_overlay_enum_option_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    resolve_enum: ResolveEnumFn,
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    if not ann_input.members:
        add(
            rng=ann_input.path.range,
            message=f"Overlay enum option path must be 'TypeRef::enum_option' (got: {ann_input.path.text})",
            code="aware.annotation.path_invalid",
        )
        return
    resolved = resolve_enum(ann_input.type_ref.text)
    if resolved is None:
        add(
            rng=ann_input.type_ref.range,
            message=f"Enum not found for annotation target: {ann_input.type_ref.text}",
            code="aware.annotation.enum_not_found",
            data={"suggestions": suggest(ann_input.type_ref.text, list(ann_input.enum_candidates))},
        )
        return
    _enum_fqn, enum_cfg = resolved
    enum = enum_cfg.code_section_enum
    if enum is None:
        return
    option_token = ann_input.members[0]
    options = [value.value for value in enum.code_section_enum_values if value.value]
    if option_token.text not in options:
        add(
            rng=option_token.range,
            message=f"Enum option {option_token.text!r} not found on enum {enum_cfg.name}",
            code="aware.annotation.member_not_found",
            data={"suggestions": suggest(option_token.text, options)},
        )


def _collect_overlay_function_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    src_class_name: str,
    src_functions: list[str],
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    if not ann_input.members:
        add(
            rng=ann_input.path.range,
            message=f"Overlay function path must be 'TypeRef::function' (got: {ann_input.path.text})",
            code="aware.annotation.path_invalid",
        )
        return
    function_token = ann_input.members[0]
    if function_token.text not in src_functions:
        add(
            rng=function_token.range,
            message=f"Function {function_token.text!r} not found on class {src_class_name}",
            code="aware.annotation.member_not_found",
            data={"suggestions": suggest(function_token.text, src_functions)},
        )


def _collect_overlay_attribute_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    src_cfg_name: str,
    src_cls: CodeSectionClass,
    resolve_class: ResolveClassFn,
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    members = ann_input.members
    if not members:
        add(
            rng=ann_input.path.range,
            message=(
                "Overlay attribute path must be one of: "
                "'TypeRef::attribute', 'TypeRef::function::attribute', "
                "'TypeRef::relationship_attr::EdgeName::edge_member', "
                "'TypeRef::relationship_attr::EdgeName::edge_fn::edge_fn_attr'"
            ),
            code="aware.annotation.path_invalid",
        )
        return

    if len(members) == 1:
        attr_token = members[0]
        names = [attribute.name for attribute in src_cls.code_section_attributes]
        if attr_token.text not in names:
            add(
                rng=attr_token.range,
                message=f"Attribute {attr_token.text!r} not found on class {src_cfg_name}",
                code="aware.annotation.member_not_found",
                data={"suggestions": suggest(attr_token.text, names)},
            )
        return

    if len(members) == 2:
        fn_token, attr_token = members[0], members[1]
        function = next(
            (candidate for candidate in src_cls.code_section_functions if candidate.name == fn_token.text),
            None,
        )
        if function is None:
            add(
                rng=fn_token.range,
                message=f"Function {fn_token.text!r} not found on class {src_cfg_name}",
                code="aware.annotation.member_not_found",
                data={
                    "suggestions": suggest(
                        fn_token.text,
                        [candidate.name for candidate in src_cls.code_section_functions],
                    )
                },
            )
            return
        function_attr_names = [attribute.name for attribute in function.code_section_attributes]
        if attr_token.text not in function_attr_names:
            add(
                rng=attr_token.range,
                message=f"Attribute {attr_token.text!r} not found on function {fn_token.text!r}",
                code="aware.annotation.member_not_found",
                data={"suggestions": suggest(attr_token.text, function_attr_names)},
            )
        return

    if len(members) == 3:
        _collect_overlay_attribute_edge_diagnostics(
            ann_input=ann_input,
            src_cfg_name=src_cfg_name,
            src_cls=src_cls,
            resolve_class=resolve_class,
            add=add,
            suggest=suggest,
        )
        return

    if len(members) == 4:
        _collect_overlay_attribute_edge_function_diagnostics(
            ann_input=ann_input,
            src_cfg_name=src_cfg_name,
            src_cls=src_cls,
            resolve_class=resolve_class,
            add=add,
            suggest=suggest,
        )
        return

    add(
        rng=ann_input.path.range,
        message=f"Overlay attribute path has too many segments (got: {ann_input.path.text})",
        code="aware.annotation.path_invalid",
    )


def _collect_overlay_attribute_edge_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    src_cfg_name: str,
    src_cls: CodeSectionClass,
    resolve_class: ResolveClassFn,
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    rel_token, edge_token, edge_attr_token = ann_input.members[0], ann_input.members[1], ann_input.members[2]
    rel_names = [attribute.name for attribute in src_cls.code_section_attributes]
    if rel_token.text not in rel_names:
        add(
            rng=rel_token.range,
            message=f"Attribute {rel_token.text!r} not found on class {src_cfg_name}",
            code="aware.annotation.member_not_found",
            data={"suggestions": suggest(rel_token.text, rel_names)},
        )

    resolved_edge = resolve_class(edge_token.text)
    if resolved_edge is None:
        add(
            rng=edge_token.range,
            message=f"Class not found for edge reference: {edge_token.text}",
            code="aware.annotation.class_not_found",
            data={"suggestions": suggest(edge_token.text, list(ann_input.class_candidates))},
        )
        return

    _edge_fqn, edge_cfg = resolved_edge
    edge_cls = edge_cfg.code_section_class
    if edge_cls is None:
        return

    edge_attr_names = [attribute.name for attribute in edge_cls.code_section_attributes]
    if edge_attr_token.text not in edge_attr_names:
        add(
            rng=edge_attr_token.range,
            message=f"Attribute {edge_attr_token.text!r} not found on class {edge_cfg.name}",
            code="aware.annotation.member_not_found",
            data={"suggestions": suggest(edge_attr_token.text, edge_attr_names)},
        )


def _collect_overlay_attribute_edge_function_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    src_cfg_name: str,
    src_cls: CodeSectionClass,
    resolve_class: ResolveClassFn,
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    rel_token, edge_token, edge_function_token, edge_attr_token = (
        ann_input.members[0],
        ann_input.members[1],
        ann_input.members[2],
        ann_input.members[3],
    )
    rel_names = [attribute.name for attribute in src_cls.code_section_attributes]
    if rel_token.text not in rel_names:
        add(
            rng=rel_token.range,
            message=f"Attribute {rel_token.text!r} not found on class {src_cfg_name}",
            code="aware.annotation.member_not_found",
            data={"suggestions": suggest(rel_token.text, rel_names)},
        )

    resolved_edge = resolve_class(edge_token.text)
    if resolved_edge is None:
        add(
            rng=edge_token.range,
            message=f"Class not found for edge reference: {edge_token.text}",
            code="aware.annotation.class_not_found",
            data={"suggestions": suggest(edge_token.text, list(ann_input.class_candidates))},
        )
        return

    _edge_fqn, edge_cfg = resolved_edge
    edge_cls = edge_cfg.code_section_class
    if edge_cls is None:
        return

    edge_function = next(
        (candidate for candidate in edge_cls.code_section_functions if candidate.name == edge_function_token.text),
        None,
    )
    if edge_function is None:
        add(
            rng=edge_function_token.range,
            message=f"Function {edge_function_token.text!r} not found on class {edge_cfg.name}",
            code="aware.annotation.member_not_found",
            data={
                "suggestions": suggest(
                    edge_function_token.text,
                    [candidate.name for candidate in edge_cls.code_section_functions],
                )
            },
        )
        return

    edge_function_attr_names = [attribute.name for attribute in edge_function.code_section_attributes]
    if edge_attr_token.text not in edge_function_attr_names:
        add(
            rng=edge_attr_token.range,
            message=f"Attribute {edge_attr_token.text!r} not found on function {edge_function_token.text!r}",
            code="aware.annotation.member_not_found",
            data={"suggestions": suggest(edge_attr_token.text, edge_function_attr_names)},
        )
