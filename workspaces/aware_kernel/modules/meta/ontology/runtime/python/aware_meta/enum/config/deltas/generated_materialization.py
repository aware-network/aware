from __future__ import annotations

import ast
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from hashlib import sha256
import keyword
import json
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


META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PROVIDER_KEY = "aware_meta"
META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER = "aware_meta.ocg"
META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PRODUCT_INTENT = "python_orm_runtime"
META_PYTHON_ORM_ENUM_RENDERER_PROFILE = "orm_runtime"
META_PYTHON_ORM_ENUM_MATERIALIZATION_SOURCE = "ontology_orm_models"
META_PYTHON_ORM_ENUM_RENDERER_KEY = "python.orm.enum"
META_PYTHON_ORM_ENUM_CLASS_ANCHOR_KEY = "python.orm.enum.class"
META_PYTHON_ORM_ENUM_DESCRIPTION_ANCHOR_KEY = "python.orm.enum.description_comment"
META_PYTHON_ORM_ENUM_OPTION_LINE_ANCHOR_KEY = "python.orm.enum.option_line"
META_PYTHON_ORM_ENUM_EVIDENCE_ONLY_DIAGNOSTIC = (
    "meta_python_orm_enum_generated_materialization_renderer_operation_evidence_only"
)
META_PYTHON_ORM_ENUM_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC = (
    "meta_python_orm_enum_generated_materialization_target_relative_path_missing"
)
META_PYTHON_ORM_ENUM_DESCRIPTION_SPAN_MISSING_DIAGNOSTIC = (
    "meta_python_orm_enum_description_generated_materialization_span_missing"
)
META_PYTHON_ORM_ENUM_DESCRIPTION_TEXT_MISSING_DIAGNOSTIC = (
    "meta_python_orm_enum_description_generated_materialization_text_missing"
)
META_PYTHON_ORM_ENUM_OPTION_LINE_SPAN_MISSING_DIAGNOSTIC = (
    "meta_python_orm_enum_option_line_generated_materialization_span_missing"
)
META_PYTHON_ORM_ENUM_OPTION_LINE_TEXT_MISSING_DIAGNOSTIC = (
    "meta_python_orm_enum_option_line_generated_materialization_text_missing"
)
META_PYTHON_ORM_ENUM_OPTION_REORDER_POLICY_MISSING_DIAGNOSTIC = (
    "meta_python_orm_enum_option_position_generated_materialization_"
    "requires_reorder_policy"
)
META_PYTHON_ORM_ENUM_OPTION_DELETE_POLICY_MISSING_DIAGNOSTIC = (
    "meta_python_orm_enum_option_delete_generated_materialization_"
    "requires_delete_policy"
)
META_PYTHON_ORM_ENUM_STRUCTURAL_CREATE_POLICY_MISSING_DIAGNOSTIC = (
    "meta_python_orm_enum_create_generated_materialization_"
    "requires_structural_policy"
)
META_PYTHON_ORM_ENUM_STRUCTURAL_DELETE_POLICY_MISSING_DIAGNOSTIC = (
    "meta_python_orm_enum_delete_generated_materialization_"
    "requires_structural_policy"
)
META_PYTHON_ORM_ENUM_NOT_REQUIRED_REASON = (
    "meta_python_orm_enum_generated_materialization_not_required"
)


@dataclass(frozen=True, slots=True)
class MetaPythonOrmEnumGeneratedMaterializationContext:
    package_name: str | None = None
    package_root: str | None = None
    sources_root: str | None = None
    target_language: str = "python"
    renderer_profile: str = META_PYTHON_ORM_ENUM_RENDERER_PROFILE
    materialization_source: str = META_PYTHON_ORM_ENUM_MATERIALIZATION_SOURCE
    artifact_family: str = "ocg_language_materialization"
    artifact_role: str = "python_orm_model"


@dataclass(frozen=True, slots=True)
class MetaPythonOrmEnumGeneratedMaterializationDeltaEvidence:
    delta_request: CodeGeneratedMaterializationDeltaRequest
    result: CodeGeneratedMaterializationDeltaResult


@dataclass(frozen=True, slots=True)
class _PythonOrmEnumDescriptionDeltaEvidence:
    grammar_anchor_render_delta: ResolveCodeGrammarAnchorRenderDeltaRequest
    anchor: CodeGeneratedRendererAnchorRef
    content_text: str
    before_hash: str
    after_hash: str
    mode_reason: str


@dataclass(frozen=True, slots=True)
class _PythonEnumOptionAssignment:
    name: str
    byte_start: int
    byte_end: int
    line_text: str


def generated_materialization_feature_results_from_enum_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> tuple[MetaProviderDeltaGeneratedMaterializationFeatureResult, ...]:
    if operation.ontology_subject_kind not in {"enum", "enum_option"}:
        return (
            MetaProviderDeltaGeneratedMaterializationFeatureResult.skipped(
                feature_key="enum_config",
                operation=operation,
                reason=(
                    "meta_python_orm_enum_generated_materialization_"
                    "subject_not_supported"
                ),
                event_refs=(
                    meta_provider_delta_world_change_event_key(operation=operation),
                ),
            ),
        )

    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            operation,
            context=_python_orm_enum_context(context),
        )
    )
    return (
        MetaProviderDeltaGeneratedMaterializationFeatureResult.from_evidence(
            feature_key="enum_config",
            operation=operation,
            delta_request=evidence.delta_request,
            result=evidence.result,
            reason="meta_python_orm_enum_generated_materialization_evidence_built",
        ),
    )


