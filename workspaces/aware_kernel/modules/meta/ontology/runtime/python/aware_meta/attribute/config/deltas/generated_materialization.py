from __future__ import annotations

import ast
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
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
    CodeSectionDeltaEntry,
    CodeSectionDeltaOperationKind,
    CodeSectionDeltaSet,
    CodeSectionRef,
    CodeSegmentRef,
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
from aware_meta.materialization.deltas.language_renderer_contracts import (
    MetaLanguageGeneratedMaterializationDeltaContext,
    MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    MetaLanguageGeneratedMaterializationTargetHint,
)
from aware_meta.materialization.deltas.generated_materialization_spans import (
    MetaGeneratedMaterializationTextSpanContext,
    meta_generated_materialization_correlated_text_span_render_delta,
    meta_generated_materialization_text_span_replacement,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_code_ontology.code.code_enums import CodeLanguage as MetaPluginCodeLanguage
from aware_types import JsonObject


META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY = "aware_meta"
META_PYTHON_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER = "aware_meta.ocg"
META_PYTHON_ORM_GENERATED_MATERIALIZATION_PRODUCT_INTENT = "python_orm_runtime"
META_PYTHON_ORM_RENDERER_PROFILE = "orm_runtime"
META_PYTHON_ORM_MATERIALIZATION_SOURCE = "ontology_orm_models"
META_PYTHON_ORM_ATTRIBUTE_TYPE_RENDERER_KEY = "python.orm.attribute.type"
META_PYTHON_ORM_ATTRIBUTE_TYPE_ANCHOR_KEY = "python.orm.attribute.type_annotation"
META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_RENDERER_KEY = (
    "python.orm.attribute.default_value"
)
META_PYTHON_ORM_ATTRIBUTE_FIELD_RENDERER_KEY = "python.orm.attribute.field"
META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_ANCHOR_KEY = (
    "python.orm.attribute.default_value"
)
META_PYTHON_ORM_ATTRIBUTE_FIELD_ANCHOR_KEY = "python.orm.attribute.field"
META_PYTHON_ORM_ATTRIBUTE_TYPE_EVIDENCE_ONLY_DIAGNOSTIC = (
    "meta_python_orm_generated_materialization_renderer_operation_evidence_only"
)
META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_EVIDENCE_ONLY_DIAGNOSTIC = (
    "meta_python_orm_attribute_default_value_renderer_operation_evidence_only"
)
META_PYTHON_ORM_ATTRIBUTE_TYPE_UNSUPPORTED_REASON = (
    "meta_python_orm_attribute_type_requires_renderable_primitive_type_descriptor"
)
META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_UNSUPPORTED_REASON = (
    "meta_python_orm_attribute_default_value_requires_renderable_default_value"
)
META_PYTHON_ORM_ATTRIBUTE_TYPE_NOT_REQUIRED_REASON = (
    "meta_python_orm_attribute_type_delta_not_required"
)
META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_NOT_REQUIRED_REASON = (
    "meta_python_orm_attribute_default_value_delta_not_required"
)
META_PYTHON_ORM_ATTRIBUTE_MEMBERSHIP_NOT_REQUIRED_REASON = (
    "meta_python_orm_attribute_membership_generated_materialization_not_required"
)
META_PYTHON_ORM_ATTRIBUTE_TYPE_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC = (
    "meta_python_orm_generated_target_relative_path_missing"
)
META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC = (
    "meta_python_orm_attribute_default_value_generated_target_relative_path_missing"
)
META_PYTHON_ORM_ATTRIBUTE_TYPE_BASELINE_HASH_MISSING_DIAGNOSTIC = (
    "meta_python_orm_attribute_type_baseline_hash_missing"
)
META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_BASELINE_HASH_MISSING_DIAGNOSTIC = (
    "meta_python_orm_attribute_default_value_baseline_hash_missing"
)
META_PYTHON_ORM_ATTRIBUTE_FIELD_EVIDENCE_ONLY_DIAGNOSTIC = (
    "meta_python_orm_attribute_field_renderer_operation_evidence_only"
)
META_PYTHON_ORM_ATTRIBUTE_FIELD_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC = (
    "meta_python_orm_attribute_field_generated_target_relative_path_missing"
)
META_PYTHON_ORM_ATTRIBUTE_FIELD_UNSUPPORTED_REASON = (
    "meta_python_orm_attribute_field_requires_renderable_primitive_type_descriptor"
)
META_PYTHON_ORM_ATTRIBUTE_FIELD_SPAN_MISSING_DIAGNOSTIC = (
    "meta_python_orm_attribute_field_span_missing"
)

_PYTHON_PRIMITIVE_TYPE_TEXT = {
    "any": "Any",
    "boolean": "bool",
    "bool": "bool",
    "bytes": "bytes",
    "datetime": "datetime",
    "date_time": "datetime",
    "float": "float",
    "integer": "int",
    "int": "int",
    "json": "Any",
    "string": "str",
    "uuid": "UUID",
}


@dataclass(frozen=True, slots=True)
class MetaPythonOrmGeneratedMaterializationContext:
    package_name: str | None = None
    package_root: str | None = None
    sources_root: str | None = None
    target_language: str = "python"
    renderer_key: str = META_PYTHON_ORM_ATTRIBUTE_TYPE_RENDERER_KEY
    renderer_profile: str = META_PYTHON_ORM_RENDERER_PROFILE
    materialization_source: str = META_PYTHON_ORM_MATERIALIZATION_SOURCE
    artifact_family: str = "ocg_language_materialization"
    artifact_role: str = "python_orm_model"
    relative_path_by_owner_key: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MetaPythonOrmGeneratedMaterializationDeltaEvidence:
    delta_request: CodeGeneratedMaterializationDeltaRequest
    result: CodeGeneratedMaterializationDeltaResult


@dataclass(frozen=True, slots=True)
class _PythonOrmAttributeStructuralDeltaEvidence:
    grammar_anchor_render_delta: ResolveCodeGrammarAnchorRenderDeltaRequest
    anchor: CodeGeneratedRendererAnchorRef
    content_text: str
    before_hash: str
    after_hash: str
    mode_reason: str


def generated_materialization_feature_results_from_attribute_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> tuple[MetaProviderDeltaGeneratedMaterializationFeatureResult, ...]:
    if operation.ontology_subject_kind not in {"attribute", "attribute_membership"}:
        return (
            MetaProviderDeltaGeneratedMaterializationFeatureResult.skipped(
                feature_key="attribute_config",
                operation=operation,
                reason="meta_python_orm_generated_materialization_subject_not_supported",
                event_refs=(
                    meta_provider_delta_world_change_event_key(operation=operation),
                ),
            ),
        )

    evidence = python_orm_generated_materialization_delta_from_attribute_config_typed_operation(
        operation,
        context=_python_orm_context(context),
    )
    return (
        MetaProviderDeltaGeneratedMaterializationFeatureResult.from_evidence(
            feature_key="attribute_config",
            operation=operation,
            delta_request=evidence.delta_request,
            result=evidence.result,
            reason="meta_python_orm_generated_materialization_evidence_built",
        ),
    )


def python_orm_generated_materialization_delta_from_attribute_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    *,
    context: MetaPythonOrmGeneratedMaterializationContext | None = None,
) -> MetaPythonOrmGeneratedMaterializationDeltaEvidence:
    """Build read-only Python ORM generated-materialization delta evidence."""

    resolved_context = _python_orm_context_for_operation(
        operation=operation,
        context=context or MetaPythonOrmGeneratedMaterializationContext(),
    )
    plugin_evidence = _python_orm_plugin_delta_evidence(
        operation=operation,
        context=resolved_context,
    )
    if plugin_evidence is not None:
        return plugin_evidence
    event_key = meta_provider_delta_world_change_event_key(operation=operation)
    target = _target_ref(operation=operation, context=resolved_context)
    attribute_field_key = _python_orm_attribute_field_key(operation=operation)
    request = CodeGeneratedMaterializationDeltaRequest(
        provider_key=META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        package_name=resolved_context.package_name,
        package_root=resolved_context.package_root,
        sources_root=resolved_context.sources_root,
        product_intent=META_PYTHON_ORM_GENERATED_MATERIALIZATION_PRODUCT_INTENT,
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
                    "aware_meta.python_orm.generated_materialization."
                    f"{operation.operation_key}"
                ),
                event_key=event_key,
                target=target,
                policy_key=f"aware_meta.python_orm.attribute_{attribute_field_key}",
                renderer_key=resolved_context.renderer_key,
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.provider_delta."
                            "python_orm_generated_materialization_action"
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
                    "python_orm_generated_materialization_delta_request"
                ),
                "renderer_profile": resolved_context.renderer_profile,
                "materialization_source": resolved_context.materialization_source,
            }
        ),
    )

    result = _python_orm_attribute_result(
        operation=operation,
        context=resolved_context,
        event_key=event_key,
        target=target,
    )
    return MetaPythonOrmGeneratedMaterializationDeltaEvidence(
        delta_request=request,
        result=result,
    )


