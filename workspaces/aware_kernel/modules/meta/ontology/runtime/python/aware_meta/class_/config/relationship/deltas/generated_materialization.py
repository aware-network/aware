from __future__ import annotations

import ast
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from aware_meta.materialization.deltas.code_dto import (
    CodeGeneratedMaterializationActionBinding,
    CodeGeneratedMaterializationDeltaEntry,
    CodeGeneratedMaterializationDeltaMode,
    CodeGeneratedMaterializationDeltaRequest,
    CodeGeneratedMaterializationDeltaResult,
    CodeGeneratedMaterializationEventRef,
    CodeGeneratedMaterializationSkippedTarget,
    CodeGeneratedMaterializationTargetRef,
    CodeGeneratedRendererAnchorRef,
    CodeGeneratedRendererDeltaOperation,
    CodeGeneratedRendererDeltaOperationKind,
    CodeGrammarAnchorRenderTargetKind,
    CodeGraphFieldSelector,
    CodeLanguage,
    ResolveCodeGrammarAnchorRenderDeltaRequest,
)
from aware_meta.materialization.deltas.coercion import (
    mapping_value,
    optional_text,
    tuple_text,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaGeneratedMaterializationContext,
    MetaProviderDeltaGeneratedMaterializationFeatureResult,
    meta_provider_delta_world_change_event_key,
)
from aware_meta.materialization.deltas.generated_materialization_spans import (
    MetaGeneratedMaterializationTextSpanContext,
    meta_generated_materialization_correlated_text_span_render_delta,
    meta_generated_materialization_text_span_replacement,
)
from aware_meta.materialization.deltas.language_renderer_contracts import (
    MetaLanguageGeneratedMaterializationDeltaContext,
    MetaLanguageGeneratedMaterializationDeltaRenderRequest,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_code_ontology.code.code_enums import CodeLanguage as MetaPluginCodeLanguage
from aware_types import JsonObject


META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY = "aware_meta"
META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER = "aware_meta.ocg"
META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PRODUCT_INTENT = (
    "python_orm_runtime"
)
META_PYTHON_ORM_RELATIONSHIP_RENDERER_PROFILE = "orm_runtime"
META_PYTHON_ORM_RELATIONSHIP_MATERIALIZATION_SOURCE = "ontology_orm_models"
META_PYTHON_ORM_RELATIONSHIP_RENDERER_KEY = "python.orm.relationship.load_policy"
META_PYTHON_ORM_RELATIONSHIP_ANCHOR_KEY = "python.orm.relationship.field"
META_PYTHON_ORM_RELATIONSHIP_EVIDENCE_ONLY_DIAGNOSTIC = (
    "meta_python_orm_relationship_generated_materialization_renderer_operation_"
    "evidence_only"
)
META_PYTHON_ORM_RELATIONSHIP_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC = (
    "meta_python_orm_relationship_generated_materialization_target_relative_path_"
    "missing"
)
META_PYTHON_ORM_RELATIONSHIP_FIELD_SPAN_MISSING_DIAGNOSTIC = (
    "meta_python_orm_relationship_generated_materialization_field_span_missing"
)
META_PYTHON_ORM_RELATIONSHIP_FIELD_TEXT_MISSING_DIAGNOSTIC = (
    "meta_python_orm_relationship_generated_materialization_field_text_missing"
)
META_PYTHON_ORM_RELATIONSHIP_STRUCTURAL_CREATE_SPAN_MISSING_DIAGNOSTIC = (
    "meta_python_orm_relationship_generated_materialization_create_span_missing"
)
META_PYTHON_ORM_RELATIONSHIP_STRUCTURAL_DELETE_SPAN_MISSING_DIAGNOSTIC = (
    "meta_python_orm_relationship_generated_materialization_delete_span_missing"
)
META_PYTHON_ORM_RELATIONSHIP_NOT_REQUIRED_REASON = (
    "meta_python_orm_relationship_load_policy_delta_not_required"
)


@dataclass(frozen=True, slots=True)
class MetaPythonOrmRelationshipGeneratedMaterializationContext:
    package_name: str | None = None
    package_root: str | None = None
    sources_root: str | None = None
    target_language: str = "python"
    renderer_profile: str = META_PYTHON_ORM_RELATIONSHIP_RENDERER_PROFILE
    materialization_source: str = META_PYTHON_ORM_RELATIONSHIP_MATERIALIZATION_SOURCE
    artifact_family: str = "ocg_language_materialization"
    artifact_role: str = "python_orm_model"


@dataclass(frozen=True, slots=True)
class MetaPythonOrmRelationshipGeneratedMaterializationDeltaEvidence:
    delta_request: CodeGeneratedMaterializationDeltaRequest
    result: CodeGeneratedMaterializationDeltaResult


@dataclass(frozen=True, slots=True)
class _PythonOrmRelationshipFieldDeltaEvidence:
    grammar_anchor_render_delta: ResolveCodeGrammarAnchorRenderDeltaRequest
    content_text: str
    before_hash: str
    after_hash: str


def generated_materialization_feature_results_from_relationship_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> tuple[MetaProviderDeltaGeneratedMaterializationFeatureResult, ...]:
    if operation.ontology_subject_kind != "relationship":
        return (
            MetaProviderDeltaGeneratedMaterializationFeatureResult.skipped(
                feature_key="relationship_config",
                operation=operation,
                reason=(
                    "meta_python_orm_relationship_generated_materialization_"
                    "subject_not_supported"
                ),
                event_refs=(
                    meta_provider_delta_world_change_event_key(operation=operation),
                ),
            ),
        )

    evidence = python_orm_generated_materialization_delta_from_relationship_config_typed_operation(
        operation,
        context=_python_orm_relationship_context(context),
    )
    return (
        MetaProviderDeltaGeneratedMaterializationFeatureResult.from_evidence(
            feature_key="relationship_config",
            operation=operation,
            delta_request=evidence.delta_request,
            result=evidence.result,
            reason=(
                "meta_python_orm_relationship_generated_materialization_"
                "evidence_built"
            ),
        ),
    )


def python_orm_generated_materialization_delta_from_relationship_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    *,
    context: MetaPythonOrmRelationshipGeneratedMaterializationContext | None = None,
) -> MetaPythonOrmRelationshipGeneratedMaterializationDeltaEvidence:
    resolved_context = (
        context or MetaPythonOrmRelationshipGeneratedMaterializationContext()
    )
    plugin_evidence = _python_orm_relationship_plugin_delta_evidence(
        operation=operation,
        context=resolved_context,
    )
    if plugin_evidence is not None:
        return plugin_evidence
    event_key = meta_provider_delta_world_change_event_key(operation=operation)
    target = _target_ref(operation=operation, context=resolved_context)
    request = CodeGeneratedMaterializationDeltaRequest(
        provider_key=(
            META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY
        ),
        semantic_owner=(
            META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
        ),
        package_name=resolved_context.package_name,
        package_root=resolved_context.package_root,
        sources_root=resolved_context.sources_root,
        product_intent=(
            META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PRODUCT_INTENT
        ),
        events=[
            CodeGeneratedMaterializationEventRef(
                event_key=event_key,
                semantic_key=operation.semantic_key,
                verb=operation.operation_family,
                subject_type=operation.ontology_subject_kind,
                source="aware_meta.provider_delta.semantic_world_change",
                source_refs=list(_sorted_unique(operation.source_refs)),
                payload=_json_object(
                    {
                        "operation_key": operation.operation_key,
                        "provider_operation_type": operation.provider_operation_type,
                    }
                ),
            )
        ],
        action_bindings=[
            CodeGeneratedMaterializationActionBinding(
                action_key=(
                    "aware_meta.python_orm.relationship.generated_materialization."
                    f"{operation.operation_key}"
                ),
                event_key=event_key,
                target=target,
                policy_key="aware_meta.python_orm.relationship.load_policy",
                renderer_key=META_PYTHON_ORM_RELATIONSHIP_RENDERER_KEY,
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.provider_delta.python_orm_relationship_"
                            "generated_materialization_action"
                        ),
                        "operation_key": operation.operation_key,
                    }
                ),
            )
        ],
        targets=[target],
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta.python_orm_relationship_"
                    "generated_materialization_delta_request"
                ),
                "renderer_profile": resolved_context.renderer_profile,
                "materialization_source": resolved_context.materialization_source,
            }
        ),
    )
    result = _python_orm_relationship_result(
        operation=operation,
        context=resolved_context,
        event_key=event_key,
        target=target,
    )
    return MetaPythonOrmRelationshipGeneratedMaterializationDeltaEvidence(
        delta_request=request,
        result=result,
    )