def python_orm_generated_materialization_delta_from_enum_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    *,
    context: MetaPythonOrmEnumGeneratedMaterializationContext | None = None,
    allow_language_plugin: bool = True,
    language_plugin_delta_renderer: str | None = None,
) -> MetaPythonOrmEnumGeneratedMaterializationDeltaEvidence:
    resolved_context = context or MetaPythonOrmEnumGeneratedMaterializationContext()
    if allow_language_plugin:
        plugin_evidence = _python_orm_enum_plugin_delta_evidence(
            operation=operation,
            context=resolved_context,
        )
        if plugin_evidence is not None:
            return plugin_evidence
    event_key = meta_provider_delta_world_change_event_key(operation=operation)
    target = _target_ref(operation=operation, context=resolved_context)
    request = CodeGeneratedMaterializationDeltaRequest(
        provider_key=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        package_name=resolved_context.package_name,
        package_root=resolved_context.package_root,
        sources_root=resolved_context.sources_root,
        product_intent=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PRODUCT_INTENT,
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
                    "aware_meta.python_orm.enum.generated_materialization."
                    f"{operation.operation_key}"
                ),
                event_key=event_key,
                target=target,
                policy_key="aware_meta.python_orm.enum.description",
                renderer_key=META_PYTHON_ORM_ENUM_RENDERER_KEY,
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.provider_delta."
                            "python_orm_enum_generated_materialization_action"
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
                    "python_orm_enum_generated_materialization_delta_request"
                ),
                "renderer_profile": resolved_context.renderer_profile,
                "materialization_source": resolved_context.materialization_source,
                **_language_plugin_metadata(language_plugin_delta_renderer),
            }
        ),
    )
    result = _python_orm_enum_generated_materialization_result(
        operation=operation,
        context=resolved_context,
        event_key=event_key,
        target=target,
        language_plugin_delta_renderer=language_plugin_delta_renderer,
    )
    return MetaPythonOrmEnumGeneratedMaterializationDeltaEvidence(
        delta_request=request,
        result=result,
    )


def _python_orm_enum_plugin_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
) -> MetaPythonOrmEnumGeneratedMaterializationDeltaEvidence | None:
    if operation.ontology_subject_kind not in {"enum", "enum_option"}:
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
    return MetaPythonOrmEnumGeneratedMaterializationDeltaEvidence(
        delta_request=render_result.delta_request,
        result=render_result.result,
    )


def _language_delta_context(
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
) -> MetaLanguageGeneratedMaterializationDeltaContext:
    return MetaLanguageGeneratedMaterializationDeltaContext(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        target_language=context.target_language,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        product_intent=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PRODUCT_INTENT,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
    )


def _meta_plugin_code_language(value: str) -> MetaPluginCodeLanguage:
    try:
        return MetaPluginCodeLanguage(value)
    except ValueError:
        return MetaPluginCodeLanguage.python


def _python_orm_enum_generated_materialization_result(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
    language_plugin_delta_renderer: str | None = None,
) -> CodeGeneratedMaterializationDeltaResult:
    if _enum_structural_create_required(operation=operation):
        delta_evidence = _python_orm_enum_create_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    elif _enum_structural_delete_required(operation=operation):
        delta_evidence = _python_orm_enum_delete_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    elif _enum_description_changed(operation=operation):
        delta_evidence = _python_orm_enum_description_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    elif _enum_option_create_required(operation=operation):
        delta_evidence = _python_orm_enum_option_create_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    elif _enum_option_delete_required(operation=operation):
        delta_evidence = _python_orm_enum_option_delete_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    elif _enum_option_position_changed(operation=operation):
        delta_evidence = _python_orm_enum_option_reorder_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    else:
        return CodeGeneratedMaterializationDeltaResult(
            provider_key=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
            semantic_owner=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
            available=True,
            mode=CodeGeneratedMaterializationDeltaMode.not_required,
            skipped_targets=[
                CodeGeneratedMaterializationSkippedTarget(
                    target=target,
                    reason=META_PYTHON_ORM_ENUM_NOT_REQUIRED_REASON,
                    event_refs=[event_key],
                )
            ],
        )

    has_delta = delta_evidence is not None
    diagnostics = (
        ()
        if has_delta
        else _python_orm_enum_guarded_delta_diagnostics(
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
        operation_key=f"aware_meta.python_orm.enum:{operation.operation_key}",
        kind=(
            CodeGeneratedRendererDeltaOperationKind.replace_anchor
            if has_delta
            else CodeGeneratedRendererDeltaOperationKind.fallback_full_render
        ),
        target=target,
        anchor=(
            delta_evidence.anchor
            if delta_evidence is not None
            else (_anchor_ref(operation=operation, context=context))
        ),
        renderer_key=META_PYTHON_ORM_ENUM_RENDERER_KEY,
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
                    "aware_meta.provider_delta." "python_orm_enum_renderer_operation"
                ),
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "mode_reason": (
                    delta_evidence.mode_reason
                    if delta_evidence is not None
                    else "python_orm_enum_guarded_delta_missing"
                ),
                **_language_plugin_metadata(language_plugin_delta_renderer),
            }
        ),
    )
    entry = CodeGeneratedMaterializationDeltaEntry(
        entry_key=f"aware_meta.python_orm.enum:{operation.operation_key}",
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
                    "python_orm_enum_generated_materialization_delta_entry"
                ),
                "operation_key": operation.operation_key,
                "package_delta_emitted": False,
                "section_delta_emitted": False,
                "grammar_anchor_render_delta_emitted": has_delta,
                **_language_plugin_metadata(language_plugin_delta_renderer),
            }
        ),
    )
    return CodeGeneratedMaterializationDeltaResult(
        provider_key=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        available=True,
        mode=entry_mode,
        entries=[entry],
        diagnostics=list(diagnostics),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_enum_generated_materialization_delta_result"
                ),
                "operation_key": operation.operation_key,
                "renderer_operation_count": 1,
                "package_delta_emitted": False,
                "section_delta_emitted": False,
                "grammar_anchor_render_delta_emitted": has_delta,
                **_language_plugin_metadata(language_plugin_delta_renderer),
            }
        ),
    )


