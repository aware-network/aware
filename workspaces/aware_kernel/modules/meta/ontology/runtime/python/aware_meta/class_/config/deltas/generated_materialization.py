from __future__ import annotations

import ast
import keyword
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


META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_PROVIDER_KEY = "aware_meta"
META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_SEMANTIC_OWNER = "aware_meta.ocg"
META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_PRODUCT_INTENT = "python_orm_runtime"
META_PYTHON_ORM_CLASS_RENDERER_PROFILE = "orm_runtime"
META_PYTHON_ORM_CLASS_MATERIALIZATION_SOURCE = "ontology_orm_models"
META_PYTHON_ORM_CLASS_RENDERER_KEY = "python.orm.class"
META_PYTHON_ORM_CLASS_DESCRIPTION_ANCHOR_KEY = "python.orm.class.description_comment"
META_PYTHON_ORM_CLASS_CLASS_ANCHOR_KEY = "python.orm.class.class"
META_PYTHON_ORM_CLASS_EVIDENCE_ONLY_DIAGNOSTIC = (
    "meta_python_orm_class_generated_materialization_renderer_operation_evidence_only"
)
META_PYTHON_ORM_CLASS_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC = (
    "meta_python_orm_class_generated_materialization_target_relative_path_missing"
)
META_PYTHON_ORM_CLASS_DESCRIPTION_SPAN_MISSING_DIAGNOSTIC = (
    "meta_python_orm_class_description_generated_materialization_span_missing"
)
META_PYTHON_ORM_CLASS_DESCRIPTION_TEXT_MISSING_DIAGNOSTIC = (
    "meta_python_orm_class_description_generated_materialization_text_missing"
)
META_PYTHON_ORM_CLASS_STRUCTURAL_CREATE_POLICY_MISSING_DIAGNOSTIC = (
    "meta_python_orm_class_create_generated_materialization_policy_missing"
)
META_PYTHON_ORM_CLASS_STRUCTURAL_DELETE_POLICY_MISSING_DIAGNOSTIC = (
    "meta_python_orm_class_delete_generated_materialization_policy_missing"
)
META_PYTHON_ORM_CLASS_NOT_REQUIRED_REASON = (
    "meta_python_orm_class_generated_materialization_not_required"
)


@dataclass(frozen=True, slots=True)
class MetaPythonOrmClassGeneratedMaterializationContext:
    package_name: str | None = None
    package_root: str | None = None
    sources_root: str | None = None
    target_language: str = "python"
    renderer_profile: str = META_PYTHON_ORM_CLASS_RENDERER_PROFILE
    materialization_source: str = META_PYTHON_ORM_CLASS_MATERIALIZATION_SOURCE
    artifact_family: str = "ocg_language_materialization"
    artifact_role: str = "python_orm_model"


@dataclass(frozen=True, slots=True)
class MetaPythonOrmClassGeneratedMaterializationDeltaEvidence:
    delta_request: CodeGeneratedMaterializationDeltaRequest
    result: CodeGeneratedMaterializationDeltaResult


@dataclass(frozen=True, slots=True)
class _PythonOrmClassDescriptionDeltaEvidence:
    grammar_anchor_render_delta: ResolveCodeGrammarAnchorRenderDeltaRequest
    anchor: CodeGeneratedRendererAnchorRef
    content_text: str
    before_hash: str
    after_hash: str
    mode_reason: str


def generated_materialization_feature_results_from_class_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> tuple[MetaProviderDeltaGeneratedMaterializationFeatureResult, ...]:
    if operation.ontology_subject_kind != "class":
        return (
            MetaProviderDeltaGeneratedMaterializationFeatureResult.skipped(
                feature_key="class_config",
                operation=operation,
                reason=(
                    "meta_python_orm_class_generated_materialization_"
                    "subject_not_supported"
                ),
                event_refs=(
                    meta_provider_delta_world_change_event_key(operation=operation),
                ),
            ),
        )

    evidence = (
        python_orm_generated_materialization_delta_from_class_config_typed_operation(
            operation,
            context=_python_orm_class_context(context),
        )
    )
    return (
        MetaProviderDeltaGeneratedMaterializationFeatureResult.from_evidence(
            feature_key="class_config",
            operation=operation,
            delta_request=evidence.delta_request,
            result=evidence.result,
            reason="meta_python_orm_class_generated_materialization_evidence_built",
        ),
    )