def _python_orm_attribute_result(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
) -> CodeGeneratedMaterializationDeltaResult:
    if operation.ontology_subject_kind == "attribute_membership":
        return CodeGeneratedMaterializationDeltaResult(
            provider_key=META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
            semantic_owner=META_PYTHON_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
            available=True,
            mode=CodeGeneratedMaterializationDeltaMode.not_required,
            skipped_targets=[
                CodeGeneratedMaterializationSkippedTarget(
                    target=target,
                    reason=META_PYTHON_ORM_ATTRIBUTE_MEMBERSHIP_NOT_REQUIRED_REASON,
                    event_refs=[event_key],
                )
            ],
        )
    if _attribute_structural_create_required(operation=operation):
        return _python_orm_attribute_structural_result(
            operation=operation,
            context=context,
            event_key=event_key,
            target=target,
        )
    if _attribute_structural_delete_required(operation=operation):
        return _python_orm_attribute_structural_result(
            operation=operation,
            context=context,
            event_key=event_key,
            target=target,
        )
    if _attribute_default_value_changed(operation=operation):
        return _python_orm_attribute_default_value_result(
            operation=operation,
            context=context,
            event_key=event_key,
            target=target,
        )
    return _python_orm_attribute_type_result(
        operation=operation,
        context=context,
        event_key=event_key,
        target=target,
    )


def _python_orm_plugin_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
) -> MetaPythonOrmGeneratedMaterializationDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "attribute"
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
    return MetaPythonOrmGeneratedMaterializationDeltaEvidence(
        delta_request=render_result.delta_request,
        result=render_result.result,
    )


def _language_delta_context(
    context: MetaPythonOrmGeneratedMaterializationContext,
) -> MetaLanguageGeneratedMaterializationDeltaContext:
    return MetaLanguageGeneratedMaterializationDeltaContext(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        target_language=context.target_language,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        product_intent=META_PYTHON_ORM_GENERATED_MATERIALIZATION_PRODUCT_INTENT,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        target_hints=tuple(
            MetaLanguageGeneratedMaterializationTargetHint(
                owner_key=owner_key,
                relative_path=relative_path,
                artifact_family=context.artifact_family,
                artifact_role=context.artifact_role,
            )
            for owner_key, relative_path in sorted(
                context.relative_path_by_owner_key.items()
            )
        ),
    )


def _meta_plugin_code_language(value: str) -> MetaPluginCodeLanguage:
    try:
        return MetaPluginCodeLanguage(value)
    except ValueError:
        return MetaPluginCodeLanguage.python