def _python_orm_enum_description_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmEnumDescriptionDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "enum"
        or operation.operation_family != "update"
        or target.relative_path is None
    ):
        return None
    enum_name = _enum_name(operation=operation)
    replacement_text = _python_enum_docstring_text(_current_description(operation))
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if enum_name is None or replacement_text is None or source_state is None:
        return None
    relative_path, source_text = source_state
    span = _python_enum_description_span(
        source_text=source_text,
        enum_name=enum_name,
        expected_description=_baseline_description(operation),
    )
    if span is None:
        return None
    byte_start, byte_end, before_text = span
    before_hash = _sha256_digest(before_text)
    after_hash = _sha256_digest(replacement_text)
    source_hash = _sha256_digest(source_text)
    graph_selector = CodeGraphFieldSelector(
        provider_key=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        subject_kind="enum_config",
        subject_type="EnumConfig",
        semantic_key=operation.semantic_key,
        object_key=_enum_fqn(operation=operation),
        field_name="description",
        field_path=f"{enum_name}.description",
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_enum_description_graph_selector"
                ),
                "operation_key": operation.operation_key,
                "enum_fqn": _enum_fqn(operation=operation),
                "enum_name": enum_name,
            }
        ),
    )
    grammar_anchor_render_delta = _python_orm_enum_text_span_render_delta(
        operation=operation,
        context=context,
        target=target,
        relative_path=relative_path,
        source_hash=source_hash,
        byte_start=byte_start,
        byte_end=byte_end,
        before_text=before_text,
        replacement_text=replacement_text,
        graph_selector=graph_selector,
        event_key=event_key,
        replacement_key=(
            "aware_meta.python_orm.enum.description:" f"{operation.operation_key}"
        ),
        replacement_metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_enum_description_replacement"
                ),
                "span_target_source": (
                    "aware_meta.provider_delta."
                    "python_orm_enum_description_span_target"
                ),
                "operation_key": operation.operation_key,
                "enum_name": enum_name,
                "renderer_key": META_PYTHON_ORM_ENUM_RENDERER_KEY,
            }
        ),
        delta_source=(
            "aware_meta.provider_delta."
            "python_orm_enum_description_grammar_anchor_render_delta"
        ),
    )
    if grammar_anchor_render_delta is None:
        return None
    return _PythonOrmEnumDescriptionDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        anchor=_anchor_ref(operation=operation, context=context),
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
        mode_reason="python_orm_enum_description_grammar_anchor_render_delta_ready",
    )


def _python_orm_enum_create_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmEnumDescriptionDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "enum"
        or operation.operation_family != "create"
        or target.relative_path is None
    ):
        return None
    enum_name = _enum_name(operation=operation)
    replacement_text = _python_enum_class_text(operation=operation)
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if enum_name is None or replacement_text is None or source_state is None:
        return None
    relative_path, source_text = source_state
    span = _python_enum_create_insert_span(
        source_text=source_text,
        enum_name=enum_name,
    )
    if span is None:
        return None
    byte_start, byte_end, before_text = span
    before_hash = _sha256_digest(before_text)
    after_hash = _sha256_digest(replacement_text)
    source_hash = _sha256_digest(source_text)
    graph_selector = CodeGraphFieldSelector(
        provider_key=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        subject_kind="enum_config",
        subject_type="EnumConfig",
        semantic_key=operation.semantic_key,
        object_key=_enum_fqn(operation=operation),
        field_name="enum_class",
        field_path=enum_name,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta." "python_orm_enum_create_graph_selector"
                ),
                "operation_key": operation.operation_key,
                "enum_fqn": _enum_fqn(operation=operation),
                "enum_name": enum_name,
            }
        ),
    )
    grammar_anchor_render_delta = _python_orm_enum_text_span_render_delta(
        operation=operation,
        context=context,
        target=target,
        relative_path=relative_path,
        source_hash=source_hash,
        byte_start=byte_start,
        byte_end=byte_end,
        before_text=before_text,
        replacement_text=replacement_text,
        graph_selector=graph_selector,
        event_key=event_key,
        replacement_key=f"aware_meta.python_orm.enum.create:{operation.operation_key}",
        replacement_metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta." "python_orm_enum_create_replacement"
                ),
                "span_target_source": (
                    "aware_meta.provider_delta." "python_orm_enum_create_span_target"
                ),
                "operation_key": operation.operation_key,
                "enum_name": enum_name,
                "renderer_key": META_PYTHON_ORM_ENUM_RENDERER_KEY,
            }
        ),
        delta_source=(
            "aware_meta.provider_delta."
            "python_orm_enum_create_grammar_anchor_render_delta"
        ),
    )
    if grammar_anchor_render_delta is None:
        return None
    return _PythonOrmEnumDescriptionDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        anchor=_enum_class_anchor_ref(operation=operation, context=context),
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
        mode_reason="python_orm_enum_create_grammar_anchor_render_delta_ready",
    )


def _python_orm_enum_delete_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmEnumDescriptionDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "enum"
        or operation.operation_family != "delete"
        or target.relative_path is None
    ):
        return None
    enum_name = _enum_name(operation=operation)
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if enum_name is None or source_state is None:
        return None
    relative_path, source_text = source_state
    span = _python_enum_delete_span(source_text=source_text, enum_name=enum_name)
    if span is None:
        return None
    byte_start, byte_end, before_text = span
    replacement_text = ""
    before_hash = _sha256_digest(before_text)
    after_hash = _sha256_digest(replacement_text)
    source_hash = _sha256_digest(source_text)
    graph_selector = CodeGraphFieldSelector(
        provider_key=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        subject_kind="enum_config",
        subject_type="EnumConfig",
        semantic_key=operation.semantic_key,
        object_key=_enum_fqn(operation=operation),
        field_name="enum_class",
        field_path=enum_name,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta." "python_orm_enum_delete_graph_selector"
                ),
                "operation_key": operation.operation_key,
                "enum_fqn": _enum_fqn(operation=operation),
                "enum_name": enum_name,
            }
        ),
    )
    grammar_anchor_render_delta = _python_orm_enum_text_span_render_delta(
        operation=operation,
        context=context,
        target=target,
        relative_path=relative_path,
        source_hash=source_hash,
        byte_start=byte_start,
        byte_end=byte_end,
        before_text=before_text,
        replacement_text=replacement_text,
        graph_selector=graph_selector,
        event_key=event_key,
        replacement_key=f"aware_meta.python_orm.enum.delete:{operation.operation_key}",
        replacement_metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta." "python_orm_enum_delete_replacement"
                ),
                "span_target_source": (
                    "aware_meta.provider_delta." "python_orm_enum_delete_span_target"
                ),
                "operation_key": operation.operation_key,
                "enum_name": enum_name,
                "renderer_key": META_PYTHON_ORM_ENUM_RENDERER_KEY,
            }
        ),
        delta_source=(
            "aware_meta.provider_delta."
            "python_orm_enum_delete_grammar_anchor_render_delta"
        ),
    )
    if grammar_anchor_render_delta is None:
        return None
    return _PythonOrmEnumDescriptionDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        anchor=_enum_class_anchor_ref(operation=operation, context=context),
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
        mode_reason="python_orm_enum_delete_grammar_anchor_render_delta_ready",
    )