def python_orm_generated_materialization_delta_from_class_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    *,
    context: MetaPythonOrmClassGeneratedMaterializationContext | None = None,
) -> MetaPythonOrmClassGeneratedMaterializationDeltaEvidence:
    resolved_context = context or MetaPythonOrmClassGeneratedMaterializationContext()
    plugin_evidence = _python_orm_class_plugin_delta_evidence(
        operation=operation,
        context=resolved_context,
    )
    if plugin_evidence is not None:
        return plugin_evidence
    event_key = meta_provider_delta_world_change_event_key(operation=operation)
    target = _target_ref(operation=operation, context=resolved_context)
    request = CodeGeneratedMaterializationDeltaRequest(
        provider_key=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        package_name=resolved_context.package_name,
        package_root=resolved_context.package_root,
        sources_root=resolved_context.sources_root,
        product_intent=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_PRODUCT_INTENT,
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
                    "aware_meta.python_orm.class.generated_materialization."
                    f"{operation.operation_key}"
                ),
                event_key=event_key,
                target=target,
                policy_key="aware_meta.python_orm.class.description",
                renderer_key=META_PYTHON_ORM_CLASS_RENDERER_KEY,
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.provider_delta."
                            "python_orm_class_generated_materialization_action"
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
                    "aware_meta.provider_delta."
                    "python_orm_class_generated_materialization_delta_request"
                ),
                "renderer_profile": resolved_context.renderer_profile,
                "materialization_source": resolved_context.materialization_source,
            }
        ),
    )
    result = _python_orm_class_generated_materialization_result(
        operation=operation,
        context=resolved_context,
        event_key=event_key,
        target=target,
    )
    return MetaPythonOrmClassGeneratedMaterializationDeltaEvidence(
        delta_request=request,
        result=result,
    )


def _python_orm_class_plugin_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmClassGeneratedMaterializationContext,
) -> MetaPythonOrmClassGeneratedMaterializationDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "class"
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
    return MetaPythonOrmClassGeneratedMaterializationDeltaEvidence(
        delta_request=render_result.delta_request,
        result=render_result.result,
    )


def _language_delta_context(
    context: MetaPythonOrmClassGeneratedMaterializationContext,
) -> MetaLanguageGeneratedMaterializationDeltaContext:
    return MetaLanguageGeneratedMaterializationDeltaContext(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        target_language=context.target_language,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        product_intent=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_PRODUCT_INTENT,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
    )


def _meta_plugin_code_language(value: str) -> MetaPluginCodeLanguage:
    try:
        return MetaPluginCodeLanguage(value)
    except ValueError:
        return MetaPluginCodeLanguage.python