def _python_orm_relationship_plugin_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmRelationshipGeneratedMaterializationContext,
) -> MetaPythonOrmRelationshipGeneratedMaterializationDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "relationship"
        or operation.operation_family not in {"create", "delete", "update"}
    ):
        return None
    try:
        plugin = MetaLanguagePluginRegistry.get(
            _meta_plugin_code_language(context.target_language)
        )
    except KeyError:
        return None
    render_result = plugin.render_generated_materialization_delta(
        MetaLanguageGeneratedMaterializationDeltaRenderRequest(
            operation=operation,
            context=_language_delta_context(context),
            renderer_profile=context.renderer_profile,
            materialization_source=context.materialization_source,
        )
    )
    if (
        not render_result.handled
        or render_result.delta_request is None
        or render_result.result is None
    ):
        return None
    return MetaPythonOrmRelationshipGeneratedMaterializationDeltaEvidence(
        delta_request=render_result.delta_request,
        result=render_result.result,
    )


def _language_delta_context(
    context: MetaPythonOrmRelationshipGeneratedMaterializationContext,
) -> MetaLanguageGeneratedMaterializationDeltaContext:
    return MetaLanguageGeneratedMaterializationDeltaContext(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        target_language=context.target_language,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        product_intent=(
            META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PRODUCT_INTENT
        ),
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
    )


def _meta_plugin_code_language(value: str) -> MetaPluginCodeLanguage:
    try:
        return MetaPluginCodeLanguage(value)
    except ValueError:
        return MetaPluginCodeLanguage.python