def _python_orm_attribute_structural_result(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
) -> CodeGeneratedMaterializationDeltaResult:
    if _attribute_structural_create_required(operation=operation):
        delta_evidence = _python_orm_attribute_create_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    else:
        delta_evidence = _python_orm_attribute_delete_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    has_delta = delta_evidence is not None
    diagnostics = (
        ()
        if has_delta
        else _python_orm_attribute_structural_diagnostics(
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
        operation_key=f"aware_meta.python_orm.attribute.field:{operation.operation_key}",
        kind=(
            CodeGeneratedRendererDeltaOperationKind.replace_anchor
            if has_delta
            else CodeGeneratedRendererDeltaOperationKind.fallback_full_render
        ),
        target=target,
        anchor=(
            delta_evidence.anchor
            if delta_evidence is not None
            else _field_anchor_ref(operation=operation, context=context)
        ),
        renderer_key=context.renderer_key,
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
                    "aware_meta.provider_delta."
                    "python_orm_attribute_field_renderer_operation"
                ),
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "mode_reason": (
                    delta_evidence.mode_reason
                    if has_delta
                    else "python_orm_attribute_field_guarded_delta_missing"
                ),
            }
        ),
    )
    entry = CodeGeneratedMaterializationDeltaEntry(
        entry_key=f"aware_meta.python_orm.attribute.field:{operation.operation_key}",
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
                    "python_orm_attribute_field_generated_materialization_delta_entry"
                ),
                "operation_key": operation.operation_key,
                "package_delta_emitted": False,
                "section_delta_emitted": False,
                "grammar_anchor_render_delta_emitted": has_delta,
            }
        ),
    )
    return CodeGeneratedMaterializationDeltaResult(
        provider_key=META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        available=True,
        mode=entry_mode,
        entries=[entry],
        diagnostics=list(diagnostics),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_attribute_field_generated_materialization_delta_result"
                ),
                "operation_key": operation.operation_key,
                "renderer_operation_count": 1,
                "package_delta_emitted": False,
                "section_delta_emitted": False,
                "grammar_anchor_render_delta_emitted": has_delta,
            }
        ),
    )


def _python_orm_attribute_type_result(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
) -> CodeGeneratedMaterializationDeltaResult:
    if not _attribute_type_changed(operation=operation):
        return CodeGeneratedMaterializationDeltaResult(
            provider_key=META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
            semantic_owner=META_PYTHON_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
            available=True,
            mode=CodeGeneratedMaterializationDeltaMode.not_required,
            skipped_targets=[
                CodeGeneratedMaterializationSkippedTarget(
                    target=target,
                    reason=META_PYTHON_ORM_ATTRIBUTE_TYPE_NOT_REQUIRED_REASON,
                    event_refs=[event_key],
                )
            ],
        )

    replacement_text = _python_type_annotation(
        operation=operation, payload=operation.current
    )
    if replacement_text is None:
        return CodeGeneratedMaterializationDeltaResult(
            provider_key=META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
            semantic_owner=META_PYTHON_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
            available=True,
            mode=CodeGeneratedMaterializationDeltaMode.blocked,
            skipped_targets=[
                CodeGeneratedMaterializationSkippedTarget(
                    target=target,
                    reason=META_PYTHON_ORM_ATTRIBUTE_TYPE_UNSUPPORTED_REASON,
                    event_refs=[event_key],
                    metadata=_json_object(
                        {
                            "operation_key": operation.operation_key,
                            "semantic_key": operation.semantic_key,
                        }
                    ),
                )
            ],
            diagnostics=[META_PYTHON_ORM_ATTRIBUTE_TYPE_UNSUPPORTED_REASON],
        )

    baseline_text = _python_type_annotation(
        operation=operation, payload=operation.baseline
    )
    operation_diagnostics = [
        *(
            [META_PYTHON_ORM_ATTRIBUTE_TYPE_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC]
            if target.relative_path is None
            else []
        ),
        *(
            [META_PYTHON_ORM_ATTRIBUTE_TYPE_BASELINE_HASH_MISSING_DIAGNOSTIC]
            if baseline_text is None
            else []
        ),
    ]
    has_resolvable_section_delta_evidence = (
        target.relative_path is not None and baseline_text is not None
    )
    entry_mode = (
        CodeGeneratedMaterializationDeltaMode.section_delta_ready
        if has_resolvable_section_delta_evidence
        else CodeGeneratedMaterializationDeltaMode.fallback_full_render
    )
    if not has_resolvable_section_delta_evidence:
        operation_diagnostics.insert(
            0,
            META_PYTHON_ORM_ATTRIBUTE_TYPE_EVIDENCE_ONLY_DIAGNOSTIC,
        )
    renderer_operation = CodeGeneratedRendererDeltaOperation(
        operation_key=f"aware_meta.python_orm.attribute.type:{operation.operation_key}",
        kind=CodeGeneratedRendererDeltaOperationKind.replace_anchor,
        target=target,
        anchor=_anchor_ref(operation=operation, context=context),
        renderer_key=context.renderer_key,
        renderer_profile=context.renderer_profile,
        before_hash=(
            _sha256_digest(baseline_text) if baseline_text is not None else None
        ),
        after_hash=_sha256_digest(replacement_text),
        content_text=replacement_text,
        replacement_text=replacement_text,
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        diagnostics=operation_diagnostics,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_attribute_type_renderer_operation"
                ),
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "baseline_rendered_text": baseline_text,
                "current_rendered_text": replacement_text,
            }
        ),
    )
    entry = CodeGeneratedMaterializationDeltaEntry(
        entry_key=f"aware_meta.python_orm.attribute.type:{operation.operation_key}",
        mode=entry_mode,
        target=target,
        section_delta=(
            _python_orm_attribute_type_section_delta(
                operation=operation,
                context=context,
                target=target,
                event_key=event_key,
                baseline_text=baseline_text,
                replacement_text=replacement_text,
            )
            if has_resolvable_section_delta_evidence
            else None
        ),
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        artifact_key=target.target_key,
        relative_path=target.relative_path,
        before_hash=renderer_operation.before_hash,
        after_hash=renderer_operation.after_hash,
        renderer_operations=[renderer_operation],
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        diagnostics=operation_diagnostics,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_generated_materialization_delta_entry"
                ),
                "operation_key": operation.operation_key,
                "mode_reason": (
                    "python_orm_attribute_type_section_delta_ready"
                    if has_resolvable_section_delta_evidence
                    else "renderer_operation_evidence_without_package_delta"
                ),
            }
        ),
    )
    return CodeGeneratedMaterializationDeltaResult(
        provider_key=META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        available=True,
        mode=entry_mode,
        entries=[entry],
        diagnostics=operation_diagnostics,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_generated_materialization_delta_result"
                ),
                "operation_key": operation.operation_key,
                "renderer_operation_count": 1,
                "package_delta_emitted": False,
                "section_delta_emitted": has_resolvable_section_delta_evidence,
            }
        ),
    )