def _python_orm_class_generated_materialization_result(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmClassGeneratedMaterializationContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
) -> CodeGeneratedMaterializationDeltaResult:
    if _class_structural_create_required(operation=operation):
        delta_evidence = _python_orm_class_create_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    elif _class_structural_delete_required(operation=operation):
        delta_evidence = _python_orm_class_delete_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    elif _class_description_changed(operation=operation):
        delta_evidence = _python_orm_class_description_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    else:
        return CodeGeneratedMaterializationDeltaResult(
            provider_key=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_PROVIDER_KEY,
            semantic_owner=(
                META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
            ),
            available=True,
            mode=CodeGeneratedMaterializationDeltaMode.not_required,
            skipped_targets=[
                CodeGeneratedMaterializationSkippedTarget(
                    target=target,
                    reason=META_PYTHON_ORM_CLASS_NOT_REQUIRED_REASON,
                    event_refs=[event_key],
                )
            ],
        )
    has_delta = delta_evidence is not None
    diagnostics = (
        ()
        if has_delta
        else _python_orm_class_guarded_delta_diagnostics(
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
        operation_key=f"aware_meta.python_orm.class:{operation.operation_key}",
        kind=(
            CodeGeneratedRendererDeltaOperationKind.replace_anchor
            if has_delta
            else CodeGeneratedRendererDeltaOperationKind.fallback_full_render
        ),
        target=target,
        anchor=(
            delta_evidence.anchor
            if delta_evidence is not None
            else _anchor_ref(operation=operation, context=context)
        ),
        renderer_key=META_PYTHON_ORM_CLASS_RENDERER_KEY,
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
                    "aware_meta.provider_delta." "python_orm_class_renderer_operation"
                ),
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "mode_reason": (
                    delta_evidence.mode_reason
                    if has_delta
                    else "python_orm_class_guarded_delta_missing"
                ),
            }
        ),
    )
    entry = CodeGeneratedMaterializationDeltaEntry(
        entry_key=f"aware_meta.python_orm.class:{operation.operation_key}",
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
                    "aware_meta.provider_delta."
                    "python_orm_class_generated_materialization_delta_entry"
                ),
                "operation_key": operation.operation_key,
                "package_delta_emitted": False,
                "section_delta_emitted": False,
                "grammar_anchor_render_delta_emitted": has_delta,
            }
        ),
    )
    return CodeGeneratedMaterializationDeltaResult(
        provider_key=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        available=True,
        mode=entry_mode,
        entries=[entry],
        diagnostics=list(diagnostics),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_class_generated_materialization_delta_result"
                ),
                "operation_key": operation.operation_key,
                "renderer_operation_count": 1,
                "package_delta_emitted": False,
                "section_delta_emitted": False,
                "grammar_anchor_render_delta_emitted": has_delta,
            }
        ),
    )


def _python_orm_class_description_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmClassGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmClassDescriptionDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "class"
        or operation.operation_family != "update"
        or target.relative_path is None
    ):
        return None
    class_name = _class_name(operation=operation)
    replacement_text = _python_class_docstring_text(_current_description(operation))
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if class_name is None or replacement_text is None or source_state is None:
        return None
    relative_path, source_text = source_state
    span = _python_class_description_span(
        source_text=source_text,
        class_name=class_name,
        expected_description=_baseline_description(operation),
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
        provider_key=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        subject_kind="class_config",
        subject_type="ClassConfig",
        semantic_key=operation.semantic_key,
        object_key=_class_fqn(operation=operation),
        field_name="description",
        field_path=f"{class_name}.description",
        class_fqn=_class_fqn(operation=operation),
        class_name=class_name,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_class_description_graph_selector"
                ),
                "operation_key": operation.operation_key,
                "class_name": class_name,
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
                        "aware_meta.python_orm.class.description:"
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
                                "aware_meta.provider_delta."
                                "python_orm_class_description_replacement"
                            ),
                            "operation_key": operation.operation_key,
                            "class_name": class_name,
                            "renderer_key": META_PYTHON_ORM_CLASS_RENDERER_KEY,
                        }
                    ),
                )
            ],
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta."
                        "python_orm_class_description_grammar_anchor_render_delta"
                    ),
                    "operation_key": operation.operation_key,
                    "target_kind": CodeGrammarAnchorRenderTargetKind.text_span.value,
                    "renderer_key": META_PYTHON_ORM_CLASS_RENDERER_KEY,
                    "renderer_profile": context.renderer_profile,
                }
            ),
        )
    )
    return _PythonOrmClassDescriptionDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        anchor=_anchor_ref(operation=operation, context=context),
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
        mode_reason="python_orm_class_description_grammar_anchor_render_delta_ready",
    )