def _python_orm_relationship_result(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmRelationshipGeneratedMaterializationContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
) -> CodeGeneratedMaterializationDeltaResult:
    if _relationship_structural_create_required(operation=operation):
        delta_evidence = _python_orm_relationship_create_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    elif _relationship_structural_delete_required(operation=operation):
        delta_evidence = _python_orm_relationship_delete_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    elif _relationship_load_policy_changed(operation=operation):
        delta_evidence = _python_orm_relationship_field_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    else:
        return CodeGeneratedMaterializationDeltaResult(
            provider_key=(
                META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY
            ),
            semantic_owner=(
                META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
            ),
            available=True,
            mode=CodeGeneratedMaterializationDeltaMode.not_required,
            skipped_targets=[
                CodeGeneratedMaterializationSkippedTarget(
                    target=target,
                    reason=META_PYTHON_ORM_RELATIONSHIP_NOT_REQUIRED_REASON,
                    event_refs=[event_key],
                )
            ],
        )

    has_delta = delta_evidence is not None
    diagnostics = (
        ()
        if has_delta
        else _python_orm_relationship_guarded_delta_diagnostics(
            operation=operation,
            target=target,
        )
    )
    entry_mode = (
        CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
        if has_delta
        else CodeGeneratedMaterializationDeltaMode.fallback_full_render
    )
    content_text = delta_evidence.content_text if delta_evidence is not None else None
    before_hash = delta_evidence.before_hash if delta_evidence is not None else None
    after_hash = (
        delta_evidence.after_hash
        if delta_evidence is not None
        else (_sha256_digest(content_text) if content_text is not None else None)
    )
    renderer_operation = CodeGeneratedRendererDeltaOperation(
        operation_key=f"aware_meta.python_orm.relationship:{operation.operation_key}",
        kind=(
            CodeGeneratedRendererDeltaOperationKind.replace_anchor
            if has_delta
            else CodeGeneratedRendererDeltaOperationKind.fallback_full_render
        ),
        target=target,
        anchor=_anchor_ref(operation=operation, context=context),
        renderer_key=META_PYTHON_ORM_RELATIONSHIP_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        before_hash=before_hash,
        after_hash=after_hash,
        content_text=content_text,
        replacement_text=content_text,
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        diagnostics=list(diagnostics),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta.python_orm_relationship_"
                    "renderer_operation"
                ),
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "mode_reason": (
                    "python_orm_relationship_grammar_anchor_render_delta_ready"
                    if has_delta
                    else "python_orm_relationship_guarded_delta_missing"
                ),
            }
        ),
    )
    entry = CodeGeneratedMaterializationDeltaEntry(
        entry_key=f"aware_meta.python_orm.relationship:{operation.operation_key}",
        mode=entry_mode,
        target=target,
        grammar_anchor_render_delta=(
            delta_evidence.grammar_anchor_render_delta
            if delta_evidence is not None
            else None
        ),
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        artifact_key=target.target_key,
        relative_path=target.relative_path,
        before_hash=before_hash,
        after_hash=after_hash,
        renderer_operations=[renderer_operation],
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        diagnostics=list(diagnostics),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta.python_orm_relationship_"
                    "generated_materialization_delta_entry"
                ),
                "operation_key": operation.operation_key,
                "package_delta_emitted": False,
                "section_delta_emitted": False,
                "grammar_anchor_render_delta_emitted": has_delta,
            }
        ),
    )
    return CodeGeneratedMaterializationDeltaResult(
        provider_key=(
            META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY
        ),
        semantic_owner=(
            META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
        ),
        available=True,
        mode=entry_mode,
        entries=[entry],
        diagnostics=list(diagnostics),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta.python_orm_relationship_"
                    "generated_materialization_delta_result"
                ),
                "operation_key": operation.operation_key,
                "renderer_operation_count": 1,
                "package_delta_emitted": False,
                "section_delta_emitted": False,
                "grammar_anchor_render_delta_emitted": has_delta,
            }
        ),
    )


