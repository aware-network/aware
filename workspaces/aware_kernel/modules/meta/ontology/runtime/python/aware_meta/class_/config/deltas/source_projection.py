from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from hashlib import sha256
from typing import Any, cast

from aware_meta.materialization.deltas.code_dto import (
    CodeGrammarAnchorBinding,
    CodeGrammarAnchorBindingDirection,
    CodeGrammarAnchorRenderReplacement,
    CodeGrammarAnchorRenderSource,
    CodeGraphFieldSelector,
    CodeLanguage,
    CodeSectionDeltaEntry,
    CodeSectionDeltaOperationKind,
    CodeSectionRef,
    CodeSegmentRef,
)
from aware_meta.materialization.deltas.coercion import (
    mapping_value,
    optional_text,
    tuple_text,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaSourceProjectionContext,
    MetaProviderDeltaSourceProjectionFeatureResult,
    meta_provider_delta_world_change_event_key,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_types import JsonObject


FEATURE_KEY = "class_config"
CLASS_CONFIG_SOURCE_PROJECTION_SKIPPED_REASON = (
    "meta_source_projection_class_config_requires_renderer_segment_policy"
)
CLASS_CONFIG_DESCRIPTION_SOURCE_PROJECTION_READY_REASON = (
    "meta_source_projection_class_config_description_segment_delta_ready"
)
CLASS_CONFIG_DESCRIPTION_SOURCE_PROJECTION_BLOCKED_REASON = (
    "meta_source_projection_class_config_description_requires_renderable_segment"
)
CLASS_CONFIG_DESCRIPTION_SOURCE_PROJECTION_REQUIRED_FIELDS = (
    "relative_path",
    "class_name",
    "baseline_description",
    "current_description",
)
CLASS_CONFIG_STRUCTURAL_DELETE_SOURCE_PROJECTION_READY_REASON = (
    "meta_source_projection_class_config_structural_delete_grammar_anchor_ready"
)
CLASS_CONFIG_STRUCTURAL_DELETE_SOURCE_PROJECTION_BLOCKED_REASON = (
    "meta_source_projection_class_config_structural_delete_requires_source_anchor"
)
CLASS_CONFIG_STRUCTURAL_DELETE_SOURCE_PROJECTION_REQUIRED_FIELDS = (
    "single_source_ref",
    "class_name",
)
META_SOURCE_PROJECTION_PROVIDER_KEY = "aware_meta"


def source_projection_feature_results_from_class_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> tuple[MetaProviderDeltaSourceProjectionFeatureResult, ...]:
    if _is_structural_class_delete(operation=operation):
        bindings, sources, replacements = _structural_class_delete_render_delta(
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
                    reason=(
                        CLASS_CONFIG_STRUCTURAL_DELETE_SOURCE_PROJECTION_READY_REASON
                    ),
                    required_evidence_fields=(
                        CLASS_CONFIG_STRUCTURAL_DELETE_SOURCE_PROJECTION_REQUIRED_FIELDS
                    ),
                ),
            )
        return (
            MetaProviderDeltaSourceProjectionFeatureResult.from_blocked(
                feature_key=FEATURE_KEY,
                operation=operation,
                reason=(
                    CLASS_CONFIG_STRUCTURAL_DELETE_SOURCE_PROJECTION_BLOCKED_REASON
                ),
                event_refs=(
                    meta_provider_delta_world_change_event_key(
                        operation=operation,
                    ),
                ),
                required_evidence_fields=(
                    CLASS_CONFIG_STRUCTURAL_DELETE_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
                missing_evidence_fields=_missing_structural_delete_fields(
                    operation=operation,
                    context=context,
                ),
            ),
        )

    entry = _code_section_delta_entry_from_class_description_typed_operation(
        operation=operation,
        context=context,
    )
    if entry is not None:
        return (
            MetaProviderDeltaSourceProjectionFeatureResult.from_projected(
                feature_key=FEATURE_KEY,
                operation=operation,
                entries=(entry,),
                reason=CLASS_CONFIG_DESCRIPTION_SOURCE_PROJECTION_READY_REASON,
                required_evidence_fields=(
                    CLASS_CONFIG_DESCRIPTION_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
            ),
        )
    missing_fields = _missing_class_description_source_projection_fields(
        operation=operation,
    )
    if _class_description_was_updated(operation=operation):
        return (
            MetaProviderDeltaSourceProjectionFeatureResult.from_blocked(
                feature_key=FEATURE_KEY,
                operation=operation,
                reason=CLASS_CONFIG_DESCRIPTION_SOURCE_PROJECTION_BLOCKED_REASON,
                event_refs=(
                    meta_provider_delta_world_change_event_key(
                        operation=operation,
                    ),
                ),
                required_evidence_fields=(
                    CLASS_CONFIG_DESCRIPTION_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
                missing_evidence_fields=missing_fields,
            ),
        )
    return (
        MetaProviderDeltaSourceProjectionFeatureResult.skipped(
            feature_key=FEATURE_KEY,
            operation=operation,
            reason=CLASS_CONFIG_SOURCE_PROJECTION_SKIPPED_REASON,
            event_refs=(
                meta_provider_delta_world_change_event_key(operation=operation),
            ),
        ),
    )


def _structural_class_delete_render_delta(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> tuple[
    tuple[CodeGrammarAnchorBinding, ...],
    tuple[CodeGrammarAnchorRenderSource, ...],
    tuple[CodeGrammarAnchorRenderReplacement, ...],
]:
    relative_path = _single_source_ref(operation.source_refs, context=context)
    class_name = _class_name(operation=operation)
    class_fqn = _class_fqn(operation=operation) or _class_key(operation=operation)
    if relative_path is None or class_name is None:
        return (), (), ()

    binding_key = f"aware_meta.class_config.{operation.operation_key}.delete_node"
    event_ref = meta_provider_delta_world_change_event_key(operation=operation)
    binding = CodeGrammarAnchorBinding(
        binding_key=binding_key,
        language="aware",
        grammar_profile_key="aware",
        provider_key=META_SOURCE_PROJECTION_PROVIDER_KEY,
        lane_key="meta_ocg_source_projection",
        grammar_rule_name="class_def",
        anchor_field_path="__node__",
        anchor_role="graph_structural_node",
        graph_selector=CodeGraphFieldSelector(
            provider_key=META_SOURCE_PROJECTION_PROVIDER_KEY,
            semantic_owner="aware_meta.object_config_graph",
            subject_kind="class_config",
            subject_type="aware_meta.ClassConfig",
            semantic_key=operation.semantic_key,
            object_key=class_fqn,
            class_fqn=class_fqn,
            class_name=class_name,
            field_name=class_name,
            field_path=f"{class_name}.__node__",
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta."
                        "class_config_graph_selector"
                    ),
                    "operation_key": operation.operation_key,
                    "semantic_key": operation.semantic_key,
                    "class_fqn": class_fqn,
                    "class_name": class_name,
                }
            ),
        ),
        value_domain="aware_class_def",
        direction=CodeGrammarAnchorBindingDirection.graph_to_source,
        renderer_key="aware.grammar_anchor",
        render_policy_key="aware_meta.class_config.structural_delete",
        compatibility_section_type="class",
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "class_config_delete_grammar_anchor_binding"
                ),
                "operation_key": operation.operation_key,
                "semantic_key": operation.semantic_key,
                "class_fqn": class_fqn,
                "class_name": class_name,
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
                    "class_config_delete_grammar_anchor_source"
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
                    "class_config_delete_grammar_anchor_replacement"
                ),
                "operation_key": operation.operation_key,
                "class_fqn": class_fqn,
                "class_name": class_name,
            }
        ),
    )
    return (binding,), (source,), (replacement,)