def _python_orm_enum_option_create_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmEnumDescriptionDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "enum_option"
        or operation.operation_family != "create"
        or target.relative_path is None
    ):
        return None
    enum_name = _enum_name(operation=operation)
    option_value = _enum_option_value(operation=operation)
    replacement_text = _python_enum_option_line_text(option_value)
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if enum_name is None or replacement_text is None or source_state is None:
        return None
    relative_path, source_text = source_state
    span = _python_enum_option_insert_span(
        source_text=source_text,
        enum_name=enum_name,
        option_value=option_value,
    )
    if span is None:
        return None
    byte_start, byte_end, before_text = span
    before_hash = _sha256_digest(before_text)
    after_hash = _sha256_digest(replacement_text)
    source_hash = _sha256_digest(source_text)
    graph_selector = CodeGraphFieldSelector(
        provider_key=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        subject_kind="enum_option",
        subject_type="EnumOption",
        semantic_key=operation.semantic_key,
        object_key=option_value,
        field_name="value",
        field_path=".".join(
            part for part in (enum_name, option_value, "value") if part
        ),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_enum_option_line_graph_selector"
                ),
                "operation_key": operation.operation_key,
                "enum_fqn": _enum_fqn(operation=operation),
                "enum_name": enum_name,
                "option_value": option_value,
            }
        ),
    )
    grammar_anchor_render_delta = _python_orm_enum_text_span_render_delta(
        operation=operation,
        context=context,
        target=target,
        relative_path=relative_path,
        source_hash=source_hash,
        byte_start=byte_start,
        byte_end=byte_end,
        before_text=before_text,
        replacement_text=replacement_text,
        graph_selector=graph_selector,
        event_key=event_key,
        replacement_key=(
            "aware_meta.python_orm.enum.option_line:" f"{operation.operation_key}"
        ),
        replacement_metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_enum_option_line_replacement"
                ),
                "span_target_source": (
                    "aware_meta.provider_delta."
                    "python_orm_enum_option_line_span_target"
                ),
                "operation_key": operation.operation_key,
                "enum_name": enum_name,
                "option_value": option_value,
                "renderer_key": META_PYTHON_ORM_ENUM_RENDERER_KEY,
            }
        ),
        delta_source=(
            "aware_meta.provider_delta."
            "python_orm_enum_option_line_grammar_anchor_render_delta"
        ),
    )
    if grammar_anchor_render_delta is None:
        return None
    return _PythonOrmEnumDescriptionDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        anchor=_enum_option_anchor_ref(operation=operation, context=context),
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
        mode_reason="python_orm_enum_option_line_grammar_anchor_render_delta_ready",
    )


def _python_orm_enum_option_delete_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmEnumDescriptionDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "enum_option"
        or operation.operation_family != "delete"
        or target.relative_path is None
    ):
        return None
    enum_name = _enum_name(operation=operation)
    option_value = _enum_option_value(operation=operation)
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if enum_name is None or option_value is None or source_state is None:
        return None
    relative_path, source_text = source_state
    span = _python_enum_option_delete_span(
        source_text=source_text,
        enum_name=enum_name,
        option_value=option_value,
    )
    if span is None:
        return None
    byte_start, byte_end, before_text = span
    return _python_orm_enum_option_span_delta_evidence(
        operation=operation,
        context=context,
        target=target,
        event_key=event_key,
        relative_path=relative_path,
        source_text=source_text,
        byte_start=byte_start,
        byte_end=byte_end,
        before_text=before_text,
        replacement_text="",
        field_name="value",
        field_path=".".join(
            part for part in (enum_name, option_value, "value") if part
        ),
        graph_selector_source=(
            "aware_meta.provider_delta."
            "python_orm_enum_option_line_delete_graph_selector"
        ),
        span_target_source=(
            "aware_meta.provider_delta."
            "python_orm_enum_option_line_delete_span_target"
        ),
        replacement_source=(
            "aware_meta.provider_delta."
            "python_orm_enum_option_line_delete_replacement"
        ),
        delta_source=(
            "aware_meta.provider_delta."
            "python_orm_enum_option_line_delete_grammar_anchor_render_delta"
        ),
        replacement_key_prefix="aware_meta.python_orm.enum.option_line.delete",
        mode_reason=("python_orm_enum_option_delete_grammar_anchor_render_delta_ready"),
    )


def _python_orm_enum_option_reorder_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmEnumDescriptionDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "enum_option"
        or operation.operation_family != "update"
        or target.relative_path is None
    ):
        return None
    enum_name = _enum_name(operation=operation)
    option_value = _enum_option_value(operation=operation)
    baseline_position = _baseline_enum_option_position(operation=operation)
    current_position = _current_enum_option_position(operation=operation)
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if (
        enum_name is None
        or option_value is None
        or baseline_position is None
        or current_position is None
        or source_state is None
    ):
        return None
    relative_path, source_text = source_state
    span = _python_enum_option_reorder_span(
        source_text=source_text,
        enum_name=enum_name,
        option_value=option_value,
        baseline_position=baseline_position,
        current_position=current_position,
    )
    if span is None:
        return None
    byte_start, byte_end, before_text, replacement_text = span
    return _python_orm_enum_option_span_delta_evidence(
        operation=operation,
        context=context,
        target=target,
        event_key=event_key,
        relative_path=relative_path,
        source_text=source_text,
        byte_start=byte_start,
        byte_end=byte_end,
        before_text=before_text,
        replacement_text=replacement_text,
        field_name="position",
        field_path=".".join(
            part for part in (enum_name, option_value, "position") if part
        ),
        graph_selector_source=(
            "aware_meta.provider_delta."
            "python_orm_enum_option_line_reorder_graph_selector"
        ),
        span_target_source=(
            "aware_meta.provider_delta."
            "python_orm_enum_option_line_reorder_span_target"
        ),
        replacement_source=(
            "aware_meta.provider_delta."
            "python_orm_enum_option_line_reorder_replacement"
        ),
        delta_source=(
            "aware_meta.provider_delta."
            "python_orm_enum_option_line_reorder_grammar_anchor_render_delta"
        ),
        replacement_key_prefix="aware_meta.python_orm.enum.option_line.reorder",
        mode_reason=(
            "python_orm_enum_option_reorder_grammar_anchor_render_delta_ready"
        ),
    )