def _python_orm_relationship_field_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmRelationshipGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmRelationshipFieldDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "relationship"
        or operation.operation_family != "update"
        or target.relative_path is None
    ):
        return None
    class_name = _source_class_name(operation=operation)
    relationship_key = _relationship_key(operation=operation)
    replacement_text = _python_relationship_field_text(operation=operation)
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if (
        class_name is None
        or relationship_key is None
        or replacement_text is None
        or source_state is None
    ):
        return None
    relative_path, source_text = source_state
    span = _python_relationship_field_span(
        source_text=source_text,
        class_name=class_name,
        relationship_key=relationship_key,
    )
    if span is None:
        return None
    byte_start, byte_end, before_text = span
    before_hash = _sha256_digest(before_text)
    after_hash = _sha256_digest(replacement_text)
    source_hash = _sha256_digest(source_text)
    target_key = target.target_key
    if target_key is None:
        return None
    graph_selector = CodeGraphFieldSelector(
        provider_key=(
            META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY
        ),
        semantic_owner=(
            META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
        ),
        subject_kind="relationship_config",
        subject_type="ClassConfigRelationship",
        semantic_key=operation.semantic_key,
        object_key=_source_class_fqn(operation=operation),
        field_name="load_policy_args",
        field_path=f"{class_name}.{relationship_key}.load_policy_args",
        class_fqn=_source_class_fqn(operation=operation),
        class_name=class_name,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta.python_orm_relationship_"
                    "graph_selector"
                ),
                "operation_key": operation.operation_key,
                "relationship_key": relationship_key,
            }
        ),
    )
    span_context = MetaGeneratedMaterializationTextSpanContext(
        target_key=target_key,
        source_key=relative_path,
        relative_path=relative_path,
        language=_code_language(context.target_language),
        before_source_hash=source_hash,
        event_ref=event_key,
        semantic_key=operation.semantic_key,
    )
    grammar_anchor_render_delta = (
        meta_generated_materialization_correlated_text_span_render_delta(
            package_name=context.package_name,
            package_root=context.package_root,
            sources_root=context.sources_root,
            source_key=relative_path,
            relative_path=relative_path,
            language=_code_language(context.target_language),
            before_source_hash=source_hash,
            replacements=[
                meta_generated_materialization_text_span_replacement(
                    context=span_context,
                    replacement_key=(
                        "aware_meta.python_orm.relationship.load_policy:"
                        f"{operation.operation_key}"
                    ),
                    byte_start=byte_start,
                    byte_end=byte_end,
                    before_text=before_text,
                    replacement_text=replacement_text,
                    graph_selector=graph_selector,
                    metadata=_json_object(
                        {
                            "source": (
                                "aware_meta.provider_delta.python_orm_"
                                "relationship_span_target"
                            ),
                            "operation_key": operation.operation_key,
                            "relationship_key": relationship_key,
                        }
                    ),
                )
            ],
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta.python_orm_relationship_"
                        "grammar_anchor_render_delta"
                    ),
                    "operation_key": operation.operation_key,
                    "target_kind": CodeGrammarAnchorRenderTargetKind.text_span.value,
                    "renderer_key": META_PYTHON_ORM_RELATIONSHIP_RENDERER_KEY,
                    "renderer_profile": context.renderer_profile,
                }
            ),
        )
    )
    return _PythonOrmRelationshipFieldDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
    )


def _python_orm_relationship_create_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmRelationshipGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmRelationshipFieldDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "relationship"
        or operation.operation_family != "create"
        or target.relative_path is None
    ):
        return None
    class_name = _source_class_name(operation=operation)
    relationship_key = _relationship_key(operation=operation)
    replacement_text = _python_relationship_field_text(operation=operation)
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if (
        class_name is None
        or relationship_key is None
        or replacement_text is None
        or source_state is None
    ):
        return None
    relative_path, source_text = source_state
    span = _python_relationship_create_insert_span(
        source_text=source_text,
        class_name=class_name,
        relationship_key=relationship_key,
    )
    if span is None:
        return None
    byte_start, byte_end, before_text = span
    before_hash = _sha256_digest(before_text)
    after_hash = _sha256_digest(replacement_text)
    grammar_anchor_render_delta = _relationship_field_grammar_anchor_render_delta(
        operation=operation,
        context=context,
        target=target,
        relative_path=relative_path,
        source_text=source_text,
        byte_start=byte_start,
        byte_end=byte_end,
        before_text=before_text,
        replacement_text=replacement_text,
        event_key=event_key,
        operation_label="create",
    )
    if grammar_anchor_render_delta is None:
        return None
    return _PythonOrmRelationshipFieldDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
    )


def _python_orm_relationship_delete_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmRelationshipGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmRelationshipFieldDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "relationship"
        or operation.operation_family != "delete"
        or target.relative_path is None
    ):
        return None
    class_name = _source_class_name(operation=operation)
    relationship_key = _relationship_key(operation=operation)
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if class_name is None or relationship_key is None or source_state is None:
        return None
    relative_path, source_text = source_state
    span = _python_relationship_field_span(
        source_text=source_text,
        class_name=class_name,
        relationship_key=relationship_key,
    )
    if span is None:
        return None
    byte_start, byte_end, before_text = span
    replacement_text = ""
    before_hash = _sha256_digest(before_text)
    after_hash = _sha256_digest(replacement_text)
    grammar_anchor_render_delta = _relationship_field_grammar_anchor_render_delta(
        operation=operation,
        context=context,
        target=target,
        relative_path=relative_path,
        source_text=source_text,
        byte_start=byte_start,
        byte_end=byte_end,
        before_text=before_text,
        replacement_text=replacement_text,
        event_key=event_key,
        operation_label="delete",
    )
    if grammar_anchor_render_delta is None:
        return None
    return _PythonOrmRelationshipFieldDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
    )