def _python_orm_attribute_default_value_result(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
) -> CodeGeneratedMaterializationDeltaResult:
    replacement_text = _python_default_value_expression(payload=operation.current)
    if replacement_text is None:
        return CodeGeneratedMaterializationDeltaResult(
            provider_key=META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
            semantic_owner=META_PYTHON_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
            available=True,
            mode=CodeGeneratedMaterializationDeltaMode.blocked,
            skipped_targets=[
                CodeGeneratedMaterializationSkippedTarget(
                    target=target,
                    reason=META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_UNSUPPORTED_REASON,
                    event_refs=[event_key],
                    metadata=_json_object(
                        {
                            "operation_key": operation.operation_key,
                            "semantic_key": operation.semantic_key,
                        }
                    ),
                )
            ],
            diagnostics=[META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_UNSUPPORTED_REASON],
        )

    baseline_text = _python_default_value_expression(payload=operation.baseline)
    operation_diagnostics = [
        *(
            [
                (
                    META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC
                )
            ]
            if target.relative_path is None
            else []
        ),
        *(
            [(META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_BASELINE_HASH_MISSING_DIAGNOSTIC)]
            if baseline_text is None
            else []
        ),
    ]
    has_resolvable_section_delta_evidence = (
        target.relative_path is not None and baseline_text is not None
    )
    entry_mode = (
        CodeGeneratedMaterializationDeltaMode.section_delta_ready
        if has_resolvable_section_delta_evidence
        else CodeGeneratedMaterializationDeltaMode.fallback_full_render
    )
    if not has_resolvable_section_delta_evidence:
        operation_diagnostics.insert(
            0,
            META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_EVIDENCE_ONLY_DIAGNOSTIC,
        )
    renderer_operation = CodeGeneratedRendererDeltaOperation(
        operation_key=(
            "aware_meta.python_orm.attribute.default_value:"
            f"{operation.operation_key}"
        ),
        kind=CodeGeneratedRendererDeltaOperationKind.replace_anchor,
        target=target,
        anchor=_default_value_anchor_ref(operation=operation, context=context),
        renderer_key=context.renderer_key,
        renderer_profile=context.renderer_profile,
        before_hash=(
            _sha256_digest(baseline_text) if baseline_text is not None else None
        ),
        after_hash=_sha256_digest(replacement_text),
        content_text=replacement_text,
        replacement_text=replacement_text,
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        diagnostics=operation_diagnostics,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_attribute_default_value_renderer_operation"
                ),
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "baseline_rendered_text": baseline_text,
                "current_rendered_text": replacement_text,
            }
        ),
    )
    entry = CodeGeneratedMaterializationDeltaEntry(
        entry_key=(
            "aware_meta.python_orm.attribute.default_value:"
            f"{operation.operation_key}"
        ),
        mode=entry_mode,
        target=target,
        section_delta=(
            _python_orm_attribute_default_value_section_delta(
                operation=operation,
                context=context,
                target=target,
                event_key=event_key,
                baseline_text=baseline_text,
                replacement_text=replacement_text,
            )
            if has_resolvable_section_delta_evidence
            else None
        ),
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        artifact_key=target.target_key,
        relative_path=target.relative_path,
        before_hash=renderer_operation.before_hash,
        after_hash=renderer_operation.after_hash,
        renderer_operations=[renderer_operation],
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        diagnostics=operation_diagnostics,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_generated_materialization_delta_entry"
                ),
                "operation_key": operation.operation_key,
                "mode_reason": (
                    "python_orm_attribute_default_value_section_delta_ready"
                    if has_resolvable_section_delta_evidence
                    else "renderer_operation_evidence_without_package_delta"
                ),
            }
        ),
    )
    return CodeGeneratedMaterializationDeltaResult(
        provider_key=META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        available=True,
        mode=entry_mode,
        entries=[entry],
        diagnostics=operation_diagnostics,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_generated_materialization_delta_result"
                ),
                "operation_key": operation.operation_key,
                "renderer_operation_count": 1,
                "package_delta_emitted": False,
                "section_delta_emitted": has_resolvable_section_delta_evidence,
            }
        ),
    )


def _python_orm_attribute_type_section_delta(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
    baseline_text: str | None,
    replacement_text: str,
) -> CodeSectionDeltaSet:
    attribute_name = _attribute_name(operation=operation)
    owner_name = _owner_name(operation=operation)
    relative_path = _section_delta_relative_path(
        relative_path=target.relative_path,
        sources_root=context.sources_root,
    )
    section_qualname = ".".join(part for part in (owner_name, attribute_name) if part)
    return CodeSectionDeltaSet(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        entries=[
            CodeSectionDeltaEntry(
                operation=CodeSectionDeltaOperationKind.replace_segment,
                section_ref=CodeSectionRef(
                    package_name=context.package_name,
                    relative_path=relative_path or "",
                    language=context.target_language,
                    section_type="attribute",
                    qualname=section_qualname or None,
                    semantic_key=operation.semantic_key,
                    source_refs=list(_sorted_unique(operation.source_refs)),
                    metadata=_json_object(
                        {
                            "source": (
                                "aware_meta.provider_delta."
                                "python_orm_attribute_type_section_ref"
                            ),
                            "operation_key": operation.operation_key,
                            "target_relative_path": target.relative_path,
                        }
                    ),
                ),
                segment_ref=CodeSegmentRef(
                    segment_name="type",
                    before_segment_hash=(
                        _sha256_digest(baseline_text)
                        if baseline_text is not None
                        else None
                    ),
                    metadata=_json_object(
                        {
                            "source": (
                                "aware_meta.provider_delta."
                                "python_orm_attribute_type_segment_ref"
                            ),
                            "anchor_key": META_PYTHON_ORM_ATTRIBUTE_TYPE_ANCHOR_KEY,
                        }
                    ),
                ),
                content_text=replacement_text,
                after_hash=_sha256_digest(replacement_text),
                event_ref=event_key,
                semantic_key=operation.semantic_key,
                provider_key=META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.provider_delta."
                            "python_orm_attribute_type_section_delta"
                        ),
                        "operation_key": operation.operation_key,
                        "renderer_key": context.renderer_key,
                        "renderer_profile": context.renderer_profile,
                    }
                ),
            )
        ],
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_generated_materialization_section_delta_set"
                ),
                "operation_key": operation.operation_key,
                "renderer_key": context.renderer_key,
                "renderer_profile": context.renderer_profile,
            }
        ),
    )


