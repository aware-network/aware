from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from aware_meta.materialization.deltas.code_dto import (
    CodeGrammarAnchorBinding,
    CodeGrammarAnchorBindingDirection,
    CodeGrammarAnchorRenderReplacement,
    CodeGrammarAnchorRenderSource,
    CodeGraphFieldSelector,
    CodeLanguage,
)
from aware_meta.materialization.deltas.coercion import optional_text
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaSourceProjectionContext,
    MetaProviderDeltaSourceProjectionFeatureResult,
    meta_provider_delta_world_change_event_key,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_types import JsonObject


FEATURE_KEY = "enum_config"
ENUM_STRUCTURAL_DELETE_SOURCE_PROJECTION_READY_REASON = (
    "meta_source_projection_enum_config_structural_delete_grammar_anchor_ready"
)
ENUM_STRUCTURAL_DELETE_SOURCE_PROJECTION_BLOCKED_REASON = (
    "meta_source_projection_enum_config_structural_delete_requires_source_anchor"
)
ENUM_STRUCTURAL_DELETE_SOURCE_PROJECTION_REQUIRED_FIELDS = (
    "single_source_ref",
    "enum_name",
)


def source_projection_feature_results_from_enum_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> tuple[MetaProviderDeltaSourceProjectionFeatureResult, ...]:
    event_refs = (meta_provider_delta_world_change_event_key(operation=operation),)
    if not _is_structural_enum_delete(operation=operation):
        return (
            MetaProviderDeltaSourceProjectionFeatureResult.skipped(
                feature_key=FEATURE_KEY,
                operation=operation,
                reason="meta_source_projection_enum_config_not_required",
                event_refs=event_refs,
            ),
        )

    bindings, sources, replacements = _structural_enum_delete_render_delta(
        operation=operation,
        context=context,
    )
    if bindings and sources and replacements:
        return (
            MetaProviderDeltaSourceProjectionFeatureResult.from_projected(
                feature_key=FEATURE_KEY,
                operation=operation,
                entries=(),
                grammar_anchor_bindings=bindings,
                grammar_anchor_sources=sources,
                grammar_anchor_replacements=replacements,
                reason=ENUM_STRUCTURAL_DELETE_SOURCE_PROJECTION_READY_REASON,
                required_evidence_fields=(
                    ENUM_STRUCTURAL_DELETE_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
            ),
        )
    return (
        MetaProviderDeltaSourceProjectionFeatureResult.from_blocked(
            feature_key=FEATURE_KEY,
            operation=operation,
            reason=ENUM_STRUCTURAL_DELETE_SOURCE_PROJECTION_BLOCKED_REASON,
            event_refs=event_refs,
            required_evidence_fields=(
                ENUM_STRUCTURAL_DELETE_SOURCE_PROJECTION_REQUIRED_FIELDS
            ),
            missing_evidence_fields=_missing_structural_delete_fields(
                operation=operation,
                context=context,
            ),
        ),
    )


def _structural_enum_delete_render_delta(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> tuple[
    tuple[CodeGrammarAnchorBinding, ...],
    tuple[CodeGrammarAnchorRenderSource, ...],
    tuple[CodeGrammarAnchorRenderReplacement, ...],
]:
    relative_path = _single_source_ref(operation.source_refs, context=context)
    enum_name = _enum_name(operation=operation)
    enum_fqn = _enum_fqn(operation=operation)
    if relative_path is None or enum_name is None:
        return (), (), ()

    binding_key = f"aware_meta.enum_config.{operation.operation_key}.delete_node"
    event_ref = meta_provider_delta_world_change_event_key(operation=operation)
    binding = CodeGrammarAnchorBinding(
        binding_key=binding_key,
        language="aware",
        grammar_profile_key="aware",
        provider_key="aware_meta",
        lane_key="meta_ocg_source_projection",
        grammar_rule_name="enum_def",
        anchor_field_path="__node__",
        anchor_role="graph_structural_node",
        graph_selector=CodeGraphFieldSelector(
            provider_key="aware_meta",
            semantic_owner="aware_meta.object_config_graph",
            subject_kind="enum_config",
            subject_type="aware_meta.EnumConfig",
            semantic_key=operation.semantic_key,
            object_key=enum_fqn,
            field_name=enum_name,
            field_path=f"{enum_name}.__node__",
            metadata=_json_object(
                {
                    "source": "aware_meta.provider_delta.enum_config_graph_selector",
                    "operation_key": operation.operation_key,
                    "semantic_key": operation.semantic_key,
                    "enum_fqn": enum_fqn,
                    "enum_name": enum_name,
                }
            ),
        ),
        value_domain="aware_enum_def",
        direction=CodeGrammarAnchorBindingDirection.graph_to_source,
        renderer_key="aware.grammar_anchor",
        render_policy_key="aware_meta.enum_config.structural_delete",
        compatibility_section_type="enum",
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "enum_config_delete_grammar_anchor_binding"
                ),
                "operation_key": operation.operation_key,
                "semantic_key": operation.semantic_key,
                "enum_fqn": enum_fqn,
                "enum_name": enum_name,
            }
        ),
    )
    source = CodeGrammarAnchorRenderSource(
        source_key=relative_path,
        language=CodeLanguage.aware,
        relative_path=relative_path,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "enum_config_delete_grammar_anchor_source"
                ),
                "operation_key": operation.operation_key,
            }
        ),
    )
    replacement = CodeGrammarAnchorRenderReplacement(
        replacement_key=f"{binding_key}.replace",
        binding_key=binding_key,
        source_key=relative_path,
        replacement_text="",
        before_text_hash=None,
        event_ref=event_ref,
        semantic_key=operation.semantic_key,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "enum_config_delete_grammar_anchor_replacement"
                ),
                "operation_key": operation.operation_key,
                "enum_fqn": enum_fqn,
                "enum_name": enum_name,
            }
        ),
    )
    return (binding,), (source,), (replacement,)