def _python_orm_enum_option_span_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
    relative_path: str,
    source_text: str,
    byte_start: int,
    byte_end: int,
    before_text: str,
    replacement_text: str,
    field_name: str,
    field_path: str,
    graph_selector_source: str,
    span_target_source: str,
    replacement_source: str,
    delta_source: str,
    replacement_key_prefix: str,
    mode_reason: str,
) -> _PythonOrmEnumDescriptionDeltaEvidence | None:
    enum_name = _enum_name(operation=operation)
    option_value = _enum_option_value(operation=operation)
    before_hash = _sha256_digest(before_text)
    after_hash = _sha256_digest(replacement_text)
    source_hash = _sha256_digest(source_text)
    graph_selector = CodeGraphFieldSelector(
        provider_key=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        subject_kind="enum_option",
        subject_type="EnumOption",
        semantic_key=operation.semantic_key,
        object_key=option_value,
        field_name=field_name,
        field_path=field_path,
        metadata=_json_object(
            {
                "source": graph_selector_source,
                "operation_key": operation.operation_key,
                "enum_fqn": _enum_fqn(operation=operation),
                "enum_name": enum_name,
                "option_value": option_value,
            }
        ),
    )
    grammar_anchor_render_delta = _python_orm_enum_text_span_render_delta(
        operation=operation,
        context=context,
        target=target,
        relative_path=relative_path,
        source_hash=source_hash,
        byte_start=byte_start,
        byte_end=byte_end,
        before_text=before_text,
        replacement_text=replacement_text,
        graph_selector=graph_selector,
        event_key=event_key,
        replacement_key=f"{replacement_key_prefix}:{operation.operation_key}",
        replacement_metadata=_json_object(
            {
                "source": replacement_source,
                "span_target_source": span_target_source,
                "operation_key": operation.operation_key,
                "enum_name": enum_name,
                "option_value": option_value,
                "renderer_key": META_PYTHON_ORM_ENUM_RENDERER_KEY,
            }
        ),
        delta_source=delta_source,
    )
    if grammar_anchor_render_delta is None:
        return None
    return _PythonOrmEnumDescriptionDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        anchor=_enum_option_anchor_ref(operation=operation, context=context),
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
        mode_reason=mode_reason,
    )


def _python_orm_enum_text_span_render_delta(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    relative_path: str,
    source_hash: str,
    byte_start: int,
    byte_end: int,
    before_text: str,
    replacement_text: str,
    graph_selector: CodeGraphFieldSelector,
    event_key: str,
    replacement_key: str,
    replacement_metadata: JsonObject,
    delta_source: str,
) -> ResolveCodeGrammarAnchorRenderDeltaRequest | None:
    target_key = target.target_key
    if target_key is None:
        return None
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
                replacement_key=replacement_key,
                byte_start=byte_start,
                byte_end=byte_end,
                before_text=before_text,
                replacement_text=replacement_text,
                graph_selector=graph_selector,
                metadata=replacement_metadata,
            )
        ],
        metadata=_json_object(
            {
                "source": delta_source,
                "operation_key": operation.operation_key,
                "target_kind": CodeGrammarAnchorRenderTargetKind.text_span.value,
                "renderer_key": META_PYTHON_ORM_ENUM_RENDERER_KEY,
                "renderer_profile": context.renderer_profile,
            }
        ),
    )


def _python_orm_enum_guarded_delta_diagnostics(
    *,
    operation: MetaProviderDeltaTypedOperation,
    target: CodeGeneratedMaterializationTargetRef,
) -> tuple[str, ...]:
    diagnostics = [META_PYTHON_ORM_ENUM_EVIDENCE_ONLY_DIAGNOSTIC]
    if target.relative_path is None:
        diagnostics.append(META_PYTHON_ORM_ENUM_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC)
    if _enum_structural_create_required(operation=operation):
        diagnostics.append(
            META_PYTHON_ORM_ENUM_STRUCTURAL_CREATE_POLICY_MISSING_DIAGNOSTIC
        )
    elif _enum_structural_delete_required(operation=operation):
        diagnostics.append(
            META_PYTHON_ORM_ENUM_STRUCTURAL_DELETE_POLICY_MISSING_DIAGNOSTIC
        )
    elif _enum_option_delete_required(operation=operation):
        diagnostics.append(META_PYTHON_ORM_ENUM_OPTION_DELETE_POLICY_MISSING_DIAGNOSTIC)
    elif _enum_option_position_changed(operation=operation):
        diagnostics.append(
            META_PYTHON_ORM_ENUM_OPTION_REORDER_POLICY_MISSING_DIAGNOSTIC
        )
    elif operation.ontology_subject_kind == "enum_option":
        if _enum_option_value(operation=operation) is None:
            diagnostics.append(META_PYTHON_ORM_ENUM_OPTION_LINE_TEXT_MISSING_DIAGNOSTIC)
        else:
            diagnostics.append(META_PYTHON_ORM_ENUM_OPTION_LINE_SPAN_MISSING_DIAGNOSTIC)
    elif _current_description(operation) is None:
        diagnostics.append(META_PYTHON_ORM_ENUM_DESCRIPTION_TEXT_MISSING_DIAGNOSTIC)
    else:
        diagnostics.append(META_PYTHON_ORM_ENUM_DESCRIPTION_SPAN_MISSING_DIAGNOSTIC)
    return tuple(dict.fromkeys(diagnostics))


def _python_enum_description_span(
    *,
    source_text: str,
    enum_name: str,
    expected_description: str | None,
) -> tuple[int, int, str] | None:
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return None
    enum_node = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == enum_name
        ),
        None,
    )
    if enum_node is None:
        return None
    body = tuple(enum_node.body)
    if not body:
        return None
    first_body_node = body[0]
    if _is_python_docstring_node(first_body_node):
        span = _node_line_span(source_text=source_text, node=first_body_node)
        if span is None:
            return None
        byte_start, byte_end, before_text = span
        if expected_description is not None and before_text != (
            _python_enum_docstring_text(expected_description)
        ):
            return None
        return byte_start, byte_end, before_text
    insert_at = _node_start_byte(source_text=source_text, node=first_body_node)
    if insert_at is None:
        return None
    if expected_description is not None:
        return None
    return insert_at, insert_at, ""