def _python_orm_class_create_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmClassGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmClassDescriptionDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "class"
        or operation.operation_family != "create"
        or target.relative_path is None
    ):
        return None
    class_name = _class_name(operation=operation)
    replacement_text = _python_class_text(operation=operation)
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if class_name is None or replacement_text is None or source_state is None:
        return None
    relative_path, source_text = source_state
    span = _python_class_create_insert_span(
        source_text=source_text,
        class_name=class_name,
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
        provider_key=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        subject_kind="class_config",
        subject_type="ClassConfig",
        semantic_key=operation.semantic_key,
        object_key=_class_fqn(operation=operation),
        field_name="class",
        field_path=class_name,
        class_fqn=_class_fqn(operation=operation),
        class_name=class_name,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_class_create_graph_selector"
                ),
                "operation_key": operation.operation_key,
                "class_name": class_name,
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
                        "aware_meta.python_orm.class.create:"
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
                                "aware_meta.provider_delta."
                                "python_orm_class_create_replacement"
                            ),
                            "operation_key": operation.operation_key,
                            "class_name": class_name,
                            "renderer_key": META_PYTHON_ORM_CLASS_RENDERER_KEY,
                        }
                    ),
                )
            ],
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta."
                        "python_orm_class_create_grammar_anchor_render_delta"
                    ),
                    "operation_key": operation.operation_key,
                    "target_kind": CodeGrammarAnchorRenderTargetKind.text_span.value,
                    "renderer_key": META_PYTHON_ORM_CLASS_RENDERER_KEY,
                    "renderer_profile": context.renderer_profile,
                }
            ),
        )
    )
    return _PythonOrmClassDescriptionDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        anchor=_class_anchor_ref(operation=operation, context=context),
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
        mode_reason="python_orm_class_create_grammar_anchor_render_delta_ready",
    )


def _python_orm_class_delete_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmClassGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmClassDescriptionDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "class"
        or operation.operation_family != "delete"
        or target.relative_path is None
    ):
        return None
    class_name = _class_name(operation=operation)
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if class_name is None or source_state is None:
        return None
    relative_path, source_text = source_state
    span = _python_class_delete_span(source_text=source_text, class_name=class_name)
    if span is None:
        return None
    byte_start, byte_end, before_text = span
    replacement_text = ""
    before_hash = _sha256_digest(before_text)
    after_hash = _sha256_digest(replacement_text)
    source_hash = _sha256_digest(source_text)
    target_key = target.target_key
    if target_key is None:
        return None
    graph_selector = CodeGraphFieldSelector(
        provider_key=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        subject_kind="class_config",
        subject_type="ClassConfig",
        semantic_key=operation.semantic_key,
        object_key=_class_fqn(operation=operation),
        field_name="class",
        field_path=class_name,
        class_fqn=_class_fqn(operation=operation),
        class_name=class_name,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_class_delete_graph_selector"
                ),
                "operation_key": operation.operation_key,
                "class_name": class_name,
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
                        "aware_meta.python_orm.class.delete:"
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
                                "aware_meta.provider_delta."
                                "python_orm_class_delete_replacement"
                            ),
                            "operation_key": operation.operation_key,
                            "class_name": class_name,
                            "renderer_key": META_PYTHON_ORM_CLASS_RENDERER_KEY,
                        }
                    ),
                )
            ],
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta."
                        "python_orm_class_delete_grammar_anchor_render_delta"
                    ),
                    "operation_key": operation.operation_key,
                    "target_kind": CodeGrammarAnchorRenderTargetKind.text_span.value,
                    "renderer_key": META_PYTHON_ORM_CLASS_RENDERER_KEY,
                    "renderer_profile": context.renderer_profile,
                }
            ),
        )
    )
    return _PythonOrmClassDescriptionDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        anchor=_class_anchor_ref(operation=operation, context=context),
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
        mode_reason="python_orm_class_delete_grammar_anchor_render_delta_ready",
    )