def _relationship_field_grammar_anchor_render_delta(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmRelationshipGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    relative_path: str,
    source_text: str,
    byte_start: int,
    byte_end: int,
    before_text: str,
    replacement_text: str,
    event_key: str,
    operation_label: str,
) -> ResolveCodeGrammarAnchorRenderDeltaRequest | None:
    source_hash = _sha256_digest(source_text)
    target_key = target.target_key
    if target_key is None:
        return None
    graph_selector = _relationship_field_graph_selector(operation=operation)
    span_context = MetaGeneratedMaterializationTextSpanContext(
        target_key=target_key,
        source_key=relative_path,
        relative_path=relative_path,
        language=_code_language(context.target_language),
        before_source_hash=source_hash,
        event_ref=event_key,
        semantic_key=operation.semantic_key,
    )
    return meta_generated_materialization_correlated_text_span_render_delta(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        source_key=relative_path,
        relative_path=relative_path,
        language=_code_language(context.target_language),
        before_source_hash=source_hash,
        replacements=[
            meta_generated_materialization_text_span_replacement(
                context=span_context,
                replacement_key=(
                    "aware_meta.python_orm.relationship.field."
                    f"{operation_label}:{operation.operation_key}"
                ),
                byte_start=byte_start,
                byte_end=byte_end,
                before_text=before_text,
                replacement_text=replacement_text,
                graph_selector=graph_selector,
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.provider_delta.python_orm_"
                            "relationship_field_span_target"
                        ),
                        "operation_key": operation.operation_key,
                        "relationship_key": _relationship_key(
                            operation=operation,
                        ),
                    }
                ),
            )
        ],
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta.python_orm_relationship_"
                    "field_grammar_anchor_render_delta"
                ),
                "operation_key": operation.operation_key,
                "target_kind": CodeGrammarAnchorRenderTargetKind.text_span.value,
                "renderer_key": META_PYTHON_ORM_RELATIONSHIP_RENDERER_KEY,
                "renderer_profile": context.renderer_profile,
            }
        ),
    )


def _relationship_field_graph_selector(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> CodeGraphFieldSelector:
    class_fqn = _source_class_fqn(operation=operation)
    class_name = _source_class_name(operation=operation)
    relationship_key = _relationship_key(operation=operation)
    field_path = ".".join(
        part for part in (class_name, relationship_key, "__field__") if part
    )
    return CodeGraphFieldSelector(
        provider_key=(
            META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY
        ),
        semantic_owner=(
            META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
        ),
        subject_kind="relationship_config",
        subject_type="ClassConfigRelationship",
        semantic_key=operation.semantic_key,
        object_key=class_fqn,
        field_name="relationship_field",
        field_path=field_path,
        class_fqn=class_fqn,
        class_name=class_name,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta.python_orm_relationship_"
                    "field_graph_selector"
                ),
                "operation_key": operation.operation_key,
                "relationship_key": relationship_key,
            }
        ),
    )


def _python_relationship_field_span(
    *,
    source_text: str,
    class_name: str,
    relationship_key: str,
) -> tuple[int, int, str] | None:
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return None
    class_node = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == class_name
        ),
        None,
    )
    if class_node is None:
        return None
    for node in class_node.body:
        if not isinstance(node, ast.AnnAssign):
            continue
        target = node.target
        if not isinstance(target, ast.Name) or target.id != relationship_key:
            continue
        return _node_line_span(source_text=source_text, node=node)
    return None


def _python_relationship_create_insert_span(
    *,
    source_text: str,
    class_name: str,
    relationship_key: str,
) -> tuple[int, int, str] | None:
    class_node = _python_class_node(source_text=source_text, class_name=class_name)
    if class_node is None or _python_class_has_field(
        class_node=class_node,
        field_name=relationship_key,
    ):
        return None
    pass_node = next(
        (node for node in class_node.body if isinstance(node, ast.Pass)),
        None,
    )
    if pass_node is not None and len(class_node.body) == 1:
        return _node_line_span(source_text=source_text, node=pass_node)
    end_lineno_value = getattr(class_node, "end_lineno", None)
    if not isinstance(end_lineno_value, int):
        return None
    lines = source_text.splitlines(keepends=True)
    if end_lineno_value <= 0 or end_lineno_value > len(lines):
        return None
    insert_at = len("".join(lines[:end_lineno_value]).encode("utf-8"))
    return insert_at, insert_at, ""


def _python_class_node(*, source_text: str, class_name: str) -> ast.ClassDef | None:
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return None
    return next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == class_name
        ),
        None,
    )


def _python_class_has_field(
    *,
    class_node: ast.ClassDef,
    field_name: str,
) -> bool:
    for node in class_node.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == field_name:
                return True
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == field_name:
                    return True
    return False


def _node_line_span(
    *,
    source_text: str,
    node: ast.AST,
) -> tuple[int, int, str] | None:
    lineno_value = getattr(node, "lineno", None)
    end_lineno_value = getattr(node, "end_lineno", None)
    if not isinstance(lineno_value, int) or not isinstance(end_lineno_value, int):
        return None
    lines = source_text.splitlines(keepends=True)
    lineno = lineno_value
    end_lineno = end_lineno_value
    if lineno <= 0 or end_lineno <= 0 or lineno > len(lines):
        return None
    byte_start = len("".join(lines[: lineno - 1]).encode("utf-8"))
    byte_end = len("".join(lines[:end_lineno]).encode("utf-8"))
    before_text = source_text.encode("utf-8")[byte_start:byte_end].decode("utf-8")
    return byte_start, byte_end, before_text


def _python_relationship_field_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    relationship_key = _relationship_key(operation=operation)
    target_class_name = _target_class_name(operation=operation)
    if relationship_key is None or target_class_name is None:
        return None
    strategy = _current_forward_loading_strategy(operation=operation)
    if strategy == "lazy":
        return (
            f"    {relationship_key}: {target_class_name} | None = "
            "Field(default=None)\n"
        )
    return f"    {relationship_key}: {target_class_name}\n"


