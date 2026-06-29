from __future__ import annotations

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.annotation.compiler import parse_identity_args
from aware_meta.fqn_resolver import FqnResolver

from aware_code.language_service.features.annotation_relationships import (
    collect_structural_relationship_keys,
)

from .contracts import (
    AnnotationAddDiagnostic,
    AnnotationSuggestFn,
    AnnotationVerbInput,
    ResolveClassFn,
)
from .helpers import first_arg_or_verb_range


def collect_identity_annotation_diagnostics(
    *,
    ann_input: AnnotationVerbInput,
    resolve_class: ResolveClassFn,
    resolver: FqnResolver,
    workspace_language: CodeLanguage | None,
    add: AnnotationAddDiagnostic,
    suggest: AnnotationSuggestFn,
) -> None:
    if ann_input.members:
        add(
            rng=ann_input.path.range,
            message=f"Identity annotation must use 'TypeRef' (got: {ann_input.path.text})",
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
    relationship_scope = None
    if class_cfg.code_section_class is not None:
        relationship_scope = resolver.scope_for_code_id(class_cfg.code_section_class.code_section.code_id)
    relationship_keys = collect_structural_relationship_keys(
        class_cfg=class_cfg,
        scope=relationship_scope,
        workspace_language=workspace_language,
    )

    try:
        _mode, structural_relation_name = parse_identity_args(list(ann_input.args))
    except ValueError as exc:
        suggestions = _identity_arg_suggestions(
            ann_input=ann_input,
            relationship_keys=relationship_keys,
            suggest=suggest,
        )
        add(
            rng=first_arg_or_verb_range(ann_input=ann_input),
            message=str(exc),
            code="aware.annotation.args_invalid",
            data={"suggestions": suggestions} if suggestions else None,
        )
        return

    if structural_relation_name is None or structural_relation_name in relationship_keys:
        return

    target_range = (
        ann_input.args_tokens[2].range if len(ann_input.args_tokens) >= 3 else first_arg_or_verb_range(ann_input=ann_input)
    )
    add(
        rng=target_range,
        message=f"Relationship {structural_relation_name!r} not found on class {class_cfg.name}",
        code="aware.annotation.member_not_found",
        data={"suggestions": suggest(structural_relation_name, relationship_keys)},
    )


def _identity_arg_suggestions(
    *,
    ann_input: AnnotationVerbInput,
    relationship_keys: list[str],
    suggest: AnnotationSuggestFn,
) -> list[str]:
    tokens = list(ann_input.args_tokens)
    if not tokens:
        return []

    first = (tokens[0].text or "").strip()
    if len(tokens) == 1:
        return suggest(first, ["contained", "standalone"])

    first_mode = first.lower()
    second = (tokens[1].text or "").strip()
    if first_mode not in {"contained", "standalone"}:
        return suggest(first, ["contained", "standalone"])
    if len(tokens) == 2:
        if second.lower() == "structural":
            return suggest("", relationship_keys)
        return suggest(second, ["structural"])

    if second.lower() != "structural":
        return suggest(second, ["structural"])

    third = (tokens[2].text or "").strip()
    return suggest(third, relationship_keys)