def _is_structural_class_delete(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    return (
        operation.ontology_subject_kind == "class"
        and operation.operation_family == "delete"
        and operation.provider_operation_type == "meta_ocg.class.delete"
    )


def _missing_structural_delete_fields(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> tuple[str, ...]:
    missing: list[str] = []
    if _single_source_ref(operation.source_refs, context=context) is None:
        missing.append("single_source_ref")
    if _class_name(operation=operation) is None:
        missing.append("class_name")
    return tuple(missing)


def _code_section_delta_entry_from_class_description_typed_operation(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> CodeSectionDeltaEntry | None:
    if not _class_description_was_updated(operation=operation):
        return None
    relative_path = _single_source_ref(operation.source_refs)
    class_name = _class_name(operation=operation)
    baseline_description = _baseline_description(operation=operation)
    current_description = _current_description(operation=operation)
    if (
        relative_path is None
        or class_name is None
        or baseline_description is None
        or current_description is None
    ):
        return None
    section_ref = CodeSectionRef(
        package_name=context.package_name,
        relative_path=relative_path,
        language=context.target_language,
        section_type="class",
        qualname=class_name,
        semantic_key=operation.semantic_key,
        source_refs=list(_sorted_unique((*operation.source_refs, relative_path))),
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.class_description_section_ref",
                "operation_key": operation.operation_key,
                "class_name": class_name,
                "class_key": _class_key(operation=operation),
            }
        ),
    )
    segment_ref = CodeSegmentRef(
        segment_name="description_comment",
        before_segment_hash=_sha256_digest(baseline_description),
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.class_description_segment_ref",
                "class_name": class_name,
            }
        ),
    )
    return CodeSectionDeltaEntry(
        operation=CodeSectionDeltaOperationKind.replace_segment,
        section_ref=section_ref,
        segment_ref=segment_ref,
        content_text=current_description,
        before_hash=None,
        after_hash=_sha256_digest(current_description),
        event_ref=meta_provider_delta_world_change_event_key(operation=operation),
        semantic_key=operation.semantic_key,
        provider_key=META_SOURCE_PROJECTION_PROVIDER_KEY,
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.class_description_section_delta",
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "ontology_subject_kind": operation.ontology_subject_kind,
                "class_name": class_name,
                "class_key": _class_key(operation=operation),
            }
        ),
    )