def _python_orm_relationship_guarded_delta_diagnostics(
    *,
    operation: MetaProviderDeltaTypedOperation,
    target: CodeGeneratedMaterializationTargetRef,
) -> tuple[str, ...]:
    diagnostics = [META_PYTHON_ORM_RELATIONSHIP_EVIDENCE_ONLY_DIAGNOSTIC]
    if target.relative_path is None:
        diagnostics.append(
            META_PYTHON_ORM_RELATIONSHIP_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC
        )
    if _python_relationship_field_text(operation=operation) is None:
        diagnostics.append(META_PYTHON_ORM_RELATIONSHIP_FIELD_TEXT_MISSING_DIAGNOSTIC)
    elif _relationship_structural_create_required(operation=operation):
        diagnostics.append(
            META_PYTHON_ORM_RELATIONSHIP_STRUCTURAL_CREATE_SPAN_MISSING_DIAGNOSTIC
        )
    elif _relationship_structural_delete_required(operation=operation):
        diagnostics.append(
            META_PYTHON_ORM_RELATIONSHIP_STRUCTURAL_DELETE_SPAN_MISSING_DIAGNOSTIC
        )
    else:
        diagnostics.append(META_PYTHON_ORM_RELATIONSHIP_FIELD_SPAN_MISSING_DIAGNOSTIC)
    return tuple(dict.fromkeys(diagnostics))


def _python_orm_generated_source_state(
    *,
    context: MetaPythonOrmRelationshipGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
) -> tuple[str, str] | None:
    if context.package_root is None or target.relative_path is None:
        return None
    relative_path = _section_delta_relative_path(
        relative_path=target.relative_path,
        sources_root=context.sources_root,
    )
    if relative_path is None or not _safe_relative_path(relative_path):
        return None
    base_path = Path(context.package_root)
    source_root = _normalized_relative_path(context.sources_root)
    source_path = base_path / relative_path
    if source_root is not None:
        source_path = base_path / source_root / relative_path
    if not source_path.is_file():
        return None
    try:
        return relative_path, source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _target_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmRelationshipGeneratedMaterializationContext,
) -> CodeGeneratedMaterializationTargetRef:
    class_fqn = _source_class_fqn(operation=operation)
    class_name = _source_class_name(operation=operation)
    relationship_key = _relationship_key(operation=operation)
    target_key = ".".join(
        part
        for part in (
            context.package_name,
            context.materialization_source,
            class_fqn,
            relationship_key,
            "python_orm_model",
        )
        if part
    )
    return CodeGeneratedMaterializationTargetRef(
        target_key=target_key,
        provider_key=(
            META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY
        ),
        semantic_owner=(
            META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
        ),
        target_language=context.target_language,
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        renderer_key=META_PYTHON_ORM_RELATIONSHIP_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        output_key=class_name,
        relative_path=_generated_relative_path(
            operation=operation,
            context=context,
        ),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta.python_orm_relationship_" "target_ref"
                ),
                "operation_key": operation.operation_key,
                "class_fqn": class_fqn,
                "class_name": class_name,
                "relationship_key": relationship_key,
            }
        ),
    )


def _anchor_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmRelationshipGeneratedMaterializationContext,
) -> CodeGeneratedRendererAnchorRef:
    class_name = _source_class_name(operation=operation)
    relationship_key = _relationship_key(operation=operation)
    anchor_path = ".".join(
        part for part in (class_name, relationship_key, "load_policy") if part
    )
    return CodeGeneratedRendererAnchorRef(
        anchor_key=META_PYTHON_ORM_RELATIONSHIP_ANCHOR_KEY,
        anchor_path=anchor_path,
        anchor_role="relationship_load_policy_field",
        renderer_key=META_PYTHON_ORM_RELATIONSHIP_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        target_language=context.target_language,
        section_type="attribute",
        segment_name="field_line",
        graph_selector=_json_object(
            {
                "provider_key": (
                    META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY
                ),
                "semantic_owner": (
                    META_PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
                ),
                "class_fqn": _source_class_fqn(operation=operation),
                "class_name": class_name,
                "relationship_key": relationship_key,
                "field_name": "load_policy_args",
                "field_path": anchor_path,
            }
        ),
        metadata=_json_object(
            {
                "source": ("aware_meta.provider_delta.python_orm_relationship_anchor"),
                "operation_key": operation.operation_key,
                "semantic_key": operation.semantic_key,
            }
        ),
    )