def _python_enum_create_insert_span(
    *,
    source_text: str,
    enum_name: str,
) -> tuple[int, int, str] | None:
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return None
    if any(
        isinstance(node, ast.ClassDef) and node.name == enum_name
        for node in ast.walk(tree)
    ):
        return None
    byte_end = len(source_text.encode("utf-8"))
    return byte_end, byte_end, ""


def _python_enum_delete_span(
    *,
    source_text: str,
    enum_name: str,
) -> tuple[int, int, str] | None:
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return None
    enum_node = next(
        (
            node
            for node in ast.walk(tree)
            if (
                isinstance(node, ast.ClassDef)
                and node.name == enum_name
                and _is_python_enum_class(node)
            )
        ),
        None,
    )
    if enum_node is None:
        return None
    lineno_value = getattr(enum_node, "lineno", None)
    end_lineno_value = getattr(enum_node, "end_lineno", None)
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


def _is_python_enum_class(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "Enum":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "Enum":
            return True
    return False


def _is_python_docstring_node(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _python_enum_option_insert_span(
    *,
    source_text: str,
    enum_name: str,
    option_value: str | None,
) -> tuple[int, int, str] | None:
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return None
    enum_node = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == enum_name
        ),
        None,
    )
    if enum_node is None:
        return None
    assignment_nodes = tuple(
        node
        for node in enum_node.body
        if _python_enum_assignment_name(node) is not None
    )
    assignment_names = {
        name
        for node in assignment_nodes
        for name in (_python_enum_assignment_name(node),)
        if name is not None
    }
    if option_value is None or option_value in assignment_names:
        return None
    if assignment_nodes:
        span = _node_line_span(source_text=source_text, node=assignment_nodes[-1])
        if span is None:
            return None
        _, byte_end, _ = span
        return byte_end, byte_end, ""
    body = tuple(enum_node.body)
    if body and _is_python_docstring_node(body[0]):
        span = _node_line_span(source_text=source_text, node=body[0])
        if span is None:
            return None
        _, byte_end, _ = span
        return byte_end, byte_end, ""
    if body:
        insert_at = _node_start_byte(source_text=source_text, node=body[0])
        if insert_at is None:
            return None
        return insert_at, insert_at, ""
    return None


def _python_enum_option_delete_span(
    *,
    source_text: str,
    enum_name: str,
    option_value: str,
) -> tuple[int, int, str] | None:
    expected_line = _python_enum_option_line_text(option_value)
    if expected_line is None:
        return None
    assignments = _python_enum_option_assignments(
        source_text=source_text,
        enum_name=enum_name,
    )
    assignment = next(
        (item for item in assignments if item.name == option_value),
        None,
    )
    if assignment is None or assignment.line_text != expected_line:
        return None
    return assignment.byte_start, assignment.byte_end, assignment.line_text


def _python_enum_option_reorder_span(
    *,
    source_text: str,
    enum_name: str,
    option_value: str,
    baseline_position: int,
    current_position: int,
) -> tuple[int, int, str, str] | None:
    assignments = _python_enum_option_assignments(
        source_text=source_text,
        enum_name=enum_name,
    )
    if (
        not assignments
        or baseline_position < 0
        or current_position < 0
        or baseline_position >= len(assignments)
        or current_position >= len(assignments)
        or assignments[baseline_position].name != option_value
        or baseline_position == current_position
    ):
        return None
    sorted_assignments = tuple(
        sorted(assignments, key=lambda assignment: assignment.byte_start)
    )
    for previous, current in zip(
        sorted_assignments,
        sorted_assignments[1:],
        strict=False,
    ):
        if previous.byte_end != current.byte_start:
            return None
    reordered = list(assignments)
    moving = reordered.pop(baseline_position)
    reordered.insert(current_position, moving)
    byte_start = sorted_assignments[0].byte_start
    byte_end = sorted_assignments[-1].byte_end
    before_text = "".join(assignment.line_text for assignment in assignments)
    replacement_text = "".join(assignment.line_text for assignment in reordered)
    if before_text == replacement_text:
        return None
    source_before_text = source_text.encode("utf-8")[byte_start:byte_end].decode(
        "utf-8"
    )
    if source_before_text != before_text:
        return None
    return byte_start, byte_end, before_text, replacement_text


def _python_enum_option_assignments(
    *,
    source_text: str,
    enum_name: str,
) -> tuple[_PythonEnumOptionAssignment, ...]:
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return ()
    enum_node = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == enum_name
        ),
        None,
    )
    if enum_node is None:
        return ()
    assignments: list[_PythonEnumOptionAssignment] = []
    for node in enum_node.body:
        name = _python_enum_assignment_name(node)
        if name is None:
            continue
        span = _node_line_span(source_text=source_text, node=node)
        if span is None:
            return ()
        byte_start, byte_end, line_text = span
        assignments.append(
            _PythonEnumOptionAssignment(
                name=name,
                byte_start=byte_start,
                byte_end=byte_end,
                line_text=line_text,
            )
        )
    return tuple(assignments)


def _python_enum_assignment_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id
    return None


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


def _python_enum_docstring_text(value: str | None) -> str | None:
    description = optional_text(value)
    if description is None:
        return None
    return f'    """{_python_docstring_line(description)}"""\n'


def _python_docstring_line(value: str) -> str:
    return " ".join(value.replace('"""', '\\"\\"\\"').split())


def _python_enum_class_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    enum_name = _enum_name(operation=operation)
    if (
        enum_name is None
        or not enum_name.isidentifier()
        or keyword.iskeyword(enum_name)
    ):
        return None
    lines = ["", "", f"class {enum_name}(Enum):"]
    description = _current_description(operation)
    if description is not None:
        lines.append(f'    """{_python_docstring_line(description)}"""')
    values = _enum_values(operation=operation)
    if values:
        for value in values:
            line = _python_enum_option_line_text(value)
            if line is None:
                return None
            lines.append(line.rstrip("\n"))
    elif description is None:
        lines.append("    pass")
    return "\n".join(lines) + "\n"


def _python_enum_option_line_text(value: str | None) -> str | None:
    option_value = optional_text(value)
    if (
        option_value is None
        or not option_value.isidentifier()
        or keyword.iskeyword(option_value)
    ):
        return None
    return f"    {option_value} = {json.dumps(option_value)}\n"