def _python_orm_class_guarded_delta_diagnostics(
    *,
    operation: MetaProviderDeltaTypedOperation,
    target: CodeGeneratedMaterializationTargetRef,
) -> tuple[str, ...]:
    diagnostics = [META_PYTHON_ORM_CLASS_EVIDENCE_ONLY_DIAGNOSTIC]
    if target.relative_path is None:
        diagnostics.append(
            META_PYTHON_ORM_CLASS_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC
        )
    if _class_structural_create_required(operation=operation):
        diagnostics.append(
            META_PYTHON_ORM_CLASS_STRUCTURAL_CREATE_POLICY_MISSING_DIAGNOSTIC
        )
    elif _class_structural_delete_required(operation=operation):
        diagnostics.append(
            META_PYTHON_ORM_CLASS_STRUCTURAL_DELETE_POLICY_MISSING_DIAGNOSTIC
        )
    elif _current_description(operation) is None:
        diagnostics.append(META_PYTHON_ORM_CLASS_DESCRIPTION_TEXT_MISSING_DIAGNOSTIC)
    else:
        diagnostics.append(META_PYTHON_ORM_CLASS_DESCRIPTION_SPAN_MISSING_DIAGNOSTIC)
    return tuple(dict.fromkeys(diagnostics))


def _python_class_description_span(
    *,
    source_text: str,
    class_name: str,
    expected_description: str | None,
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
    body = tuple(class_node.body)
    if not body:
        return None
    first_body_node = body[0]
    if _is_python_docstring_node(first_body_node):
        span = _node_line_span(source_text=source_text, node=first_body_node)
        if span is None:
            return None
        byte_start, byte_end, before_text = span
        if expected_description is not None and before_text != (
            _python_class_docstring_text(expected_description)
        ):
            return None
        return byte_start, byte_end, before_text
    insert_at = _node_start_byte(source_text=source_text, node=first_body_node)
    if insert_at is None:
        return None
    if expected_description is not None:
        return None
    return insert_at, insert_at, ""


def _python_class_create_insert_span(
    *,
    source_text: str,
    class_name: str,
) -> tuple[int, int, str] | None:
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return None
    if any(
        isinstance(node, ast.ClassDef) and node.name == class_name
        for node in ast.walk(tree)
    ):
        return None
    byte_end = len(source_text.encode("utf-8"))
    return byte_end, byte_end, ""


def _python_class_delete_span(
    *,
    source_text: str,
    class_name: str,
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
    lineno_value = getattr(class_node, "lineno", None)
    end_lineno_value = getattr(class_node, "end_lineno", None)
    if not isinstance(lineno_value, int) or not isinstance(end_lineno_value, int):
        return None
    lines = source_text.splitlines(keepends=True)
    start_index = lineno_value - 1
    end_index = end_lineno_value
    if start_index < 0 or end_index <= start_index or start_index >= len(lines):
        return None
    if not "".join(lines[end_index:]).strip():
        while start_index > 0 and not lines[start_index - 1].strip():
            start_index -= 1
    byte_start = len("".join(lines[:start_index]).encode("utf-8"))
    byte_end = len("".join(lines[:end_index]).encode("utf-8"))
    before_text = source_text.encode("utf-8")[byte_start:byte_end].decode("utf-8")
    return byte_start, byte_end, before_text


def _is_python_docstring_node(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


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


def _node_start_byte(*, source_text: str, node: ast.AST) -> int | None:
    lineno_value = getattr(node, "lineno", None)
    if not isinstance(lineno_value, int):
        return None
    lines = source_text.splitlines(keepends=True)
    lineno = lineno_value
    if lineno <= 0 or lineno > len(lines):
        return None
    return len("".join(lines[: lineno - 1]).encode("utf-8"))


def _python_class_docstring_text(value: str | None) -> str | None:
    description = optional_text(value)
    if description is None:
        return None
    return f'    """{_python_docstring_line(description)}"""\n'


def _python_docstring_line(value: str) -> str:
    return " ".join(value.replace('"""', '\\"\\"\\"').split())


def _python_class_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    class_name = _class_name(operation=operation)
    if (
        class_name is None
        or not class_name.isidentifier()
        or keyword.iskeyword(class_name)
    ):
        return None
    lines = ["", "", f"class {class_name}(ORMModel):"]
    description = _current_description(operation)
    if description is not None:
        lines.append(f'    """{_python_docstring_line(description)}"""')
    else:
        lines.append("    pass")
    return "\n".join(lines) + "\n"


def _python_orm_generated_source_state(
    *,
    context: MetaPythonOrmClassGeneratedMaterializationContext,
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
    if source_root is not None and not relative_path.startswith(f"{source_root}/"):
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
    context: MetaPythonOrmClassGeneratedMaterializationContext,
) -> CodeGeneratedMaterializationTargetRef:
    class_fqn = _class_fqn(operation=operation)
    class_name = _class_name(operation=operation)
    target_key = ".".join(
        part
        for part in (
            context.package_name,
            context.materialization_source,
            class_fqn,
            "python_orm_model",
        )
        if part
    )
    return CodeGeneratedMaterializationTargetRef(
        target_key=target_key,
        provider_key=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        target_language=context.target_language,
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        renderer_key=META_PYTHON_ORM_CLASS_RENDERER_KEY,
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
                "source": "aware_meta.provider_delta.python_orm_class_target_ref",
                "operation_key": operation.operation_key,
                "class_fqn": class_fqn,
                "class_name": class_name,
            }
        ),
    )


def _anchor_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmClassGeneratedMaterializationContext,
) -> CodeGeneratedRendererAnchorRef:
    class_fqn = _class_fqn(operation=operation)
    class_name = _class_name(operation=operation)
    anchor_path = ".".join(part for part in (class_name, "description") if part)
    return CodeGeneratedRendererAnchorRef(
        anchor_key=META_PYTHON_ORM_CLASS_DESCRIPTION_ANCHOR_KEY,
        anchor_path=anchor_path,
        anchor_role="class_description",
        renderer_key=META_PYTHON_ORM_CLASS_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        target_language=context.target_language,
        section_type="class",
        segment_name="description_comment",
        graph_selector=_json_object(
            {
                "provider_key": (
                    META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_PROVIDER_KEY
                ),
                "semantic_owner": (
                    META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
                ),
                "class_fqn": class_fqn,
                "class_name": class_name,
                "field_name": "description",
                "field_path": anchor_path,
            }
        ),
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.python_orm_class_anchor",
                "operation_key": operation.operation_key,
                "semantic_key": operation.semantic_key,
            }
        ),
    )