def _relationship_load_policy_changed(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    if (
        operation.ontology_subject_kind != "relationship"
        or operation.operation_family != "update"
    ):
        return False
    return _current_load_policy_args(operation=operation) != (
        _baseline_load_policy_args(operation=operation)
    )


def _relationship_structural_create_required(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    return (
        operation.ontology_subject_kind == "relationship"
        and operation.operation_family == "create"
    )


def _relationship_structural_delete_required(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    return (
        operation.ontology_subject_kind == "relationship"
        and operation.operation_family == "delete"
    )


def _current_load_policy_args(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[str, ...] | None:
    return _load_policy_args(
        payload=operation.current,
        signature=_relationship_signature(payload=operation.current),
    )


def _baseline_load_policy_args(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[str, ...] | None:
    return _load_policy_args(
        payload=operation.baseline,
        signature=_relationship_signature(payload=operation.baseline),
    )


def _load_policy_args(
    *,
    payload: Mapping[str, object],
    signature: Mapping[str, object],
) -> tuple[str, ...] | None:
    forward = _loading_strategy_text(
        payload.get("forward_loading_strategy")
        or signature.get("forward_loading_strategy")
    )
    reverse = _loading_strategy_text(
        payload.get("reverse_loading_strategy")
        or signature.get("reverse_loading_strategy")
    )
    args: list[str] = []
    if forward is not None:
        args.extend(("forward", forward))
    if reverse is not None:
        args.extend(("reverse", reverse))
    return tuple(args) if args else None


def _loading_strategy_text(value: object) -> str | None:
    text = optional_text(value)
    if text is None:
        return None
    normalized = text.rsplit(".", maxsplit=1)[-1].lower()
    if normalized in {"eager", "lazy"}:
        return normalized
    return None


def _current_forward_loading_strategy(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    signature = _relationship_signature(payload=operation.current)
    return _loading_strategy_text(
        operation.current.get("forward_loading_strategy")
        or signature.get("forward_loading_strategy")
    )


def _relationship_signature(
    *,
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    signature = mapping_value(payload.get("relationship_signature"))
    if signature:
        return signature
    object_payload = mapping_value(payload.get("object"))
    signature = mapping_value(object_payload.get("relationship_signature"))
    if signature:
        return signature
    baseline_object = mapping_value(payload.get("baseline_object"))
    return mapping_value(baseline_object.get("relationship_signature"))


def _relationship_key(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    current_signature = _relationship_signature(payload=operation.current)
    baseline_signature = _relationship_signature(payload=operation.baseline)
    return (
        optional_text(operation.current.get("relationship_key"))
        or optional_text(current_signature.get("relationship_key"))
        or optional_text(operation.baseline.get("relationship_key"))
        or optional_text(baseline_signature.get("relationship_key"))
        or _relationship_key_from_semantic_key(operation.semantic_key)
    )


def _source_class_name(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    class_fqn = _source_class_fqn(operation=operation)
    if class_fqn is not None:
        return class_fqn.rsplit(".", maxsplit=1)[-1]
    owner_key = (
        optional_text(operation.current.get("owner_semantic_key"))
        or optional_text(operation.current.get("parent_semantic_key"))
        or _owner_key_from_semantic_key(operation.semantic_key)
    )
    if owner_key is None:
        return None
    return owner_key.rsplit(".", maxsplit=1)[-1]


def _source_class_fqn(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    current_signature = _relationship_signature(payload=operation.current)
    baseline_signature = _relationship_signature(payload=operation.baseline)
    return (
        optional_text(operation.current.get("source_class_fqn"))
        or optional_text(current_signature.get("source_class_fqn"))
        or optional_text(operation.baseline.get("source_class_fqn"))
        or optional_text(baseline_signature.get("source_class_fqn"))
        or _owner_key_from_semantic_key(operation.semantic_key)
    )


def _target_class_name(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    current_signature = _relationship_signature(payload=operation.current)
    baseline_signature = _relationship_signature(payload=operation.baseline)
    target_fqn = (
        optional_text(operation.current.get("target_class_fqn"))
        or optional_text(current_signature.get("target_class_fqn"))
        or optional_text(operation.baseline.get("target_class_fqn"))
        or optional_text(baseline_signature.get("target_class_fqn"))
    )
    if target_fqn is None:
        return None
    return target_fqn.rsplit(".", maxsplit=1)[-1]


def _owner_key_from_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.relationship:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        return raw.rsplit(".", maxsplit=1)[0] if "." in raw else None
    marker = "/node:"
    if marker not in semantic_key:
        return None
    node_key = semantic_key.split(marker, maxsplit=1)[-1]
    if ":" not in node_key:
        return node_key
    return node_key.split(":", maxsplit=1)[0]


def _relationship_key_from_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.relationship:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        return raw.rsplit(".", maxsplit=1)[-1] if "." in raw else raw
    owner_key = _owner_key_from_semantic_key(semantic_key)
    if owner_key is None:
        return None
    suffix = semantic_key.split(f"/node:{owner_key}", maxsplit=1)[-1]
    parts = [part for part in suffix.split(":") if part]
    return parts[0] if parts else None


def _generated_relative_path(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmRelationshipGeneratedMaterializationContext,
) -> str | None:
    explicit_relative_path = _explicit_generated_relative_path(operation=operation)
    if explicit_relative_path is not None:
        return explicit_relative_path
    sources_root = _normalized_path(context.sources_root)
    if sources_root is None:
        return None
    for source_ref in _sorted_unique(operation.source_refs):
        relative_path = _python_orm_relative_path_from_source_ref(
            source_ref=source_ref,
            sources_root=sources_root,
        )
        if relative_path is not None:
            return relative_path
    return None


def _explicit_generated_relative_path(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    for payload in (
        operation.current,
        operation.semantic_change_projection or {},
        operation.extra,
    ):
        generated = mapping_value(payload.get("generated_materialization"))
        python_orm = mapping_value(generated.get("python_orm"))
        relative_path = optional_text(python_orm.get("relative_path"))
        if relative_path is not None:
            return relative_path
    return None


def _python_orm_relative_path_from_source_ref(
    *,
    source_ref: str,
    sources_root: str | None,
) -> str | None:
    normalized_source_ref = _normalized_relative_path(source_ref)
    if normalized_source_ref is None or not normalized_source_ref.endswith(".aware"):
        return None
    source_parts = normalized_source_ref.split("/")
    if "aware" in source_parts:
        source_parts = source_parts[source_parts.index("aware") + 1 :]
    python_path = "/".join(source_parts)[: -len(".aware")] + ".py"
    if sources_root is None or python_path.startswith(f"{sources_root}/"):
        return python_path
    return f"{sources_root}/{python_path}"


def _python_orm_relationship_context(
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> MetaPythonOrmRelationshipGeneratedMaterializationContext:
    sources_root = _python_orm_sources_root(
        package_name=context.package_name,
        sources_root=context.sources_root,
    )
    return MetaPythonOrmRelationshipGeneratedMaterializationContext(
        package_name=context.package_name,
        package_root=_python_orm_package_root(
            package_root=context.package_root,
            source_sources_root=context.sources_root,
            generated_sources_root=sources_root,
        ),
        sources_root=sources_root,
        target_language=context.target_language or "python",
    )


def _python_orm_package_root(
    *,
    package_root: str | None,
    source_sources_root: str | None,
    generated_sources_root: str | None,
) -> str | None:
    normalized_package_root = _normalized_path(package_root)
    if normalized_package_root is None:
        return None
    if normalized_package_root.endswith("/python"):
        return normalized_package_root
    if _is_authored_aware_sources_root(source_sources_root):
        return f"{normalized_package_root}/python"
    if generated_sources_root is not None and (
        _normalized_path(source_sources_root) == generated_sources_root
    ):
        return normalized_package_root
    return normalized_package_root


def _python_orm_sources_root(
    *,
    package_name: str | None,
    sources_root: str | None,
) -> str | None:
    normalized_sources_root = _normalized_path(sources_root)
    if not _is_authored_aware_sources_root(normalized_sources_root):
        return normalized_sources_root
    generated_root = _python_orm_sources_root_from_package_name(package_name)
    return generated_root or normalized_sources_root


def _python_orm_sources_root_from_package_name(
    package_name: str | None,
) -> str | None:
    normalized_package_name = optional_text(package_name)
    if normalized_package_name is None:
        return None
    package_base = normalized_package_name
    if package_base.endswith("-ontology"):
        package_base = package_base[: -len("-ontology")]
    package_base = package_base.replace("-", "_").strip("_")
    if not package_base:
        return None
    return f"aware_{package_base}_ontology"


def _is_authored_aware_sources_root(sources_root: str | None) -> bool:
    return sources_root is None or sources_root == "aware"


def _section_delta_relative_path(
    *,
    relative_path: str | None,
    sources_root: str | None,
) -> str | None:
    normalized_relative_path = _normalized_relative_path(relative_path)
    normalized_sources_root = _normalized_relative_path(sources_root)
    if (
        normalized_relative_path is not None
        and normalized_sources_root is not None
        and normalized_relative_path.startswith(f"{normalized_sources_root}/")
    ):
        return normalized_relative_path[len(normalized_sources_root) + 1 :]
    return normalized_relative_path


def _safe_relative_path(value: str) -> bool:
    parts = _normalized_relative_path(value)
    if parts is None:
        return False
    return not any(part == ".." for part in parts.split("/"))


def _code_language(value: str) -> CodeLanguage:
    try:
        return CodeLanguage(value)
    except ValueError:
        return CodeLanguage.python


def _normalized_path(value: str | None) -> str | None:
    text = optional_text(value)
    if text is None:
        return None
    return text.replace("\\", "/").strip().rstrip("/")


def _normalized_relative_path(value: str | None) -> str | None:
    text = _normalized_path(value)
    if text is None:
        return None
    return text.lstrip("/")


def _sorted_unique(values: Iterable[str | object]) -> tuple[str, ...]:
    return tuple(sorted({text for item in values for text in tuple_text(item)}))


def _sha256_digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _json_object(payload: Mapping[str, object]) -> JsonObject:
    return JsonObject(cast(Any, dict(payload)))


__all__ = [
    "META_PYTHON_ORM_RELATIONSHIP_ANCHOR_KEY",
    "META_PYTHON_ORM_RELATIONSHIP_EVIDENCE_ONLY_DIAGNOSTIC",
    "META_PYTHON_ORM_RELATIONSHIP_FIELD_SPAN_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_RELATIONSHIP_FIELD_TEXT_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_RELATIONSHIP_RENDERER_KEY",
    "META_PYTHON_ORM_RELATIONSHIP_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC",
    "MetaPythonOrmRelationshipGeneratedMaterializationContext",
    "MetaPythonOrmRelationshipGeneratedMaterializationDeltaEvidence",
    "generated_materialization_feature_results_from_relationship_config_typed_operation",
    "python_orm_generated_materialization_delta_from_relationship_config_typed_operation",
]