def _enum_option_delete_required(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    return (
        operation.ontology_subject_kind == "enum_option"
        and operation.operation_family == "delete"
    )


def _python_orm_generated_source_state(
    *,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
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
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
) -> CodeGeneratedMaterializationTargetRef:
    enum_fqn = _enum_fqn(operation=operation)
    enum_name = _enum_name(operation=operation)
    target_key = ".".join(
        part
        for part in (
            context.package_name,
            context.materialization_source,
            enum_fqn,
            "python_orm_enum",
        )
        if part
    )
    return CodeGeneratedMaterializationTargetRef(
        target_key=target_key,
        provider_key=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        target_language=context.target_language,
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        renderer_key=META_PYTHON_ORM_ENUM_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        output_key=enum_name,
        relative_path=_generated_relative_path(operation=operation, context=context),
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.python_orm_enum_target_ref",
                "operation_key": operation.operation_key,
                "enum_fqn": enum_fqn,
                "enum_name": enum_name,
            }
        ),
    )


def _anchor_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
) -> CodeGeneratedRendererAnchorRef:
    enum_fqn = _enum_fqn(operation=operation)
    enum_name = _enum_name(operation=operation)
    anchor_path = ".".join(part for part in (enum_name, "description") if part)
    return CodeGeneratedRendererAnchorRef(
        anchor_key=META_PYTHON_ORM_ENUM_DESCRIPTION_ANCHOR_KEY,
        anchor_path=anchor_path,
        anchor_role="enum_description",
        renderer_key=META_PYTHON_ORM_ENUM_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        target_language=context.target_language,
        section_type="enum",
        segment_name="description_comment",
        graph_selector=_json_object(
            {
                "provider_key": (
                    META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PROVIDER_KEY
                ),
                "semantic_owner": (
                    META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
                ),
                "enum_fqn": enum_fqn,
                "enum_name": enum_name,
                "field_name": "description",
                "field_path": anchor_path,
            }
        ),
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.python_orm_enum_anchor",
                "operation_key": operation.operation_key,
                "semantic_key": operation.semantic_key,
            }
        ),
    )


def _enum_option_anchor_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
) -> CodeGeneratedRendererAnchorRef:
    enum_fqn = _enum_fqn(operation=operation)
    enum_name = _enum_name(operation=operation)
    option_value = _enum_option_value(operation=operation)
    anchor_path = ".".join(part for part in (enum_name, option_value, "value") if part)
    return CodeGeneratedRendererAnchorRef(
        anchor_key=META_PYTHON_ORM_ENUM_OPTION_LINE_ANCHOR_KEY,
        anchor_path=anchor_path,
        anchor_role="enum_option_line",
        renderer_key=META_PYTHON_ORM_ENUM_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        target_language=context.target_language,
        section_type="enum_option",
        segment_name="option_line",
        graph_selector=_json_object(
            {
                "provider_key": (
                    META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PROVIDER_KEY
                ),
                "semantic_owner": (
                    META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
                ),
                "enum_fqn": enum_fqn,
                "enum_name": enum_name,
                "option_value": option_value,
                "field_name": "value",
                "field_path": anchor_path,
            }
        ),
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.python_orm_enum_option_anchor",
                "operation_key": operation.operation_key,
                "semantic_key": operation.semantic_key,
            }
        ),
    )


def _enum_class_anchor_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
) -> CodeGeneratedRendererAnchorRef:
    enum_fqn = _enum_fqn(operation=operation)
    enum_name = _enum_name(operation=operation)
    return CodeGeneratedRendererAnchorRef(
        anchor_key=META_PYTHON_ORM_ENUM_CLASS_ANCHOR_KEY,
        anchor_path=enum_name,
        anchor_role="enum_class",
        renderer_key=META_PYTHON_ORM_ENUM_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        target_language=context.target_language,
        section_type="enum",
        segment_name="enum_class",
        graph_selector=_json_object(
            {
                "provider_key": (
                    META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_PROVIDER_KEY
                ),
                "semantic_owner": (
                    META_PYTHON_ORM_ENUM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
                ),
                "enum_fqn": enum_fqn,
                "enum_name": enum_name,
                "field_name": "enum_class",
                "field_path": enum_name,
            }
        ),
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.python_orm_enum_class_anchor",
                "operation_key": operation.operation_key,
                "semantic_key": operation.semantic_key,
            }
        ),
    )


def _enum_description_changed(*, operation: MetaProviderDeltaTypedOperation) -> bool:
    if (
        operation.ontology_subject_kind != "enum"
        or operation.operation_family != "update"
    ):
        return False
    current_description = _current_description(operation)
    if current_description is None:
        return False
    return current_description != _baseline_description(operation)