def _python_orm_attribute_default_value_section_delta(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
    baseline_text: str | None,
    replacement_text: str,
) -> CodeSectionDeltaSet:
    attribute_name = _attribute_name(operation=operation)
    owner_name = _owner_name(operation=operation)
    relative_path = _section_delta_relative_path(
        relative_path=target.relative_path,
        sources_root=context.sources_root,
    )
    section_qualname = ".".join(part for part in (owner_name, attribute_name) if part)
    return CodeSectionDeltaSet(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        entries=[
            CodeSectionDeltaEntry(
                operation=CodeSectionDeltaOperationKind.replace_segment,
                section_ref=CodeSectionRef(
                    package_name=context.package_name,
                    relative_path=relative_path or "",
                    language=context.target_language,
                    section_type="attribute",
                    qualname=section_qualname or None,
                    semantic_key=operation.semantic_key,
                    source_refs=list(_sorted_unique(operation.source_refs)),
                    metadata=_json_object(
                        {
                            "source": (
                                "aware_meta.provider_delta."
                                "python_orm_attribute_default_value_section_ref"
                            ),
                            "operation_key": operation.operation_key,
                            "target_relative_path": target.relative_path,
                        }
                    ),
                ),
                segment_ref=CodeSegmentRef(
                    segment_name="default_value",
                    before_segment_hash=(
                        _sha256_digest(baseline_text)
                        if baseline_text is not None
                        else None
                    ),
                    metadata=_json_object(
                        {
                            "source": (
                                "aware_meta.provider_delta."
                                "python_orm_attribute_default_value_segment_ref"
                            ),
                            "anchor_key": (
                                META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_ANCHOR_KEY
                            ),
                        }
                    ),
                ),
                content_text=replacement_text,
                after_hash=_sha256_digest(replacement_text),
                event_ref=event_key,
                semantic_key=operation.semantic_key,
                provider_key=META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.provider_delta."
                            "python_orm_attribute_default_value_section_delta"
                        ),
                        "operation_key": operation.operation_key,
                        "renderer_key": context.renderer_key,
                        "renderer_profile": context.renderer_profile,
                    }
                ),
            )
        ],
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_generated_materialization_section_delta_set"
                ),
                "operation_key": operation.operation_key,
                "renderer_key": context.renderer_key,
                "renderer_profile": context.renderer_profile,
            }
        ),
    )


def _python_orm_attribute_create_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmAttributeStructuralDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "attribute"
        or operation.operation_family != "create"
        or target.relative_path is None
    ):
        return None
    attribute_name = _attribute_name(operation=operation)
    owner_name = _owner_name(operation=operation)
    replacement_text = _python_field_text(operation=operation)
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if (
        attribute_name is None
        or owner_name is None
        or replacement_text is None
        or source_state is None
    ):
        return None
    relative_path, source_text = source_state
    span = _python_attribute_create_insert_span(
        source_text=source_text,
        class_name=owner_name,
        attribute_name=attribute_name,
    )
    if span is None:
        return None
    byte_start, byte_end, before_text = span
    before_hash = _sha256_digest(before_text)
    after_hash = _sha256_digest(replacement_text)
    grammar_anchor_render_delta = _attribute_field_grammar_anchor_render_delta(
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
    return _PythonOrmAttributeStructuralDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        anchor=_field_anchor_ref(operation=operation, context=context),
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
        mode_reason="python_orm_attribute_create_grammar_anchor_render_delta_ready",
    )


def _python_orm_attribute_delete_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmAttributeStructuralDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "attribute"
        or operation.operation_family != "delete"
        or target.relative_path is None
    ):
        return None
    attribute_name = _attribute_name(operation=operation)
    owner_name = _owner_name(operation=operation)
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if attribute_name is None or owner_name is None or source_state is None:
        return None
    relative_path, source_text = source_state
    span = _python_attribute_delete_span(
        source_text=source_text,
        class_name=owner_name,
        attribute_name=attribute_name,
    )
    if span is None:
        return None
    byte_start, byte_end, before_text = span
    replacement_text = ""
    before_hash = _sha256_digest(before_text)
    after_hash = _sha256_digest(replacement_text)
    grammar_anchor_render_delta = _attribute_field_grammar_anchor_render_delta(
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
    return _PythonOrmAttributeStructuralDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        anchor=_field_anchor_ref(operation=operation, context=context),
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
        mode_reason="python_orm_attribute_delete_grammar_anchor_render_delta_ready",
    )


def _attribute_field_grammar_anchor_render_delta(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
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
    graph_selector = _attribute_field_graph_selector(operation=operation)
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
                    "aware_meta.python_orm.attribute.field."
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
                            "aware_meta.provider_delta."
                            "python_orm_attribute_field_span_target"
                        ),
                        "operation_key": operation.operation_key,
                        "attribute_name": _attribute_name(operation=operation),
                        "owner_key": _owner_key(operation=operation),
                    }
                ),
            )
        ],
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_attribute_field_grammar_anchor_render_delta"
                ),
                "operation_key": operation.operation_key,
                "target_kind": CodeGrammarAnchorRenderTargetKind.text_span.value,
                "renderer_key": META_PYTHON_ORM_ATTRIBUTE_FIELD_RENDERER_KEY,
                "renderer_profile": context.renderer_profile,
            }
        ),
    )


def _attribute_field_graph_selector(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> CodeGraphFieldSelector:
    owner_key = _owner_key(operation=operation)
    owner_name = _owner_name(operation=operation)
    attribute_name = _attribute_name(operation=operation)
    field_path = ".".join(
        part for part in (owner_name, attribute_name, "__field__") if part
    )
    return CodeGraphFieldSelector(
        provider_key=META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        subject_kind="attribute_config",
        subject_type="AttributeConfig",
        semantic_key=operation.semantic_key,
        object_key=owner_key,
        field_name="attribute_field",
        field_path=field_path,
        class_fqn=owner_key,
        class_name=owner_name,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_attribute_field_graph_selector"
                ),
                "operation_key": operation.operation_key,
                "attribute_name": attribute_name,
                "owner_key": owner_key,
            }
        ),
    )