def _is_structural_enum_delete(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    return (
        operation.ontology_subject_kind == "enum"
        and operation.operation_family == "delete"
        and operation.provider_operation_type == "meta_ocg.enum.delete"
    )


def _missing_structural_delete_fields(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> tuple[str, ...]:
    missing: list[str] = []
    if _single_source_ref(operation.source_refs, context=context) is None:
        missing.append("single_source_ref")
    if _enum_name(operation=operation) is None:
        missing.append("enum_name")
    return tuple(missing)


def _single_source_ref(
    source_refs: Sequence[str],
    *,
    context: MetaProviderDeltaSourceProjectionContext,
) -> str | None:
    unique = tuple(
        dict.fromkeys(
            item
            for item in (
                _source_ref_relative_to_sources_root(item, context=context)
                for item in source_refs
            )
            if item is not None
        )
    )
    return unique[0] if len(unique) == 1 else None


def _source_ref_relative_to_sources_root(
    value: object,
    *,
    context: MetaProviderDeltaSourceProjectionContext,
) -> str | None:
    raw_value = optional_text(value)
    if raw_value is None:
        return None
    normalized = raw_value.strip().strip("/")
    if not normalized or normalized == ".":
        return None

    sources_root = _normalized_relative_path(context.sources_root)
    package_root = _normalized_relative_path(context.package_root)
    if sources_root is not None and normalized.startswith(f"{sources_root}/"):
        return normalized[len(sources_root) + 1 :]
    if package_root is not None and normalized.startswith(f"{package_root}/"):
        package_relative = normalized[len(package_root) + 1 :]
        source_root_relative = _source_root_relative_to_package(
            package_root=package_root,
            sources_root=sources_root,
        )
        if (
            source_root_relative is not None
            and package_relative.startswith(f"{source_root_relative}/")
        ):
            return package_relative[len(source_root_relative) + 1 :]
        return package_relative

    source_root_tail = _source_root_tail(sources_root)
    if source_root_tail is not None and normalized.startswith(f"{source_root_tail}/"):
        return normalized[len(source_root_tail) + 1 :]
    return normalized


def _source_root_relative_to_package(
    *,
    package_root: str | None,
    sources_root: str | None,
) -> str | None:
    if package_root is None or sources_root is None:
        return None
    if sources_root.startswith(f"{package_root}/"):
        return sources_root[len(package_root) + 1 :]
    return None


def _source_root_tail(value: str | None) -> str | None:
    if value is None:
        return "aware"
    return optional_text(value.rsplit("/", maxsplit=1)[-1])


def _normalized_relative_path(value: str | None) -> str | None:
    text = optional_text(value)
    if text is None:
        return None
    return text.strip().strip("/")


def _enum_name(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return _first_text(
        operation.current.get("name"),
        operation.current.get("entity_name"),
        operation.current.get("enum_name"),
        operation.baseline.get("name"),
        operation.baseline.get("entity_name"),
        operation.baseline.get("enum_name"),
        _enum_name_from_fqn(_enum_fqn(operation=operation)),
        _enum_name_from_semantic_key(operation.semantic_key),
    )


def _enum_fqn(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return _first_text(
        operation.current.get("enum_fqn"),
        operation.current.get("node_key"),
        operation.baseline.get("enum_fqn"),
        operation.baseline.get("node_key"),
        _enum_fqn_from_semantic_key(operation.semantic_key),
    )


def _enum_name_from_fqn(value: str | None) -> str | None:
    if value is None:
        return None
    return optional_text(value.rsplit(".", maxsplit=1)[-1])


def _enum_fqn_from_semantic_key(value: str) -> str | None:
    _, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    return optional_text(node_key.split("/", maxsplit=1)[0])


def _enum_name_from_semantic_key(value: str) -> str | None:
    semantic_tail = _enum_fqn_from_semantic_key(value)
    if semantic_tail is None:
        _, separator, semantic_tail = value.rpartition(":")
        if not separator:
            return None
    return _enum_name_from_fqn(semantic_tail)


def _first_text(*values: object) -> str | None:
    for value in values:
        text = optional_text(value)
        if text is not None:
            return text
    return None


def _json_object(value: Mapping[str, object]) -> JsonObject:
    return JsonObject(cast(Any, dict(value)))


__all__ = [
    "ENUM_STRUCTURAL_DELETE_SOURCE_PROJECTION_BLOCKED_REASON",
    "ENUM_STRUCTURAL_DELETE_SOURCE_PROJECTION_READY_REASON",
    "source_projection_feature_results_from_enum_config_typed_operation",
]