def _class_description_was_updated(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    if operation.ontology_subject_kind != "class":
        return False
    if operation.operation_family != "update":
        return False
    baseline_description = _baseline_description(operation=operation)
    current_description = _current_description(operation=operation)
    return baseline_description != current_description


def _missing_class_description_source_projection_fields(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[str, ...]:
    missing: list[str] = []
    if _single_source_ref(operation.source_refs) is None:
        missing.append("relative_path")
    if _class_name(operation=operation) is None:
        missing.append("class_name")
    if _baseline_description(operation=operation) is None:
        missing.append("baseline_description")
    if _current_description(operation=operation) is None:
        missing.append("current_description")
    return tuple(missing)


def _baseline_description(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    signature = _baseline_class_signature(operation=operation)
    return optional_text(signature.get("description"))


def _current_description(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    signature = _current_class_signature(operation=operation)
    return optional_text(signature.get("description"))


def _class_name(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    for source in (
        operation.current,
        operation.baseline,
        _current_class_signature(operation=operation),
        _baseline_class_signature(operation=operation),
        _baseline_object(operation=operation),
    ):
        name = optional_text(source.get("class_name")) or optional_text(
            source.get("name"),
        )
        if name is not None:
            return name
    class_fqn = _class_fqn(operation=operation)
    if class_fqn is not None:
        return class_fqn.rsplit(".", 1)[-1]
    class_key = _class_key(operation=operation)
    if class_key is None:
        return None
    return class_key.rsplit(".", 1)[-1]


def _class_key(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    for source in (
        operation.current,
        operation.baseline,
        _current_class_signature(operation=operation),
        _baseline_class_signature(operation=operation),
        _baseline_object(operation=operation),
    ):
        class_key = (
            optional_text(source.get("class_key"))
            or optional_text(source.get("class_fqn"))
            or optional_text(source.get("semantic_key"))
        )
        if class_key is not None:
            return class_key
    return None


def _class_fqn(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return _first_text(
        operation.current.get("class_fqn"),
        operation.current.get("node_key"),
        operation.baseline.get("class_fqn"),
        operation.baseline.get("node_key"),
        _baseline_object(operation=operation).get("class_fqn"),
        _baseline_object(operation=operation).get("node_key"),
        _class_fqn_from_semantic_key(operation.semantic_key),
    )


def _class_fqn_from_semantic_key(value: str) -> str | None:
    _, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    return optional_text(node_key.split("/", maxsplit=1)[0])


def _current_class_signature(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> Mapping[str, object]:
    for candidate in (
        operation.current.get("class_signature"),
        operation.current,
    ):
        if isinstance(candidate, Mapping):
            return mapping_value(candidate)
    return {}


def _baseline_class_signature(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> Mapping[str, object]:
    baseline_object = _baseline_object(operation=operation)
    for candidate in (
        operation.baseline.get("class_signature"),
        operation.baseline.get("baseline_class_signature"),
        baseline_object.get("class_signature"),
        baseline_object,
    ):
        if isinstance(candidate, Mapping):
            return mapping_value(candidate)
    return {}


def _baseline_object(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> Mapping[str, object]:
    candidate = operation.baseline.get("object")
    if isinstance(candidate, Mapping):
        return mapping_value(candidate)
    return {}


def _single_source_ref(
    source_refs: Sequence[str],
    *,
    context: MetaProviderDeltaSourceProjectionContext | None = None,
) -> str | None:
    if context is not None:
        refs = tuple(
            dict.fromkeys(
                item
                for item in (
                    _source_ref_relative_to_sources_root(item, context=context)
                    for item in source_refs
                )
                if item is not None
            )
        )
        return refs[0] if len(refs) == 1 else None
    refs = _sorted_unique(source_refs)
    return refs[0] if len(refs) == 1 else None


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


def _sha256_digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _sorted_unique(values: Iterable[str | object]) -> tuple[str, ...]:
    return tuple(sorted({text for item in values for text in tuple_text(item)}))


def _json_object(payload: Mapping[str, object]) -> JsonObject:
    return JsonObject(cast(Any, dict(payload)))


def _first_text(*values: object) -> str | None:
    for value in values:
        text = optional_text(value)
        if text is not None:
            return text
    return None


__all__ = [
    "CLASS_CONFIG_DESCRIPTION_SOURCE_PROJECTION_BLOCKED_REASON",
    "CLASS_CONFIG_DESCRIPTION_SOURCE_PROJECTION_READY_REASON",
    "CLASS_CONFIG_DESCRIPTION_SOURCE_PROJECTION_REQUIRED_FIELDS",
    "CLASS_CONFIG_SOURCE_PROJECTION_SKIPPED_REASON",
    "CLASS_CONFIG_STRUCTURAL_DELETE_SOURCE_PROJECTION_BLOCKED_REASON",
    "CLASS_CONFIG_STRUCTURAL_DELETE_SOURCE_PROJECTION_READY_REASON",
    "CLASS_CONFIG_STRUCTURAL_DELETE_SOURCE_PROJECTION_REQUIRED_FIELDS",
    "source_projection_feature_results_from_class_config_typed_operation",
]