def _python_orm_attribute_structural_diagnostics(
    *,
    operation: MetaProviderDeltaTypedOperation,
    target: CodeGeneratedMaterializationTargetRef,
) -> tuple[str, ...]:
    diagnostics = [META_PYTHON_ORM_ATTRIBUTE_FIELD_EVIDENCE_ONLY_DIAGNOSTIC]
    if target.relative_path is None:
        diagnostics.append(
            META_PYTHON_ORM_ATTRIBUTE_FIELD_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC
        )
    if _python_field_text(operation=operation) is None and (
        _attribute_structural_create_required(operation=operation)
    ):
        diagnostics.append(META_PYTHON_ORM_ATTRIBUTE_FIELD_UNSUPPORTED_REASON)
    else:
        diagnostics.append(META_PYTHON_ORM_ATTRIBUTE_FIELD_SPAN_MISSING_DIAGNOSTIC)
    return tuple(dict.fromkeys(diagnostics))


def _python_field_text(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    attribute_name = _attribute_name(operation=operation)
    type_text = _python_type_annotation(operation=operation, payload=operation.current)
    if attribute_name is None or type_text is None:
        return None
    default_text = _python_default_value_expression(payload=operation.current)
    suffix = f" = {default_text}" if default_text is not None else ""
    return f"    {attribute_name}: {type_text}{suffix}\n"


def _python_orm_generated_source_state(
    *,
    context: MetaPythonOrmGeneratedMaterializationContext,
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


def _python_attribute_create_insert_span(
    *,
    source_text: str,
    class_name: str,
    attribute_name: str,
) -> tuple[int, int, str] | None:
    class_node = _python_class_node(source_text=source_text, class_name=class_name)
    if class_node is None or _python_class_has_attribute(
        class_node=class_node,
        attribute_name=attribute_name,
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


def _python_attribute_delete_span(
    *,
    source_text: str,
    class_name: str,
    attribute_name: str,
) -> tuple[int, int, str] | None:
    class_node = _python_class_node(source_text=source_text, class_name=class_name)
    if class_node is None:
        return None
    attribute_node = _python_class_attribute_node(
        class_node=class_node,
        attribute_name=attribute_name,
    )
    if attribute_node is None:
        return None
    return _node_line_span(source_text=source_text, node=attribute_node)


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


def _python_class_has_attribute(
    *,
    class_node: ast.ClassDef,
    attribute_name: str,
) -> bool:
    return (
        _python_class_attribute_node(
            class_node=class_node,
            attribute_name=attribute_name,
        )
        is not None
    )


def _python_class_attribute_node(
    *,
    class_node: ast.ClassDef,
    attribute_name: str,
) -> ast.AST | None:
    for node in class_node.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == attribute_name:
                return node
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == attribute_name:
                    return node
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
    if lineno_value <= 0 or end_lineno_value <= 0 or lineno_value > len(lines):
        return None
    byte_start = len("".join(lines[: lineno_value - 1]).encode("utf-8"))
    byte_end = len("".join(lines[:end_lineno_value]).encode("utf-8"))
    before_text = source_text.encode("utf-8")[byte_start:byte_end].decode("utf-8")
    return byte_start, byte_end, before_text


def _target_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
) -> CodeGeneratedMaterializationTargetRef:
    owner_key = _owner_key(operation=operation)
    owner_name = _owner_name(operation=operation)
    raw_relative_path = (
        _generated_relative_path(operation=operation)
        or (
            context.relative_path_by_owner_key.get(owner_key)
            if owner_key is not None
            else None
        )
        or _generated_relative_path_from_source_refs(
            operation=operation,
            context=context,
        )
    )
    relative_path = _generated_target_relative_path(
        relative_path=raw_relative_path,
        context=context,
    )
    target_key = ".".join(
        part
        for part in (
            context.package_name,
            context.materialization_source,
            owner_key,
            "python_orm_model",
        )
        if part
    )
    return CodeGeneratedMaterializationTargetRef(
        target_key=target_key,
        provider_key=META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        target_language=context.target_language,
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        renderer_key=context.renderer_key,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        output_key=owner_name,
        relative_path=relative_path,
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.python_orm_target_ref",
                "operation_key": operation.operation_key,
                "owner_key": owner_key,
                "owner_name": owner_name,
            }
        ),
    )


def _generated_target_relative_path(
    *,
    relative_path: str | None,
    context: MetaPythonOrmGeneratedMaterializationContext,
) -> str | None:
    normalized = _normalized_relative_path(relative_path)
    if normalized is None:
        return None
    sources_root = _normalized_relative_path(context.sources_root)
    parts = tuple(part for part in normalized.split("/") if part)
    if sources_root is not None and (
        normalized == sources_root or normalized.startswith(f"{sources_root}/")
    ):
        return normalized
    if sources_root is not None and sources_root in parts:
        source_root_index = parts.index(sources_root)
        return "/".join(parts[source_root_index:])
    if "python" in parts:
        python_index = len(parts) - 1 - tuple(reversed(parts)).index("python")
        python_relative = "/".join(parts[python_index + 1 :])
        if python_relative:
            if sources_root is not None:
                return f"{sources_root}/{python_relative}"
            return python_relative
    if sources_root is not None:
        return f"{sources_root}/{normalized}"
    return normalized


def _python_orm_context_for_operation(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
) -> MetaPythonOrmGeneratedMaterializationContext:
    if (
        _attribute_structural_create_required(operation=operation)
        or _attribute_structural_delete_required(operation=operation)
    ) and context.renderer_key == META_PYTHON_ORM_ATTRIBUTE_TYPE_RENDERER_KEY:
        return replace(
            context,
            renderer_key=META_PYTHON_ORM_ATTRIBUTE_FIELD_RENDERER_KEY,
        )
    if (
        _attribute_default_value_changed(operation=operation)
        and context.renderer_key == META_PYTHON_ORM_ATTRIBUTE_TYPE_RENDERER_KEY
    ):
        return replace(
            context,
            renderer_key=META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_RENDERER_KEY,
        )
    return context