def _class_anchor_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmClassGeneratedMaterializationContext,
) -> CodeGeneratedRendererAnchorRef:
    class_fqn = _class_fqn(operation=operation)
    class_name = _class_name(operation=operation)
    return CodeGeneratedRendererAnchorRef(
        anchor_key=META_PYTHON_ORM_CLASS_CLASS_ANCHOR_KEY,
        anchor_path=class_name,
        anchor_role="class",
        renderer_key=META_PYTHON_ORM_CLASS_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        target_language=context.target_language,
        section_type="class",
        segment_name="class",
        graph_selector=_json_object(
            {
                "provider_key": (
                    META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_PROVIDER_KEY
                ),
                "semantic_owner": (
                    META_PYTHON_ORM_CLASS_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
                ),
                "class_fqn": class_fqn,
                "class_name": class_name,
                "field_name": "class",
                "field_path": class_name,
            }
        ),
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.python_orm_class_class_anchor",
                "operation_key": operation.operation_key,
                "semantic_key": operation.semantic_key,
            }
        ),
    )


def _class_structural_create_required(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    return (
        operation.ontology_subject_kind == "class"
        and operation.operation_family == "create"
    )


def _class_structural_delete_required(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    return (
        operation.ontology_subject_kind == "class"
        and operation.operation_family == "delete"
    )


def _class_description_changed(*, operation: MetaProviderDeltaTypedOperation) -> bool:
    if (
        operation.ontology_subject_kind != "class"
        or operation.operation_family != "update"
    ):
        return False
    current_description = _current_description(operation)
    if current_description is None:
        return False
    return current_description != _baseline_description(operation)


def _current_description(operation: MetaProviderDeltaTypedOperation) -> str | None:
    signature = _class_signature(payload=operation.current)
    return optional_text(signature.get("description")) or optional_text(
        operation.current.get("description")
    )


def _baseline_description(operation: MetaProviderDeltaTypedOperation) -> str | None:
    signature = _class_signature(payload=operation.baseline)
    return optional_text(signature.get("description")) or optional_text(
        mapping_value(operation.baseline.get("object")).get("description")
    )


def _class_signature(*, payload: Mapping[str, object]) -> Mapping[str, object]:
    signature = mapping_value(payload.get("class_signature"))
    if signature:
        return signature
    nested_payload = mapping_value(payload.get("payload"))
    signature = mapping_value(nested_payload.get("class_signature"))
    if signature:
        return signature
    object_payload = mapping_value(payload.get("object"))
    signature = mapping_value(object_payload.get("class_signature"))
    if signature:
        return signature
    if object_payload:
        return object_payload
    return payload


def _class_name(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return (
        optional_text(operation.current.get("class_name"))
        or optional_text(operation.current.get("name"))
        or optional_text(operation.current.get("entity_name"))
        or optional_text(_class_signature(payload=operation.current).get("class_name"))
        or optional_text(_class_signature(payload=operation.current).get("name"))
        or _class_name_from_semantic_key(operation.semantic_key)
    )


def _class_fqn(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return (
        optional_text(operation.current.get("class_fqn"))
        or optional_text(operation.current.get("class_key"))
        or optional_text(_class_signature(payload=operation.current).get("class_fqn"))
        or optional_text(_class_signature(payload=operation.baseline).get("class_fqn"))
        or _class_fqn_from_semantic_key(operation.semantic_key)
        or _class_name(operation=operation)
    )


def _class_name_from_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.class:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        return raw.rsplit(".", maxsplit=1)[-1] or None
    marker = "/node:"
    if marker in semantic_key:
        node_key = semantic_key.split(marker, maxsplit=1)[-1].split(
            "/",
            maxsplit=1,
        )[0]
        return node_key.rsplit(".", maxsplit=1)[-1] or None
    return None


def _class_fqn_from_semantic_key(semantic_key: str) -> str | None:
    marker = "/node:"
    if marker not in semantic_key:
        return None
    return semantic_key.split(marker, maxsplit=1)[-1].split("/", maxsplit=1)[0]


def _generated_relative_path(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmClassGeneratedMaterializationContext,
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


def _python_orm_class_context(
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> MetaPythonOrmClassGeneratedMaterializationContext:
    sources_root = _python_orm_sources_root(
        package_name=context.package_name,
        sources_root=context.sources_root,
    )
    return MetaPythonOrmClassGeneratedMaterializationContext(
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
    if normalized_package_root.endswith("/python/orm_runtime"):
        return normalized_package_root
    if _is_authored_aware_sources_root(source_sources_root):
        if normalized_package_root.endswith("/python"):
            return f"{normalized_package_root}/orm_runtime"
        return f"{normalized_package_root}/python/orm_runtime"
    if normalized_package_root.endswith("/python"):
        return normalized_package_root
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
    normalized_sources_root = _normalized_path(sources_root)
    return (
        normalized_sources_root is None
        or normalized_sources_root == "aware"
        or normalized_sources_root.endswith("/aware")
    )


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
    "META_PYTHON_ORM_CLASS_CLASS_ANCHOR_KEY",
    "META_PYTHON_ORM_CLASS_DESCRIPTION_ANCHOR_KEY",
    "META_PYTHON_ORM_CLASS_DESCRIPTION_SPAN_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_CLASS_DESCRIPTION_TEXT_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_CLASS_EVIDENCE_ONLY_DIAGNOSTIC",
    "META_PYTHON_ORM_CLASS_RENDERER_KEY",
    "META_PYTHON_ORM_CLASS_STRUCTURAL_DELETE_POLICY_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_CLASS_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC",
    "MetaPythonOrmClassGeneratedMaterializationContext",
    "MetaPythonOrmClassGeneratedMaterializationDeltaEvidence",
    "generated_materialization_feature_results_from_class_config_typed_operation",
    "python_orm_generated_materialization_delta_from_class_config_typed_operation",
]