def _enum_option_create_required(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    return (
        operation.ontology_subject_kind == "enum_option"
        and operation.operation_family == "create"
        and _enum_option_value(operation=operation) is not None
    )


def _enum_structural_create_required(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    return (
        operation.ontology_subject_kind == "enum"
        and operation.operation_family == "create"
    )


def _enum_structural_delete_required(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    return (
        operation.ontology_subject_kind == "enum"
        and operation.operation_family == "delete"
    )


def _enum_option_position_changed(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    if (
        operation.ontology_subject_kind != "enum_option"
        or operation.operation_family != "update"
    ):
        return False
    current_position = _current_enum_option_position(operation=operation)
    baseline_position = _baseline_enum_option_position(operation=operation)
    return (
        current_position is not None
        and baseline_position is not None
        and current_position != baseline_position
    )


def _current_enum_option_position(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> int | None:
    return _optional_int(
        _first_value(
            operation.current.get("position"),
            mapping_value(operation.current.get("payload")).get("position"),
        )
    )


def _baseline_enum_option_position(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> int | None:
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _optional_int(
        _first_value(
            operation.baseline.get("position"),
            baseline_object.get("position"),
            baseline_payload.get("position"),
        )
    )


def _current_description(operation: MetaProviderDeltaTypedOperation) -> str | None:
    signature = _enum_signature(payload=operation.current)
    return optional_text(signature.get("description")) or optional_text(
        operation.current.get("description")
    )


def _baseline_description(operation: MetaProviderDeltaTypedOperation) -> str | None:
    signature = _enum_signature(payload=operation.baseline)
    return optional_text(signature.get("description")) or optional_text(
        mapping_value(operation.baseline.get("object")).get("description")
    )


def _enum_signature(*, payload: Mapping[str, object]) -> Mapping[str, object]:
    signature = mapping_value(payload.get("enum_signature"))
    if signature:
        return signature
    nested_payload = mapping_value(payload.get("payload"))
    signature = mapping_value(nested_payload.get("enum_signature"))
    if signature:
        return signature
    object_payload = mapping_value(payload.get("object"))
    signature = mapping_value(object_payload.get("enum_signature"))
    if signature:
        return signature
    if object_payload:
        return object_payload
    return payload


def _enum_name(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return (
        optional_text(operation.current.get("enum_name"))
        or optional_text(operation.current.get("name"))
        or optional_text(operation.current.get("entity_name"))
        or _enum_name_from_fqn(optional_text(operation.current.get("enum_fqn")))
        or optional_text(_enum_signature(payload=operation.current).get("enum_name"))
        or optional_text(_enum_signature(payload=operation.current).get("name"))
        or _enum_name_from_fqn(
            optional_text(_enum_signature(payload=operation.current).get("enum_fqn"))
        )
        or _enum_name_from_semantic_key(operation.semantic_key)
    )


def _enum_fqn(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return (
        optional_text(operation.current.get("enum_fqn"))
        or optional_text(operation.current.get("enum_key"))
        or optional_text(_enum_signature(payload=operation.current).get("enum_fqn"))
        or optional_text(_enum_signature(payload=operation.baseline).get("enum_fqn"))
        or _enum_fqn_from_semantic_key(operation.semantic_key)
        or _enum_name(operation=operation)
    )


def _enum_option_value(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return (
        optional_text(operation.current.get("value"))
        or optional_text(operation.current.get("option_value"))
        or optional_text(operation.current.get("entity_name"))
        or optional_text(payload.get("value"))
        or optional_text(payload.get("option_value"))
        or optional_text(payload.get("entity_name"))
        or optional_text(baseline_object.get("value"))
        or optional_text(baseline_object.get("option_value"))
        or optional_text(baseline_object.get("entity_name"))
        or optional_text(baseline_payload.get("value"))
        or optional_text(baseline_payload.get("option_value"))
        or optional_text(baseline_payload.get("entity_name"))
        or _enum_option_value_from_semantic_key(operation.semantic_key)
    )


def _enum_values(*, operation: MetaProviderDeltaTypedOperation) -> tuple[str, ...]:
    return tuple_text(
        _first_value(
            operation.current.get("values"),
            mapping_value(operation.current.get("payload")).get("values"),
            _enum_signature(payload=operation.current).get("values"),
        )
    )


def _enum_option_value_from_semantic_key(semantic_key: str) -> str | None:
    marker = "/option:"
    if marker in semantic_key:
        return semantic_key.split(marker, maxsplit=1)[-1].split("/", maxsplit=1)[0]
    if semantic_key.startswith("meta.enum_option:"):
        return semantic_key.rsplit(".", maxsplit=1)[-1] or None
    return None


def _enum_name_from_fqn(value: str | None) -> str | None:
    if value is None:
        return None
    return value.rsplit(".", maxsplit=1)[-1] or None


def _enum_name_from_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.enum:"):
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


def _enum_fqn_from_semantic_key(semantic_key: str) -> str | None:
    marker = "/node:"
    if marker not in semantic_key:
        return None
    return semantic_key.split(marker, maxsplit=1)[-1].split("/", maxsplit=1)[0]


def _generated_relative_path(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmEnumGeneratedMaterializationContext,
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
    base_path = "/".join(source_parts)[: -len(".aware")]
    python_path = f"{base_path}.py"
    if not python_path.endswith("_enums.py"):
        parent, _, stem = python_path.rpartition("/")
        enum_stem = f"{stem.removesuffix('_enum')}_enums.py"
        python_path = f"{parent}/{enum_stem}" if parent else enum_stem
    if sources_root is None or python_path.startswith(f"{sources_root}/"):
        return python_path
    return f"{sources_root}/{python_path}"


def _python_orm_enum_context(
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> MetaPythonOrmEnumGeneratedMaterializationContext:
    sources_root = _python_orm_sources_root(
        package_name=context.package_name,
        sources_root=context.sources_root,
    )
    return MetaPythonOrmEnumGeneratedMaterializationContext(
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
    normalized_sources_root = _normalized_relative_path(sources_root)
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


def _first_value(*values: object) -> object | None:
    for value in values:
        if value is not None:
            return value
    return None


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _sorted_unique(values: Iterable[str | object]) -> tuple[str, ...]:
    return tuple(sorted({text for item in values for text in tuple_text(item)}))


def _language_plugin_metadata(
    language_plugin_delta_renderer: str | None,
) -> dict[str, object]:
    if language_plugin_delta_renderer is None:
        return {}
    return {"language_plugin_delta_renderer": language_plugin_delta_renderer}


def _sha256_digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _json_object(payload: Mapping[str, object]) -> JsonObject:
    return JsonObject(cast(Any, dict(payload)))


__all__ = [
    "META_PYTHON_ORM_ENUM_DESCRIPTION_ANCHOR_KEY",
    "META_PYTHON_ORM_ENUM_OPTION_LINE_ANCHOR_KEY",
    "META_PYTHON_ORM_ENUM_DESCRIPTION_SPAN_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_ENUM_DESCRIPTION_TEXT_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_ENUM_EVIDENCE_ONLY_DIAGNOSTIC",
    "META_PYTHON_ORM_ENUM_OPTION_LINE_SPAN_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_ENUM_OPTION_LINE_TEXT_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_ENUM_OPTION_REORDER_POLICY_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_ENUM_STRUCTURAL_CREATE_POLICY_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_ENUM_STRUCTURAL_DELETE_POLICY_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_ENUM_RENDERER_KEY",
    "META_PYTHON_ORM_ENUM_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC",
    "MetaPythonOrmEnumGeneratedMaterializationContext",
    "MetaPythonOrmEnumGeneratedMaterializationDeltaEvidence",
    "generated_materialization_feature_results_from_enum_config_typed_operation",
    "python_orm_generated_materialization_delta_from_enum_config_typed_operation",
]