def _python_orm_attribute_field_key(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str:
    if _attribute_default_value_changed(operation=operation):
        return "default_value"
    return "type"


def _python_orm_context(
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> MetaPythonOrmGeneratedMaterializationContext:
    sources_root = _python_orm_sources_root(
        package_name=context.package_name,
        sources_root=context.sources_root,
    )
    return MetaPythonOrmGeneratedMaterializationContext(
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


def _generated_relative_path_from_source_refs(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
) -> str | None:
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


def _is_authored_aware_sources_root(sources_root: str | None) -> bool:
    return sources_root is None or sources_root == "aware"


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


def _section_delta_relative_path(
    *,
    relative_path: str | None,
    sources_root: str | None,
) -> str | None:
    if relative_path is None:
        return None
    normalized_relative_path = relative_path.strip().lstrip("/")
    normalized_sources_root = (
        sources_root.strip().strip("/")
        if isinstance(sources_root, str) and sources_root.strip()
        else None
    )
    if normalized_sources_root is not None and normalized_relative_path.startswith(
        f"{normalized_sources_root}/"
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


def _anchor_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
) -> CodeGeneratedRendererAnchorRef:
    owner_key = _owner_key(operation=operation)
    owner_name = _owner_name(operation=operation)
    attribute_name = _attribute_name(operation=operation)
    anchor_path = ".".join(
        part for part in (owner_name, attribute_name, "type") if part
    )
    return CodeGeneratedRendererAnchorRef(
        anchor_key=META_PYTHON_ORM_ATTRIBUTE_TYPE_ANCHOR_KEY,
        anchor_path=anchor_path,
        anchor_role="type_annotation",
        renderer_key=context.renderer_key,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        target_language=context.target_language,
        section_type="attribute",
        segment_name="type",
        graph_selector=_json_object(
            {
                "provider_key": META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
                "semantic_owner": META_PYTHON_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
                "class_fqn": owner_key,
                "class_name": owner_name,
                "attribute_name": attribute_name,
                "attribute_path": anchor_path,
            }
        ),
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.python_orm_attribute_type_anchor",
                "operation_key": operation.operation_key,
                "semantic_key": operation.semantic_key,
            }
        ),
    )


def _default_value_anchor_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
) -> CodeGeneratedRendererAnchorRef:
    owner_key = _owner_key(operation=operation)
    owner_name = _owner_name(operation=operation)
    attribute_name = _attribute_name(operation=operation)
    anchor_path = ".".join(
        part for part in (owner_name, attribute_name, "default_value") if part
    )
    return CodeGeneratedRendererAnchorRef(
        anchor_key=META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_ANCHOR_KEY,
        anchor_path=anchor_path,
        anchor_role="default_value",
        renderer_key=context.renderer_key,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        target_language=context.target_language,
        section_type="attribute",
        segment_name="default_value",
        graph_selector=_json_object(
            {
                "provider_key": META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
                "semantic_owner": META_PYTHON_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
                "class_fqn": owner_key,
                "class_name": owner_name,
                "attribute_name": attribute_name,
                "attribute_path": anchor_path,
            }
        ),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_attribute_default_value_anchor"
                ),
                "operation_key": operation.operation_key,
                "semantic_key": operation.semantic_key,
            }
        ),
    )


def _field_anchor_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmGeneratedMaterializationContext,
) -> CodeGeneratedRendererAnchorRef:
    owner_key = _owner_key(operation=operation)
    owner_name = _owner_name(operation=operation)
    attribute_name = _attribute_name(operation=operation)
    anchor_path = ".".join(
        part for part in (owner_name, attribute_name, "__field__") if part
    )
    return CodeGeneratedRendererAnchorRef(
        anchor_key=META_PYTHON_ORM_ATTRIBUTE_FIELD_ANCHOR_KEY,
        anchor_path=anchor_path,
        anchor_role="attribute_field",
        renderer_key=context.renderer_key,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        target_language=context.target_language,
        section_type="attribute",
        segment_name="field",
        graph_selector=_json_object(
            {
                "provider_key": (
                    META_PYTHON_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY
                ),
                "semantic_owner": (
                    META_PYTHON_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
                ),
                "class_fqn": owner_key,
                "class_name": owner_name,
                "attribute_name": attribute_name,
                "attribute_path": anchor_path,
            }
        ),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta." "python_orm_attribute_field_anchor"
                ),
                "operation_key": operation.operation_key,
                "semantic_key": operation.semantic_key,
            }
        ),
    )


def _attribute_structural_create_required(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    return (
        operation.ontology_subject_kind == "attribute"
        and operation.operation_family == "create"
    )


def _attribute_structural_delete_required(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    return (
        operation.ontology_subject_kind == "attribute"
        and operation.operation_family == "delete"
    )


def _attribute_type_changed(*, operation: MetaProviderDeltaTypedOperation) -> bool:
    if (
        operation.ontology_subject_kind != "attribute"
        or operation.operation_family != "update"
    ):
        return False
    current_text = _python_type_annotation(
        operation=operation, payload=operation.current
    )
    baseline_text = _python_type_annotation(
        operation=operation, payload=operation.baseline
    )
    if current_text is None:
        return bool(
            mapping_value(
                _attribute_signature(payload=operation.current).get("type_descriptor")
            )
        )
    return current_text != baseline_text


def _attribute_default_value_changed(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    if (
        operation.ontology_subject_kind != "attribute"
        or operation.operation_family != "update"
    ):
        return False
    current_raw = _default_value_raw(payload=operation.current)
    baseline_raw = _default_value_raw(payload=operation.baseline)
    if current_raw is None and baseline_raw is None:
        return False
    return _python_default_value_expression(
        payload=operation.current
    ) != _python_default_value_expression(payload=operation.baseline)


def _python_type_annotation(
    *,
    operation: MetaProviderDeltaTypedOperation,
    payload: Mapping[str, object],
) -> str | None:
    _ = operation
    signature = _attribute_signature(payload=payload)
    descriptor = mapping_value(signature.get("type_descriptor"))
    if optional_text(descriptor.get("kind")) != "primitive":
        return None
    primitive = _python_primitive_type_text(descriptor.get("primitive_base_type"))
    if primitive is None:
        return None
    rendered = (
        f"list[{primitive}]"
        if _is_collection(signature=signature, descriptor=descriptor)
        else primitive
    )
    if signature.get("is_required") is False and not rendered.startswith("list["):
        rendered = f"{rendered} | None"
    return rendered


def _python_default_value_expression(
    *,
    payload: Mapping[str, object],
) -> str | None:
    raw_value = _default_value_raw(payload=payload)
    if raw_value is None:
        return None
    parsed_value: object
    if isinstance(raw_value, str):
        try:
            parsed_value = json.loads(raw_value)
        except json.JSONDecodeError:
            return None
    else:
        parsed_value = raw_value
    return _python_literal(parsed_value)


def _python_literal(value: object) -> str | None:
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, int | float | str | list | dict):
        return repr(value)
    return None


def _default_value_raw(*, payload: Mapping[str, object]) -> object | None:
    signature = _attribute_signature(payload=payload)
    return signature.get("default_value")


def _python_primitive_type_text(value: object) -> str | None:
    raw_value = optional_text(value)
    if raw_value is None:
        return None
    key = raw_value.rsplit(".", maxsplit=1)[-1].lower()
    return _PYTHON_PRIMITIVE_TYPE_TEXT.get(key)


def _is_collection(
    *,
    signature: Mapping[str, object],
    descriptor: Mapping[str, object],
) -> bool:
    collection_kind = optional_text(descriptor.get("collection_kind")) or optional_text(
        signature.get("collection_kind")
    )
    return (
        signature.get("is_collection") is True
        or descriptor.get("is_collection") is True
        or (
            collection_kind is not None
            and collection_kind.rsplit(".", maxsplit=1)[-1].lower()
            not in {"single", "scalar", "none"}
        )
    )


def _attribute_signature(*, payload: Mapping[str, object]) -> Mapping[str, object]:
    signature = mapping_value(payload.get("attribute_signature"))
    if signature:
        return signature
    nested_payload = mapping_value(payload.get("payload"))
    signature = mapping_value(nested_payload.get("attribute_signature"))
    if signature:
        return signature
    object_payload = mapping_value(payload.get("object"))
    signature = mapping_value(object_payload.get("attribute_signature"))
    if signature:
        return signature
    baseline_object = mapping_value(payload.get("baseline_object"))
    return mapping_value(baseline_object.get("attribute_signature"))


def _attribute_name(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return (
        optional_text(operation.current.get("attribute_name"))
        or optional_text(_attribute_signature(payload=operation.current).get("name"))
        or _attribute_name_from_semantic_key(operation.semantic_key)
    )


def _attribute_name_from_semantic_key(semantic_key: str) -> str | None:
    marker = "/attribute:"
    if marker not in semantic_key:
        return None
    raw_attribute = semantic_key.rsplit(marker, maxsplit=1)[-1]
    return raw_attribute.rsplit("/", maxsplit=1)[-1].rsplit(":", maxsplit=1)[-1]


def _owner_key(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return (
        optional_text(operation.current.get("owner_key"))
        or optional_text(operation.current.get("owner_semantic_key"))
        or optional_text(
            _attribute_signature(payload=operation.current).get("owner_key")
        )
        or _owner_key_from_semantic_key(operation.semantic_key)
    )


def _owner_name(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    owner_key = _owner_key(operation=operation)
    if owner_key is None:
        return None
    return owner_key.rsplit(".", maxsplit=1)[-1]


def _owner_key_from_semantic_key(semantic_key: str) -> str | None:
    node_marker = "/node:"
    attribute_marker = "/attribute:"
    if node_marker not in semantic_key or attribute_marker not in semantic_key:
        return None
    return semantic_key.split(node_marker, maxsplit=1)[-1].split(
        attribute_marker,
        maxsplit=1,
    )[0]


def _generated_relative_path(
    *, operation: MetaProviderDeltaTypedOperation
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


def _sorted_unique(values: Iterable[str | object]) -> tuple[str, ...]:
    return tuple(sorted({text for item in values for text in tuple_text(item)}))


def _sha256_digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _json_object(payload: Mapping[str, object]) -> JsonObject:
    return JsonObject(cast(Any, dict(payload)))


__all__ = [
    "META_PYTHON_ORM_ATTRIBUTE_TYPE_ANCHOR_KEY",
    "META_PYTHON_ORM_ATTRIBUTE_TYPE_BASELINE_HASH_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_ATTRIBUTE_TYPE_EVIDENCE_ONLY_DIAGNOSTIC",
    "META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_ANCHOR_KEY",
    "META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_BASELINE_HASH_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_EVIDENCE_ONLY_DIAGNOSTIC",
    "META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_RENDERER_KEY",
    "META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_UNSUPPORTED_REASON",
    "META_PYTHON_ORM_ATTRIBUTE_FIELD_ANCHOR_KEY",
    "META_PYTHON_ORM_ATTRIBUTE_FIELD_EVIDENCE_ONLY_DIAGNOSTIC",
    "META_PYTHON_ORM_ATTRIBUTE_FIELD_RENDERER_KEY",
    "META_PYTHON_ORM_ATTRIBUTE_FIELD_SPAN_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_ATTRIBUTE_FIELD_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_ATTRIBUTE_FIELD_UNSUPPORTED_REASON",
    "META_PYTHON_ORM_ATTRIBUTE_TYPE_RENDERER_KEY",
    "META_PYTHON_ORM_ATTRIBUTE_TYPE_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_ATTRIBUTE_TYPE_UNSUPPORTED_REASON",
    "MetaPythonOrmGeneratedMaterializationContext",
    "MetaPythonOrmGeneratedMaterializationDeltaEvidence",
    "generated_materialization_feature_results_from_attribute_config_typed_operation",
    "python_orm_generated_materialization_delta_from_attribute_config_typed_operation",
]
