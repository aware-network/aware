from __future__ import annotations

import ast
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from aware_meta.materialization.deltas.code_dto import (
    CodeGrammarAnchorRenderReplacement,
    CodeGrammarAnchorRenderTargetKind,
    CodeGraphFieldSelector,
    CodeLanguage,
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
    CodeNestedMemberInsertAnchor,
    CodePackageDelta,
    CodePackageDeltaAuthorityKind,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
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
    tuple_mappings,
    tuple_text,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaGeneratedMaterializationContext,
    MetaProviderDeltaGeneratedMaterializationFeatureResult,
    meta_provider_delta_world_change_event_key,
)
from aware_meta.materialization.deltas.generated_materialization_dispatch import (
    explicit_language_generated_materialization_feature_result,
)
from aware_meta.materialization.deltas.generated_materialization_spans import (
    MetaGeneratedMaterializationTextSpanContext,
    meta_generated_materialization_correlated_text_span_render_delta,
    meta_generated_materialization_text_span_replacement,
    missing_correlated_text_span_names,
)
from aware_meta.materialization.deltas.language_renderer_contracts import (
    MetaLanguageGeneratedMaterializationDeltaContext,
    MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    MetaLanguageGeneratedMaterializationDeltaRenderResult,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_code_ontology.code.code_enums import CodeLanguage as MetaPluginCodeLanguage
from aware_types import JsonObject, canonical_decimal_text
from python_grammar.renderer_delta_orm_targets import (
    ORM_RUNTIME_PRODUCT_INTENT,
    orm_runtime_target_payload,
)

try:
    from aware_grammar.function.parser import (
        FunctionParseError,
        parse_function_statements_from_block,
    )
except Exception:  # pragma: no cover - import fallback for partial runtimes
    FunctionParseError = ValueError
    parse_function_statements_from_block = None


META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY = "aware_meta"
META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER = "aware_meta.ocg"
META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PRODUCT_INTENT = (
    ORM_RUNTIME_PRODUCT_INTENT
)
META_PYTHON_ORM_FUNCTION_RENDERER_PROFILE = "orm_runtime"
META_PYTHON_ORM_FUNCTION_MATERIALIZATION_SOURCE = "ontology_orm_models"
META_PYTHON_ORM_FUNCTION_RENDERER_KEY = "python.orm.function"
META_PYTHON_ORM_FUNCTION_INVOCATION_RENDERER_KEY = "python.orm.function.invocation_plan"
META_PYTHON_ORM_FUNCTION_ANCHOR_KEY = "python.orm.function.section"
META_PYTHON_ORM_FUNCTION_INVOCATION_ANCHOR_KEY = "python.orm.function.invocation_plan"
META_PYTHON_ORM_FUNCTION_EVIDENCE_ONLY_DIAGNOSTIC = (
    "meta_python_orm_function_generated_materialization_renderer_operation_"
    "evidence_only"
)
META_PYTHON_ORM_FUNCTION_GUARDED_DELTA_MISSING_DIAGNOSTIC = (
    "meta_python_orm_function_generated_materialization_guarded_delta_missing"
)
META_PYTHON_ORM_FUNCTION_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC = (
    "meta_python_orm_function_generated_materialization_target_relative_path_" "missing"
)
META_PYTHON_ORM_FUNCTION_INVOCATION_BASELINE_BODY_MISSING_DIAGNOSTIC = (
    "meta_python_orm_function_invocation_generated_materialization_baseline_"
    "body_missing"
)
META_PYTHON_ORM_FUNCTION_INVOCATION_BODY_MISSING_DIAGNOSTIC = (
    "meta_python_orm_function_invocation_generated_materialization_body_missing"
)
META_PYTHON_ORM_FUNCTION_UPDATE_UNSUPPORTED_DIAGNOSTIC = (
    "meta_python_orm_function_update_generated_materialization_"
    "unsupported_segment_shape"
)
META_PYTHON_ORM_FUNCTION_UPDATE_BODY_MISSING_DIAGNOSTIC = (
    "meta_python_orm_function_update_generated_materialization_body_missing"
)
META_PYTHON_ORM_FUNCTION_SIGNATURE_SPAN_MISSING_DIAGNOSTIC = (
    "meta_python_orm_function_signature_generated_materialization_span_missing"
)
META_PYTHON_ORM_FUNCTION_SIGNATURE_TEXT_MISSING_DIAGNOSTIC = (
    "meta_python_orm_function_signature_generated_materialization_text_missing"
)
META_PYTHON_ORM_FUNCTION_SIGNATURE_PAYLOAD_SPAN_MISSING_DIAGNOSTIC = (
    "meta_python_orm_function_signature_generated_materialization_payload_span_missing"
)
META_PYTHON_ORM_FUNCTION_SIGNATURE_INPUT_MODEL_SPAN_MISSING_DIAGNOSTIC = "meta_python_orm_function_signature_generated_materialization_input_model_span_missing"
META_PYTHON_ORM_FUNCTION_DELETE_SPAN_MISSING_DIAGNOSTIC = (
    "meta_python_orm_function_delete_generated_materialization_span_missing"
)
META_PYTHON_ORM_FUNCTION_NOT_REQUIRED_REASON = (
    "meta_python_orm_function_generated_materialization_not_required"
)
PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME = "python_orm_runtime"

_PYTHON_PRIMITIVE_TYPE_TEXT = {
    "any": "Any",
    "boolean": "bool",
    "bool": "bool",
    "bytes": "bytes",
    "datetime": "datetime",
    "date_time": "datetime",
    "decimal": "Annotated[Decimal, DecimalWire()]",
    "float": "float",
    "integer": "int",
    "int": "int",
    "json": "JsonObject",
    "string": "str",
    "uuid": "UUID",
    "vector": "list",
}


@dataclass(frozen=True, slots=True)
class MetaPythonOrmFunctionGeneratedMaterializationContext:
    package_name: str | None = None
    package_root: str | None = None
    sources_root: str | None = None
    target_language: str = "python"
    renderer_profile: str = META_PYTHON_ORM_FUNCTION_RENDERER_PROFILE
    materialization_source: str = META_PYTHON_ORM_FUNCTION_MATERIALIZATION_SOURCE
    artifact_family: str = "ocg_language_materialization"
    artifact_role: str = "python_orm_model"


@dataclass(frozen=True, slots=True)
class MetaPythonOrmFunctionGeneratedMaterializationDeltaEvidence:
    delta_request: CodeGeneratedMaterializationDeltaRequest
    result: CodeGeneratedMaterializationDeltaResult


@dataclass(frozen=True, slots=True)
class _PythonOrmFunctionSectionDeltaEvidence:
    section_delta: CodeSectionDeltaSet | None
    renderer_operation_kind: CodeGeneratedRendererDeltaOperationKind
    content_text: str | None
    mode_reason: str
    package_delta: CodePackageDelta | None = None
    grammar_anchor_render_delta: ResolveCodeGrammarAnchorRenderDeltaRequest | None = (
        None
    )
    renderer_operations: tuple[CodeGeneratedRendererDeltaOperation, ...] = ()
    before_hash: str | None = None
    after_hash: str | None = None


@dataclass(frozen=True, slots=True)
class _PythonOrmGeneratedSourceState:
    package_root: str
    relative_path: str
    source_text: str


def supports_python_orm_function_generated_delta(
    request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
) -> bool:
    operation = request.operation
    if operation.ontology_subject_kind == "function":
        return operation.operation_family in {"create", "delete", "update"}
    if operation.ontology_subject_kind == "function_invocation":
        return operation.operation_family == "create"
    if operation.ontology_subject_kind == "function_membership":
        return True
    return False


def render_python_orm_function_generated_delta(
    request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
) -> MetaLanguageGeneratedMaterializationDeltaRenderResult:
    if not supports_python_orm_function_generated_delta(request):
        return MetaLanguageGeneratedMaterializationDeltaRenderResult.unhandled(
            reason="python_orm_function_generated_delta_operation_not_supported",
        )
    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            request.operation,
            context=_context_with_defaults(request.context),
            allow_language_plugin=False,
            language_plugin_delta_renderer=PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME,
        )
    )
    return MetaLanguageGeneratedMaterializationDeltaRenderResult.from_evidence(
        delta_request=evidence.delta_request,
        result=evidence.result,
        reason="python_orm_runtime_function_generated_delta_rendered",
    )


def _context_with_defaults(
    context: MetaLanguageGeneratedMaterializationDeltaContext,
) -> MetaPythonOrmFunctionGeneratedMaterializationContext:
    normalized_context = _python_orm_function_context(
        MetaProviderDeltaGeneratedMaterializationContext(
            package_name=context.package_name,
            package_root=context.package_root,
            sources_root=context.sources_root,
            target_language=context.target_language,
        )
    )
    return MetaPythonOrmFunctionGeneratedMaterializationContext(
        package_name=normalized_context.package_name,
        package_root=normalized_context.package_root,
        sources_root=normalized_context.sources_root,
        target_language=normalized_context.target_language,
        renderer_profile=(
            context.renderer_profile or META_PYTHON_ORM_FUNCTION_RENDERER_PROFILE
        ),
        materialization_source=(
            context.materialization_source
            or META_PYTHON_ORM_FUNCTION_MATERIALIZATION_SOURCE
        ),
        artifact_family=context.artifact_family or "ocg_language_materialization",
        artifact_role=context.artifact_role or "python_orm_model",
    )


def generated_materialization_feature_results_from_function_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> tuple[MetaProviderDeltaGeneratedMaterializationFeatureResult, ...]:
    if operation.ontology_subject_kind not in {
        "function",
        "function_invocation",
        "function_membership",
    }:
        return (
            MetaProviderDeltaGeneratedMaterializationFeatureResult.skipped(
                feature_key="function_config",
                operation=operation,
                reason=(
                    "meta_python_orm_function_generated_materialization_"
                    "subject_not_supported"
                ),
                event_refs=(
                    meta_provider_delta_world_change_event_key(operation=operation),
                ),
            ),
        )

    dispatched = explicit_language_generated_materialization_feature_result(
        feature_key="function_config",
        operation=operation,
        context=context,
    )
    if dispatched is not None:
        return (dispatched,)

    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            operation,
            context=_python_orm_function_context(context),
        )
    )
    return (
        MetaProviderDeltaGeneratedMaterializationFeatureResult.from_evidence(
            feature_key="function_config",
            operation=operation,
            delta_request=evidence.delta_request,
            result=evidence.result,
            reason="meta_python_orm_function_generated_materialization_evidence_built",
        ),
    )


def python_orm_generated_materialization_delta_from_function_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    *,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext | None = None,
    allow_language_plugin: bool = True,
    language_plugin_delta_renderer: str | None = None,
) -> MetaPythonOrmFunctionGeneratedMaterializationDeltaEvidence:
    """Build read-only Python ORM generated-materialization delta evidence."""

    resolved_context = context or MetaPythonOrmFunctionGeneratedMaterializationContext()
    if allow_language_plugin:
        plugin_evidence = _python_orm_function_plugin_delta_evidence(
            operation=operation,
            context=resolved_context,
        )
        if plugin_evidence is not None:
            return plugin_evidence
    event_key = meta_provider_delta_world_change_event_key(operation=operation)
    target = _target_ref(operation=operation, context=resolved_context)
    request = CodeGeneratedMaterializationDeltaRequest(
        provider_key=META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=(
            META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
        ),
        package_name=resolved_context.package_name,
        package_root=resolved_context.package_root,
        sources_root=resolved_context.sources_root,
        product_intent=(
            META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PRODUCT_INTENT
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
                        "provider_operation_type": (operation.provider_operation_type),
                    }
                ),
            )
        ],
        action_bindings=[
            CodeGeneratedMaterializationActionBinding(
                action_key=(
                    "aware_meta.python_orm.function.generated_materialization."
                    f"{operation.operation_key}"
                ),
                event_key=event_key,
                target=target,
                policy_key=_policy_key(operation=operation),
                renderer_key=_renderer_key(operation=operation),
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.provider_delta."
                            "python_orm_function_generated_materialization_action"
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
                    "python_orm_function_generated_materialization_delta_request"
                ),
                "renderer_profile": resolved_context.renderer_profile,
                "materialization_source": resolved_context.materialization_source,
                **_language_plugin_metadata(language_plugin_delta_renderer),
            }
        ),
    )
    result = _python_orm_function_generated_materialization_result(
        operation=operation,
        context=resolved_context,
        event_key=event_key,
        target=target,
        language_plugin_delta_renderer=language_plugin_delta_renderer,
    )
    return MetaPythonOrmFunctionGeneratedMaterializationDeltaEvidence(
        delta_request=request,
        result=result,
    )


def _python_orm_function_plugin_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
) -> MetaPythonOrmFunctionGeneratedMaterializationDeltaEvidence | None:
    if operation.ontology_subject_kind not in {
        "function",
        "function_invocation",
        "function_membership",
    }:
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
    return MetaPythonOrmFunctionGeneratedMaterializationDeltaEvidence(
        delta_request=render_result.delta_request,
        result=render_result.result,
    )


def _language_delta_context(
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
) -> MetaLanguageGeneratedMaterializationDeltaContext:
    return MetaLanguageGeneratedMaterializationDeltaContext(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        target_language=context.target_language,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        product_intent=META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PRODUCT_INTENT,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
    )


def _meta_plugin_code_language(value: str) -> MetaPluginCodeLanguage:
    try:
        return MetaPluginCodeLanguage(value)
    except ValueError:
        return MetaPluginCodeLanguage.python


def _python_orm_function_generated_materialization_result(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
    language_plugin_delta_renderer: str | None = None,
) -> CodeGeneratedMaterializationDeltaResult:
    if not _requires_generated_materialization_policy(operation=operation):
        return CodeGeneratedMaterializationDeltaResult(
            provider_key=(
                META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY
            ),
            semantic_owner=(
                META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
            ),
            available=True,
            mode=CodeGeneratedMaterializationDeltaMode.not_required,
            skipped_targets=[
                CodeGeneratedMaterializationSkippedTarget(
                    target=target,
                    reason=META_PYTHON_ORM_FUNCTION_NOT_REQUIRED_REASON,
                    event_refs=[event_key],
                )
            ],
        )

    section_delta_evidence = _python_orm_function_section_delta_evidence(
        operation=operation,
        context=context,
        target=target,
        event_key=event_key,
    )
    has_resolvable_section_delta_evidence = (
        section_delta_evidence is not None
        and section_delta_evidence.section_delta is not None
    )
    has_resolvable_package_delta_evidence = (
        section_delta_evidence is not None
        and section_delta_evidence.package_delta is not None
    )
    has_resolvable_grammar_anchor_render_evidence = (
        section_delta_evidence is not None
        and section_delta_evidence.grammar_anchor_render_delta is not None
    )
    has_resolvable_delta_evidence = (
        has_resolvable_package_delta_evidence
        or has_resolvable_section_delta_evidence
        or has_resolvable_grammar_anchor_render_evidence
    )
    diagnostics = (
        ()
        if has_resolvable_delta_evidence
        else _python_orm_function_guarded_delta_diagnostics(
            operation=operation,
            context=context,
            target=target,
        )
    )
    entry_mode = (
        (
            CodeGeneratedMaterializationDeltaMode.package_delta_ready
            if has_resolvable_package_delta_evidence
            else (
                CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
                if has_resolvable_grammar_anchor_render_evidence
                else CodeGeneratedMaterializationDeltaMode.section_delta_ready
            )
        )
        if has_resolvable_delta_evidence
        else CodeGeneratedMaterializationDeltaMode.fallback_full_render
    )
    renderer_operation_kind = (
        section_delta_evidence.renderer_operation_kind
        if section_delta_evidence is not None
        else CodeGeneratedRendererDeltaOperationKind.fallback_full_render
    )
    content_text = (
        section_delta_evidence.content_text
        if section_delta_evidence is not None
        else None
    )
    before_hash = (
        section_delta_evidence.before_hash
        if section_delta_evidence is not None
        else None
    )
    after_hash = (
        section_delta_evidence.after_hash
        if section_delta_evidence is not None
        else (_sha256_digest(content_text) if content_text is not None else None)
    )
    mode_reason = (
        section_delta_evidence.mode_reason
        if section_delta_evidence is not None
        else (
            "function_generated_materialization_policy_ready_" "guarded_delta_missing"
        )
    )
    renderer_operations = (
        list(section_delta_evidence.renderer_operations)
        if section_delta_evidence is not None
        and section_delta_evidence.renderer_operations
        else [
            CodeGeneratedRendererDeltaOperation(
                operation_key=f"aware_meta.python_orm.function:{operation.operation_key}",
                kind=renderer_operation_kind,
                target=target,
                anchor=_anchor_ref(operation=operation, context=context),
                renderer_key=_renderer_key(operation=operation),
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
                            "python_orm_function_renderer_operation"
                        ),
                        "operation_key": operation.operation_key,
                        "operation_family": operation.operation_family,
                        "provider_operation_type": operation.provider_operation_type,
                        "mode_reason": mode_reason,
                        **_language_plugin_metadata(language_plugin_delta_renderer),
                    }
                ),
            )
        ]
    )
    entry = CodeGeneratedMaterializationDeltaEntry(
        entry_key=f"aware_meta.python_orm.function:{operation.operation_key}",
        mode=entry_mode,
        target=target,
        package_delta=(
            section_delta_evidence.package_delta
            if section_delta_evidence is not None
            else None
        ),
        section_delta=(
            section_delta_evidence.section_delta
            if section_delta_evidence is not None
            else None
        ),
        grammar_anchor_render_delta=(
            section_delta_evidence.grammar_anchor_render_delta
            if section_delta_evidence is not None
            else None
        ),
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        artifact_key=target.target_key,
        relative_path=target.relative_path,
        before_hash=before_hash,
        after_hash=after_hash,
        renderer_operations=renderer_operations,
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        diagnostics=list(diagnostics),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_function_generated_materialization_delta_entry"
                ),
                "operation_key": operation.operation_key,
                "package_delta_emitted": has_resolvable_package_delta_evidence,
                "section_delta_emitted": has_resolvable_section_delta_evidence,
                "grammar_anchor_render_delta_emitted": (
                    has_resolvable_grammar_anchor_render_evidence
                ),
                "mode_reason": mode_reason,
                **_language_plugin_metadata(language_plugin_delta_renderer),
            }
        ),
    )
    return CodeGeneratedMaterializationDeltaResult(
        provider_key=META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=(
            META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
        ),
        available=True,
        mode=entry_mode,
        entries=[entry],
        diagnostics=list(diagnostics),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_function_generated_materialization_delta_result"
                ),
                "operation_key": operation.operation_key,
                "renderer_operation_count": len(renderer_operations),
                "package_delta_emitted": has_resolvable_package_delta_evidence,
                "section_delta_emitted": has_resolvable_section_delta_evidence,
                "grammar_anchor_render_delta_emitted": (
                    has_resolvable_grammar_anchor_render_evidence
                ),
                **_language_plugin_metadata(language_plugin_delta_renderer),
            }
        ),
    )


def _python_orm_function_section_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmFunctionSectionDeltaEvidence | None:
    if operation.ontology_subject_kind == "function_invocation":
        return _python_orm_function_invocation_section_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    if operation.operation_family == "update":
        return _python_orm_function_update_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    if operation.operation_family == "delete":
        return _python_orm_function_delete_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    return _python_orm_function_create_section_delta_evidence(
        operation=operation,
        context=context,
        target=target,
        event_key=event_key,
    )


def _python_orm_function_create_section_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmFunctionSectionDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "function"
        or operation.operation_family != "create"
        or target.relative_path is None
    ):
        return None
    package_delta_evidence = _python_orm_function_create_package_delta_evidence(
        operation=operation,
        context=context,
        target=target,
        event_key=event_key,
    )
    if package_delta_evidence is not None:
        return package_delta_evidence
    function_name = _function_name(operation=operation)
    owner_name = _owner_name(operation=operation)
    inserted_text = _python_orm_function_create_content_text(operation=operation)
    if function_name is None or owner_name is None or inserted_text is None:
        return None
    relative_path = _section_delta_relative_path(
        relative_path=target.relative_path,
        sources_root=context.sources_root,
    )
    member_qualname = ".".join(part for part in (owner_name, function_name) if part)
    section_delta = CodeSectionDeltaSet(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        entries=[
            CodeSectionDeltaEntry(
                operation=CodeSectionDeltaOperationKind.insert_after_section,
                section_ref=CodeSectionRef(
                    package_name=context.package_name,
                    relative_path=relative_path or "",
                    language=context.target_language,
                    section_type="class",
                    qualname=owner_name,
                    semantic_key=_owner_semantic_key(operation=operation),
                    source_refs=list(_sorted_unique(operation.source_refs)),
                    metadata=_json_object(
                        {
                            "source": (
                                "aware_meta.provider_delta."
                                "python_orm_function_parent_section_ref"
                            ),
                            "operation_key": operation.operation_key,
                            "target_relative_path": target.relative_path,
                        }
                    ),
                ),
                nested_member_insert_anchor=CodeNestedMemberInsertAnchor(
                    member_section_type="function",
                    member_qualname=member_qualname or None,
                ),
                content_text=inserted_text,
                after_hash=_sha256_digest(inserted_text),
                event_ref=event_key,
                semantic_key=operation.semantic_key,
                provider_key=(
                    META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY
                ),
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.provider_delta."
                            "python_orm_function_create_section_delta"
                        ),
                        "operation_key": operation.operation_key,
                        "renderer_key": _renderer_key(operation=operation),
                        "renderer_profile": context.renderer_profile,
                    }
                ),
            )
        ],
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_function_generated_materialization_section_delta_set"
                ),
                "operation_key": operation.operation_key,
                "renderer_key": _renderer_key(operation=operation),
                "renderer_profile": context.renderer_profile,
            }
        ),
    )
    return _PythonOrmFunctionSectionDeltaEvidence(
        section_delta=section_delta,
        renderer_operation_kind=CodeGeneratedRendererDeltaOperationKind.insert_section,
        content_text=inserted_text,
        mode_reason="python_orm_function_create_nested_section_delta_ready",
        after_hash=_sha256_digest(inserted_text),
    )


def _python_orm_function_create_package_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmFunctionSectionDeltaEvidence | None:
    source_state = _python_orm_generated_source_state(context=context, target=target)
    if source_state is None:
        return None
    updated_text = _python_orm_function_create_updated_source_text(
        operation=operation,
        context=context,
        source_text=source_state.source_text,
    )
    if updated_text is None or updated_text == source_state.source_text:
        return None
    before_hash = _sha256_digest(source_state.source_text)
    after_hash = _sha256_digest(updated_text)
    package_delta = CodePackageDelta(
        package_name=context.package_name,
        package_root=source_state.package_root,
        sources_root=context.sources_root,
        authority=CodePackageDeltaAuthorityKind.code_package_delta,
        authority_kind=CodePackageDeltaAuthorityKind.code_package_delta.value,
        paths=[
            CodePackageDeltaPath(
                relative_path=source_state.relative_path,
                kind=CodePackageDeltaKind.update,
                content_text=updated_text,
                before_hash=before_hash,
                after_hash=after_hash,
                size_bytes=len(updated_text.encode("utf-8")),
                language=CodeLanguage.python,
                is_structural=True,
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.provider_delta."
                            "python_orm_function_create_package_delta_path"
                        ),
                        "operation_key": operation.operation_key,
                        "renderer_key": _renderer_key(operation=operation),
                        "renderer_profile": context.renderer_profile,
                    }
                ),
            )
        ],
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_function_create_package_delta"
                ),
                "operation_key": operation.operation_key,
                "renderer_key": _renderer_key(operation=operation),
                "renderer_profile": context.renderer_profile,
            }
        ),
    )
    renderer_operations = _python_orm_function_create_renderer_operations(
        operation=operation,
        context=context,
        target=target,
        event_key=event_key,
        before_hash=before_hash,
        after_hash=after_hash,
        updated_text=updated_text,
    )
    return _PythonOrmFunctionSectionDeltaEvidence(
        package_delta=package_delta,
        section_delta=None,
        renderer_operation_kind=CodeGeneratedRendererDeltaOperationKind.insert_section,
        content_text=updated_text,
        mode_reason="python_orm_function_create_package_delta_ready",
        renderer_operations=renderer_operations,
        before_hash=before_hash,
        after_hash=after_hash,
    )


def _python_orm_function_create_updated_source_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    source_text: str,
) -> str | None:
    source_without_registry = _python_orm_strip_empty_function_registry(
        source_text=source_text,
    )
    if source_without_registry is None:
        return None
    owner_name = _owner_name(operation=operation)
    function_name = _function_name(operation=operation)
    if owner_name is None or function_name is None:
        return None
    method_text = _python_orm_function_create_facade_method_text(
        operation=operation,
    )
    io_text = _python_orm_function_create_io_model_text(operation=operation)
    registry_text = _python_orm_function_create_registry_text(operation=operation)
    if method_text is None or io_text is None or registry_text is None:
        return None
    if _python_top_level_class_exists(
        source_text=source_without_registry,
        class_name=(
            _python_orm_function_input_model_name(
                owner_name=owner_name,
                function_name=function_name,
            )
        ),
    ):
        return None
    class_span = _python_top_level_class_span(
        source_text=source_without_registry,
        class_name=owner_name,
    )
    if class_span is None:
        return None
    class_start, class_end = class_span
    class_text = source_without_registry.encode("utf-8")[class_start:class_end].decode(
        "utf-8"
    )
    updated_class_text = _python_orm_insert_method_in_class_text(
        class_text=class_text,
        method_text=method_text,
        function_name=function_name,
    )
    if updated_class_text is None:
        return None
    source_bytes = source_without_registry.encode("utf-8")
    updated_bytes = (
        source_bytes[:class_start]
        + _python_append_top_level_after_class(
            class_text=updated_class_text,
            top_level_text=io_text,
        ).encode("utf-8")
        + source_bytes[class_end:]
    )
    updated_text = updated_bytes.decode("utf-8")
    updated_text = _python_orm_ensure_function_imports(
        source_text=updated_text,
        is_constructor=_function_is_constructor(operation=operation),
        operation=operation,
        context=context,
    )
    return f"{updated_text.rstrip()}\n\n\n{registry_text}"


def _python_orm_strip_empty_function_registry(*, source_text: str) -> str | None:
    registry_start = source_text.find("\n\nFUNCTIONS = {")
    if registry_start < 0:
        return source_text
    registry_tail = source_text[registry_start:].strip()
    if '"canonical"' in registry_tail or '"input"' in registry_tail:
        return None
    if "__all__ = [" not in registry_tail:
        return None
    return source_text[:registry_start].rstrip() + "\n"


def _python_orm_function_create_facade_method_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    owner_name = _owner_name(operation=operation)
    function_name = _function_name(operation=operation)
    signature = _function_signature(payload=operation.current)
    if owner_name is None or function_name is None or not signature:
        return None
    is_constructor = _function_is_constructor(operation=operation)
    input_texts: list[str] = []
    payload_items: list[str] = []
    for input_signature in _function_signature_inputs(
        operation=operation,
        payload=operation.current,
    ):
        input_text = _python_function_input_text(input_signature, model_field=False)
        name = optional_text(input_signature.get("name"))
        if input_text is None or name is None:
            return None
        input_texts.append(input_text)
        payload_items.append(f"{_python_double_quoted(name)}: {name}")
    output_signatures = tuple_mappings(signature.get("outputs"))
    input_model_name, output_model_name = _python_orm_function_io_model_names(
        owner_name=owner_name,
        function_name=function_name,
    )
    _ = input_model_name
    return_type = _python_orm_function_return_type_text(
        operation=operation,
        output_model_name=output_model_name,
        outputs=output_signatures,
    )
    if return_type is None:
        return None
    receiver = "cls" if is_constructor else "self"
    invocation_name = "invoke_constructor" if is_constructor else "invoke_instance"
    invocation_receiver = "orm_class=cls" if is_constructor else "orm_model=self"
    signature_args = _python_function_signature_args_text(
        receiver=receiver,
        input_texts=tuple(input_texts),
    )
    description = optional_text(signature.get("description"))
    lines: list[str] = []
    if is_constructor:
        lines.append("    @classmethod")
    if "\n" in signature_args:
        lines.append(f"    async def {function_name}(")
        lines.append(signature_args)
        lines.append(f"    ) -> {return_type}:")
    else:
        lines.append(
            f"    async def {function_name}({signature_args}) -> {return_type}:"
        )
    if description is not None:
        lines.extend(_python_docstring_lines(description, indent="        "))
        lines.append("")
    payload_literal = "{" + ", ".join(payload_items) + "}"
    lines.append(f"        payload = {payload_literal}")
    if not output_signatures:
        lines.append(
            f"        await {invocation_name}("
            f"{invocation_receiver}, function_name={_python_double_quoted(function_name)}, "
            "payload=payload)"
        )
        lines.append("        return None")
        return "\n".join(lines) + "\n"
    lines.append(
        f"        result = await {invocation_name}("
        f"{invocation_receiver}, function_name={_python_double_quoted(function_name)}, "
        "payload=payload)"
    )
    if len(output_signatures) > 1:
        lines.append(f"        if isinstance(result, {output_model_name}):")
        lines.append("            return result")
        lines.append(f"        return {output_model_name}.model_validate(result)")
        return "\n".join(lines) + "\n"
    if len(output_signatures) != 1:
        return None
    output_signature = output_signatures[0]
    output_name = optional_text(output_signature.get("name"))
    if output_name is None:
        return None
    lines.append(
        f"        value = result.get({_python_double_quoted(output_name)}) "
        "if isinstance(result, dict) "
        f"and {_python_double_quoted(output_name)} in result else result"
    )
    output_type = _python_type_text_from_signature(output_signature)
    if output_type is None:
        return None
    if _signature_is_optional(output_signature):
        lines.append("        if value is None:")
        lines.append("            return None")
    lines.append(f"        if isinstance(value, {output_type}):")
    lines.append("            return value")
    if _signature_type_descriptor_kind(output_signature) == "class":
        lines.append(f"        return {output_type}.validate_invocation_value(value)")
    elif _signature_type_descriptor_kind(output_signature) == "enum":
        lines.append(f"        return {output_type}(value)")
    else:
        lines.append("        return value")
    return "\n".join(lines) + "\n"


def _python_function_signature_args_text(
    *,
    receiver: str,
    input_texts: tuple[str, ...],
) -> str:
    single_line = ", ".join((receiver, *input_texts))
    if len(single_line) <= 88:
        return single_line
    return "\n".join(f"        {text}," for text in (receiver, *input_texts))


def _python_orm_function_create_io_model_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    owner_name = _owner_name(operation=operation)
    function_name = _function_name(operation=operation)
    if owner_name is None or function_name is None:
        return None
    input_model_name, output_model_name = _python_orm_function_io_model_names(
        owner_name=owner_name,
        function_name=function_name,
    )
    input_body = _python_orm_function_input_model_body_text(
        operation=operation,
        payload=operation.current,
    )
    output_body = _python_orm_function_output_model_body_text(
        operation=operation,
        payload=operation.current,
    )
    if input_body is None or output_body is None:
        return None
    return (
        f"class {input_model_name}(BaseModel):\n"
        f"{input_body}\n\n\n"
        f"class {output_model_name}(BaseModel):\n"
        f"{output_body}\n"
    )


def _python_orm_function_create_registry_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    owner_name = _owner_name(operation=operation)
    function_name = _function_name(operation=operation)
    signature = _function_signature(payload=operation.current)
    if owner_name is None or function_name is None or not signature:
        return None
    input_model_name, output_model_name = _python_orm_function_io_model_names(
        owner_name=owner_name,
        function_name=function_name,
    )
    description = optional_text(signature.get("description"))
    canonical_text = _python_orm_function_registry_canonical_text(
        function_name=function_name,
        description=description,
        is_constructor=_function_is_constructor(operation=operation),
    )
    return (
        "FUNCTIONS = {\n"
        f"    {_python_double_quoted(owner_name)}: {{\n"
        f"        {_python_double_quoted(function_name)}: {{\n"
        f"            {_python_double_quoted('canonical')}: {canonical_text},\n"
        f"            {_python_double_quoted('input')}: {input_model_name},\n"
        f"            {_python_double_quoted('output')}: {output_model_name},\n"
        "        },\n"
        "    },\n"
        "}\n\n"
        "__all__ = [\n"
        f"    {_python_double_quoted(owner_name)},\n"
        f"    {_python_double_quoted(input_model_name)},\n"
        f"    {_python_double_quoted(output_model_name)},\n"
        f"    {_python_double_quoted('FUNCTIONS')},\n"
        "]\n"
    )


def _python_orm_function_registry_canonical_text(
    *,
    function_name: str,
    description: str | None,
    is_constructor: bool,
) -> str:
    if description is None or "\n" not in description:
        return (
            "{"
            f'"name": {_python_double_quoted(function_name)}, '
            f'"description": {_python_python_literal(description)}, '
            f'"is_constructor": {_python_bool_literal(is_constructor)}'
            "}"
        )
    return (
        "{\n"
        f"                {_python_double_quoted('name')}: {_python_double_quoted(function_name)},\n"
        f"                {_python_double_quoted('description')}: {_python_python_literal(description)},\n"
        f"                {_python_double_quoted('is_constructor')}: "
        f"{_python_bool_literal(is_constructor)},\n"
        "            }"
    )


def _python_orm_function_output_model_body_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
    payload: Mapping[str, object],
) -> str | None:
    signature = _function_signature(payload=payload)
    if not signature and payload is operation.baseline:
        signature = _function_signature(payload=operation.current)
    lines: list[str] = []
    for output_signature in sorted(
        tuple_mappings(signature.get("outputs")),
        key=_function_attribute_sort_key,
    ):
        output_text = _python_function_input_text(output_signature, model_field=True)
        if output_text is None:
            return None
        lines.append(f"    {output_text}")
    if not lines:
        return "    pass"
    return "\n".join(lines)


def _python_orm_function_return_type_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
    output_model_name: str,
    outputs: tuple[dict[str, object], ...],
) -> str | None:
    if not outputs:
        return "None"
    if len(outputs) > 1:
        return output_model_name
    return _python_function_return_text(outputs)


def _python_orm_insert_method_in_class_text(
    *,
    class_text: str,
    method_text: str,
    function_name: str,
) -> str | None:
    if method_text.strip() in class_text:
        return None
    replaced = _python_orm_replace_stub_method_in_class_text(
        class_text=class_text,
        method_text=method_text,
        function_name=function_name,
    )
    if replaced is not None:
        return replaced
    return f"{class_text.rstrip()}\n\n{method_text.rstrip()}\n"


def _python_orm_replace_stub_method_in_class_text(
    *,
    class_text: str,
    method_text: str,
    function_name: str,
) -> str | None:
    try:
        tree = ast.parse(class_text)
    except SyntaxError:
        return None
    class_node = next(
        (node for node in tree.body if isinstance(node, ast.ClassDef)), None
    )
    if class_node is None:
        return None
    for child in class_node.body:
        if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if child.name != function_name or not _python_function_body_is_not_implemented(
            child
        ):
            continue
        start_line = (
            child.decorator_list[0].lineno if child.decorator_list else child.lineno
        )
        end_line = getattr(child, "end_lineno", None)
        if not isinstance(end_line, int):
            return None
        lines = class_text.splitlines(keepends=True)
        byte_start = len("".join(lines[: max(start_line - 1, 0)]).encode("utf-8"))
        byte_end = len("".join(lines[:end_line]).encode("utf-8"))
        class_bytes = class_text.encode("utf-8")
        return (
            class_bytes[:byte_start]
            + method_text.rstrip().encode("utf-8")
            + b"\n"
            + class_bytes[byte_end:]
        ).decode("utf-8")
    return None


def _python_function_body_is_not_implemented(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    return any(
        isinstance(statement, ast.Raise) and _python_raise_is_not_implemented(statement)
        for statement in node.body
    )


def _python_raise_is_not_implemented(statement: ast.Raise) -> bool:
    if isinstance(statement.exc, ast.Call) and isinstance(statement.exc.func, ast.Name):
        return statement.exc.func.id == "NotImplementedError"
    return (
        isinstance(statement.exc, ast.Name)
        and statement.exc.id == "NotImplementedError"
    )


def _python_append_top_level_after_class(
    *,
    class_text: str,
    top_level_text: str,
) -> str:
    return f"{class_text.rstrip()}\n\n\n{top_level_text.rstrip()}\n"


def _python_orm_ensure_function_imports(
    *,
    source_text: str,
    is_constructor: bool,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
) -> str:
    updated = _python_ensure_import(
        source_text=source_text,
        group_header="# Third-party",
        import_line="from pydantic import BaseModel",
        before_group_header="# Orm",
    )
    if "Field(" in updated:
        updated = _python_ensure_import(
            source_text=updated,
            group_header="# Third-party",
            import_line="from pydantic import Field",
            before_group_header="# Orm",
        )
    invocation_symbol = "invoke_constructor" if is_constructor else "invoke_instance"
    updated = _python_ensure_import(
        source_text=updated,
        group_header="# Orm",
        import_line=f"from aware_orm.runtime.invocation import {invocation_symbol}",
        after_import_prefix="from aware_orm.models.orm_model import ORMModel",
    )
    for import_line in _python_function_descriptor_import_lines(
        operation=operation,
        context=context,
    ):
        imported_name = _python_imported_symbol_name(import_line=import_line)
        if imported_name is not None and (
            f"class {imported_name}(" in updated or f"class {imported_name}:" in updated
        ):
            continue
        updated = _python_ensure_import(
            source_text=updated,
            group_header=_python_import_group_header(import_line),
            import_line=import_line,
            before_group_header=(
                "# Types" if import_line.startswith("from aware_types ") else None
            ),
        )
    return _python_normalize_import_spacing(
        source_text=_python_normalize_pydantic_imports(source_text=updated),
    )


def _python_ensure_import(
    *,
    source_text: str,
    group_header: str,
    import_line: str,
    before_group_header: str | None = None,
    after_import_prefix: str | None = None,
) -> str:
    if import_line in source_text:
        return source_text
    if after_import_prefix is not None and after_import_prefix in source_text:
        return source_text.replace(
            after_import_prefix,
            f"{after_import_prefix}\n{import_line}",
            1,
        )
    if group_header in source_text:
        return source_text.replace(group_header, f"{group_header}\n{import_line}", 1)
    if before_group_header is not None and before_group_header in source_text:
        return source_text.replace(
            before_group_header,
            f"{group_header}\n{import_line}\n\n{before_group_header}",
            1,
        )
    byte_start = _python_markerless_import_insert_offset(
        source_text=source_text,
        prefer_import_block_end=group_header not in {"# Standard", "# Third-party"},
    )
    source_bytes = source_text.encode("utf-8")
    return (
        source_bytes[:byte_start]
        + f"{group_header}\n{import_line}\n\n".encode("utf-8")
        + source_bytes[byte_start:]
    ).decode("utf-8")


def _python_markerless_import_insert_offset(
    *,
    source_text: str,
    prefer_import_block_end: bool = False,
) -> int:
    if prefer_import_block_end and any(
        marker in source_text
        for marker in ("# Standard\n", "# Third-party\n", "# Orm\n")
    ):
        class_index = source_text.find("\n\nclass ")
        if class_index >= 0:
            return len(source_text[: class_index + 2].encode("utf-8"))
    future_import = "from __future__ import annotations\n"
    future_index = source_text.find(future_import)
    if future_index >= 0:
        insert_index = future_index + len(future_import)
        if source_text[insert_index : insert_index + 1] == "\n":
            insert_index += 1
        return len(source_text[:insert_index].encode("utf-8"))
    import_index = source_text.find("import ")
    from_index = source_text.find("from ")
    candidates = tuple(index for index in (import_index, from_index) if index >= 0)
    if not candidates:
        return 0
    return len(source_text[: min(candidates)].encode("utf-8"))


def _python_imported_symbol_name(*, import_line: str) -> str | None:
    if " import " not in import_line:
        return None
    imported = import_line.rsplit(" import ", maxsplit=1)[-1].strip()
    if "," in imported or imported.startswith("("):
        return None
    return imported or None


def _python_function_descriptor_import_lines(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
) -> tuple[str, ...]:
    signature = _function_signature(payload=operation.current)
    owner_fqn = _owner_key(operation=operation)
    import_lines: list[str] = []
    for value_signature in (
        *tuple_mappings(signature.get("inputs")),
        *tuple_mappings(signature.get("outputs")),
    ):
        import_lines.extend(
            _python_descriptor_import_lines(
                descriptor=mapping_value(value_signature.get("type_descriptor")),
                context=context,
                owner_fqn=owner_fqn,
            )
        )
    return tuple(dict.fromkeys(import_lines))


def _python_descriptor_import_lines(
    *,
    descriptor: Mapping[str, object],
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    owner_fqn: str | None = None,
) -> tuple[str, ...]:
    descriptor_kind = optional_text(descriptor.get("kind"))
    if descriptor_kind == "primitive":
        primitive = optional_text(descriptor.get("primitive_base_type"))
        if (
            primitive is not None
            and primitive.rsplit(".", maxsplit=1)[-1].lower() == "decimal"
        ):
            return (
                "from decimal import Decimal",
                "from typing import Annotated",
                "from aware_types import DecimalWire",
            )
        if (
            primitive is not None
            and primitive.rsplit(".", maxsplit=1)[-1].lower() == "json"
        ):
            return ("from aware_types import JsonObject",)
        return ()
    if descriptor_kind == "enum":
        enum_fqn = optional_text(descriptor.get("enum_fqn"))
        enum_name = _fqn_leaf(enum_fqn)
        module_name = _python_enum_module_name(
            enum_fqn=enum_fqn,
            sources_root=context.sources_root,
            owner_fqn=owner_fqn,
        )
        if enum_name is None or module_name is None:
            return ()
        return (f"from {module_name} import {enum_name}",)
    if descriptor_kind in {"collection", "union"}:
        return tuple(
            line
            for child in _python_descriptor_children(descriptor=descriptor)
            for line in _python_descriptor_import_lines(
                descriptor=child,
                context=context,
                owner_fqn=owner_fqn,
            )
        )
    return ()


def _python_descriptor_children(
    *,
    descriptor: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    child_descriptors = tuple_mappings(descriptor.get("child_descriptors"))
    if child_descriptors:
        return child_descriptors
    return tuple(
        mapping_value(link.get("child"))
        for link in tuple_mappings(descriptor.get("child_links"))
    )


def _python_enum_module_name(
    *,
    enum_fqn: str | None,
    sources_root: str | None,
    owner_fqn: str | None = None,
) -> str | None:
    if enum_fqn is None or sources_root is None:
        return None
    parts = [part for part in enum_fqn.split(".") if part]
    if len(parts) < 2:
        return None
    enum_name = parts[-1]
    namespace_parts = parts[1:-1]
    enum_module_stem = _python_snake_case(enum_name)
    owner_parts = [part for part in (owner_fqn or "").split(".") if part]
    if len(owner_parts) >= 2 and owner_parts[:-1] == parts[:-1]:
        enum_module_stem = _python_snake_case(owner_parts[-1])
    module_parts = (*namespace_parts, f"{enum_module_stem}_enums")
    return ".".join((sources_root, *module_parts))


def _python_import_group_header(import_line: str) -> str:
    if import_line.startswith("from aware_types "):
        return "# Types"
    if import_line.startswith("from aware_") and "_ontology." in import_line:
        module_root = import_line.split(maxsplit=2)[1].split(".", maxsplit=1)[0]
        label = module_root.removeprefix("aware_").removesuffix("_ontology")
        label_text = label.replace("_", " ").title()
        return f"# {label_text} Ontology"
    return "# Third-party"


def _python_normalize_pydantic_imports(*, source_text: str) -> str:
    if (
        "from pydantic import BaseModel" not in source_text
        or "from pydantic import Field" not in source_text
    ):
        return source_text
    source_text = source_text.replace("from pydantic import BaseModel\n", "")
    source_text = source_text.replace("from pydantic import Field\n", "")
    block = "from pydantic import (\n    BaseModel,\n    Field,\n)\n"
    third_party_marker = "# Third-party\n"
    marker_index = source_text.find(third_party_marker)
    if marker_index >= 0:
        insert_index = marker_index + len(third_party_marker)
        return f"{source_text[:insert_index]}{block}{source_text[insert_index:]}"
    byte_start = _python_markerless_import_insert_offset(source_text=source_text)
    source_bytes = source_text.encode("utf-8")
    return (
        source_bytes[:byte_start]
        + f"# Third-party\n{block}\n".encode("utf-8")
        + source_bytes[byte_start:]
    ).decode("utf-8")


def _python_normalize_import_spacing(*, source_text: str) -> str:
    while "\n\n\n#" in source_text:
        source_text = source_text.replace("\n\n\n#", "\n\n#")
    for import_line in ("from aware_types import JsonObject",):
        source_text = source_text.replace(
            f"{import_line}\n\nclass ",
            f"{import_line}\n\n\nclass ",
        )
    return source_text


def _python_top_level_class_span(
    *,
    source_text: str,
    class_name: str,
) -> tuple[int, int] | None:
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return None
    lines = source_text.splitlines(keepends=True)
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        span = _python_ast_node_line_span(source_text=source_text, node=node)
        if span is None:
            return None
        start_line_index = max(node.lineno - 1, 0)
        byte_start = len("".join(lines[:start_line_index]).encode("utf-8"))
        return byte_start, span[1]
    return None


def _python_top_level_class_exists(
    *,
    source_text: str,
    class_name: str,
) -> bool:
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return False
    return any(
        isinstance(node, ast.ClassDef) and node.name == class_name for node in tree.body
    )


def _python_orm_function_create_renderer_operations(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
    before_hash: str,
    after_hash: str,
    updated_text: str,
) -> tuple[CodeGeneratedRendererDeltaOperation, ...]:
    surfaces = (
        ("method", "function_method"),
        ("input_model", "function_input_model"),
        ("output_model", "function_output_model"),
        ("registry", "function_registry"),
    )
    return tuple(
        CodeGeneratedRendererDeltaOperation(
            operation_key=(
                f"aware_meta.python_orm.function.{surface_key}:"
                f"{operation.operation_key}"
            ),
            kind=CodeGeneratedRendererDeltaOperationKind.insert_section,
            target=target,
            anchor=_anchor_ref_for_surface(
                operation=operation,
                context=context,
                surface_role=surface_role,
            ),
            renderer_key=_renderer_key(operation=operation),
            renderer_profile=context.renderer_profile,
            before_hash=before_hash,
            after_hash=after_hash,
            content_text=updated_text,
            replacement_text=updated_text,
            event_refs=[event_key],
            semantic_keys=[operation.semantic_key],
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta."
                        "python_orm_function_create_renderer_operation"
                    ),
                    "operation_key": operation.operation_key,
                    "surface_key": surface_key,
                    "surface_role": surface_role,
                }
            ),
        )
        for surface_key, surface_role in surfaces
    )


def _anchor_ref_for_surface(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    surface_role: str,
) -> CodeGeneratedRendererAnchorRef:
    base = _anchor_ref(operation=operation, context=context)
    return base.model_copy(
        update={
            "anchor_key": f"{base.anchor_key}.{surface_role}",
            "anchor_role": surface_role,
            "segment_name": surface_role,
        }
    )


def _python_orm_function_io_model_names(
    *,
    owner_name: str,
    function_name: str,
) -> tuple[str, str]:
    input_name = _python_orm_function_input_model_name(
        owner_name=owner_name,
        function_name=function_name,
    )
    return input_name, input_name[: -len("Input")] + "Output"


def _python_orm_function_delete_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmFunctionSectionDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "function"
        or operation.operation_family != "delete"
        or target.relative_path is None
    ):
        return None
    function_name = _function_name(operation=operation)
    owner_name = _owner_name(operation=operation)
    source_state = _python_orm_generated_source_state(
        context=context,
        target=target,
    )
    if function_name is None or owner_name is None or source_state is None:
        return None
    relative_path = source_state.relative_path
    source_text = source_state.source_text
    span = _python_function_delete_span(
        source_text=source_text,
        owner_name=owner_name,
        function_name=function_name,
    )
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
        provider_key=META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        subject_kind="function_config",
        subject_type="FunctionConfig",
        semantic_key=_function_semantic_key(operation=operation),
        object_key=_owner_key(operation=operation),
        field_name="function",
        field_path=f"{owner_name}.{function_name}",
        class_fqn=_owner_key(operation=operation),
        class_name=owner_name,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_function_delete_graph_selector"
                ),
                "operation_key": operation.operation_key,
                "function_name": function_name,
                "owner_name": owner_name,
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
            package_root=source_state.package_root,
            sources_root=context.sources_root,
            source_key=relative_path,
            relative_path=relative_path,
            language=_code_language(context.target_language),
            before_source_hash=source_hash,
            replacements=[
                meta_generated_materialization_text_span_replacement(
                    context=span_context,
                    replacement_key=(
                        "aware_meta.python_orm.function.delete:"
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
                                "python_orm_function_delete_replacement"
                            ),
                            "operation_key": operation.operation_key,
                            "function_name": function_name,
                            "owner_name": owner_name,
                            "renderer_key": _renderer_key(operation=operation),
                        }
                    ),
                )
            ],
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta."
                        "python_orm_function_delete_grammar_anchor_render_delta"
                    ),
                    "operation_key": operation.operation_key,
                    "target_kind": CodeGrammarAnchorRenderTargetKind.text_span.value,
                    "renderer_key": _renderer_key(operation=operation),
                    "renderer_profile": context.renderer_profile,
                }
            ),
        )
    )
    return _PythonOrmFunctionSectionDeltaEvidence(
        section_delta=None,
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        renderer_operation_kind=CodeGeneratedRendererDeltaOperationKind.delete_section,
        content_text=replacement_text,
        mode_reason="python_orm_function_delete_grammar_anchor_render_delta_ready",
        before_hash=before_hash,
        after_hash=after_hash,
    )


def _python_orm_function_update_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmFunctionSectionDeltaEvidence | None:
    signature_evidence = _python_orm_function_signature_render_delta_evidence(
        operation=operation,
        context=context,
        target=target,
        event_key=event_key,
    )
    if signature_evidence is not None:
        return signature_evidence
    if (
        operation.ontology_subject_kind != "function"
        or operation.operation_family != "update"
        or target.relative_path is None
        or not _function_description_changed(operation=operation)
    ):
        return None
    function_name = _function_name(operation=operation)
    owner_name = _owner_name(operation=operation)
    baseline_body_text = _python_orm_function_body_text_from_signature(
        operation=operation,
        payload=operation.baseline,
    )
    body_text = _python_orm_function_body_text_from_signature(
        operation=operation,
        payload=operation.current,
    )
    if (
        function_name is None
        or owner_name is None
        or baseline_body_text is None
        or body_text is None
    ):
        return None
    function_semantic_key = _function_semantic_key(operation=operation)
    source_state = _python_orm_generated_source_state(
        context=context,
        target=target,
    )
    if source_state is not None and target.target_key is not None:
        span = _python_function_body_span(
            source_text=source_state.source_text,
            owner_name=owner_name,
            function_name=function_name,
            expected_body_text=baseline_body_text,
        )
        if span is not None:
            byte_start, byte_end, before_text = span
            replacement_body_text = _python_function_body_replacement_text(
                before_text=before_text,
                expected_body_text=baseline_body_text,
                replacement_body_text=body_text,
            )
            replacement_text = _python_replacement_with_preserved_line_suffix(
                before_text=before_text,
                replacement_text=replacement_body_text,
            )
            before_hash = _sha256_digest(before_text)
            after_hash = _sha256_digest(replacement_text)
            source_hash = _sha256_digest(source_state.source_text)
            function_impl_semantic_key = optional_text(
                operation.current.get("function_impl_semantic_key")
            )
            graph_selector = CodeGraphFieldSelector(
                provider_key=(
                    META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY
                ),
                semantic_owner=(
                    META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
                ),
                subject_kind="function_impl",
                subject_type="FunctionImpl",
                semantic_key=function_impl_semantic_key or operation.semantic_key,
                object_key=_owner_key(operation=operation),
                field_name="body",
                field_path=f"{owner_name}.{function_name}.body",
                class_fqn=_owner_key(operation=operation),
                class_name=owner_name,
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.provider_delta.python_orm_"
                            "function_invocation_body_graph_selector"
                        ),
                        "operation_key": operation.operation_key,
                        "function_name": function_name,
                        "function_semantic_key": function_semantic_key,
                        "invocation_position": _invocation_position(
                            operation=operation,
                        ),
                    }
                ),
            )
            span_context = MetaGeneratedMaterializationTextSpanContext(
                target_key=target.target_key,
                source_key=source_state.relative_path,
                relative_path=source_state.relative_path,
                language=_code_language(context.target_language),
                before_source_hash=source_hash,
                event_ref=event_key,
                semantic_key=operation.semantic_key,
            )
            grammar_anchor_render_delta = (
                meta_generated_materialization_correlated_text_span_render_delta(
                    package_name=context.package_name,
                    package_root=source_state.package_root,
                    sources_root=context.sources_root,
                    source_key=source_state.relative_path,
                    relative_path=source_state.relative_path,
                    language=_code_language(context.target_language),
                    before_source_hash=source_hash,
                    replacements=[
                        meta_generated_materialization_text_span_replacement(
                            context=span_context,
                            replacement_key=(
                                "aware_meta.python_orm.function_invocation.body:"
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
                                        "python_orm_function_invocation_body_"
                                        "replacement"
                                    ),
                                    "operation_key": operation.operation_key,
                                    "function_name": function_name,
                                    "owner_name": owner_name,
                                    "renderer_key": _renderer_key(
                                        operation=operation,
                                    ),
                                }
                            ),
                        )
                    ],
                    metadata=_json_object(
                        {
                            "source": (
                                "aware_meta.provider_delta."
                                "python_orm_function_invocation_body_"
                                "grammar_anchor_render_delta"
                            ),
                            "operation_key": operation.operation_key,
                            "target_kind": (
                                CodeGrammarAnchorRenderTargetKind.text_span.value
                            ),
                            "renderer_key": _renderer_key(operation=operation),
                            "renderer_profile": context.renderer_profile,
                        }
                    ),
                )
            )
            return _PythonOrmFunctionSectionDeltaEvidence(
                section_delta=None,
                grammar_anchor_render_delta=grammar_anchor_render_delta,
                renderer_operation_kind=(
                    CodeGeneratedRendererDeltaOperationKind.replace_anchor
                ),
                content_text=replacement_text,
                mode_reason=(
                    "python_orm_function_invocation_body_"
                    "grammar_anchor_render_delta_ready"
                ),
                before_hash=before_hash,
                after_hash=after_hash,
            )
    relative_path = _section_delta_relative_path(
        relative_path=target.relative_path,
        sources_root=context.sources_root,
    )
    function_qualname = ".".join(part for part in (owner_name, function_name) if part)
    before_hash = _sha256_digest(baseline_body_text)
    after_hash = _sha256_digest(body_text)
    section_delta = CodeSectionDeltaSet(
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
                    section_type="function",
                    qualname=function_qualname or None,
                    semantic_key=function_semantic_key,
                    source_refs=list(_sorted_unique(operation.source_refs)),
                    metadata=_json_object(
                        {
                            "source": (
                                "aware_meta.provider_delta."
                                "python_orm_function_update_section_ref"
                            ),
                            "operation_key": operation.operation_key,
                            "target_relative_path": target.relative_path,
                        }
                    ),
                ),
                segment_ref=CodeSegmentRef(
                    segment_name="body",
                    before_segment_hash=before_hash,
                    metadata=_json_object(
                        {
                            "source": (
                                "aware_meta.provider_delta."
                                "python_orm_function_update_body_segment"
                            ),
                            "operation_key": operation.operation_key,
                            "renderer_key": _renderer_key(operation=operation),
                        }
                    ),
                ),
                content_text=body_text,
                after_hash=after_hash,
                event_ref=event_key,
                semantic_key=operation.semantic_key,
                provider_key=(
                    META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY
                ),
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.provider_delta."
                            "python_orm_function_update_section_delta"
                        ),
                        "operation_key": operation.operation_key,
                        "renderer_key": _renderer_key(operation=operation),
                        "renderer_profile": context.renderer_profile,
                    }
                ),
            )
        ],
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_function_update_section_delta_set"
                ),
                "operation_key": operation.operation_key,
                "renderer_key": _renderer_key(operation=operation),
                "renderer_profile": context.renderer_profile,
            }
        ),
    )
    return _PythonOrmFunctionSectionDeltaEvidence(
        section_delta=section_delta,
        renderer_operation_kind=CodeGeneratedRendererDeltaOperationKind.replace_anchor,
        content_text=body_text,
        mode_reason="python_orm_function_update_body_section_delta_ready",
        before_hash=before_hash,
        after_hash=after_hash,
    )


def _python_orm_function_signature_render_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmFunctionSectionDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "function"
        or operation.operation_family != "update"
        or target.relative_path is None
        or not _function_python_signature_changed(operation=operation)
    ):
        return None
    function_name = _function_name(operation=operation)
    owner_name = _owner_name(operation=operation)
    baseline_signature_text = _python_signature_line(
        operation=operation,
        payload=operation.baseline,
    )
    signature_text = _python_signature_line(
        operation=operation,
        payload=operation.current,
    )
    source_state = _python_orm_generated_source_state(
        context=context,
        target=target,
    )
    if (
        function_name is None
        or owner_name is None
        or baseline_signature_text is None
        or signature_text is None
        or source_state is None
    ):
        return None
    relative_path = source_state.relative_path
    source_text = source_state.source_text
    span = _python_function_signature_span(
        source_text=source_text,
        owner_name=owner_name,
        function_name=function_name,
        expected_signature_text=baseline_signature_text,
    )
    if span is None:
        async_baseline_signature_text = _python_async_signature_line(
            baseline_signature_text
        )
        async_signature_text = _python_async_signature_line(signature_text)
        if (
            async_baseline_signature_text != baseline_signature_text
            and async_signature_text != signature_text
        ):
            async_span = _python_function_signature_span(
                source_text=source_text,
                owner_name=owner_name,
                function_name=function_name,
                expected_signature_text=async_baseline_signature_text,
            )
            if async_span is not None:
                baseline_signature_text = async_baseline_signature_text
                signature_text = async_signature_text
                span = async_span
    if span is None:
        return None
    byte_start, byte_end, before_text = span
    before_hash = _sha256_digest(before_text)
    after_hash = _sha256_digest(signature_text)
    source_hash = _sha256_digest(source_text)
    source_key = relative_path
    target_key = target.target_key
    if target_key is None:
        return None
    graph_selector = CodeGraphFieldSelector(
        provider_key=META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        subject_kind="function_config",
        subject_type="FunctionConfig",
        semantic_key=_function_semantic_key(operation=operation),
        object_key=_owner_key(operation=operation),
        field_name="signature",
        field_path=f"{owner_name}.{function_name}.signature",
        class_fqn=_owner_key(operation=operation),
        class_name=owner_name,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_function_signature_graph_selector"
                ),
                "operation_key": operation.operation_key,
                "function_name": function_name,
                "owner_name": owner_name,
            }
        ),
    )
    span_context = MetaGeneratedMaterializationTextSpanContext(
        target_key=target_key,
        source_key=source_key,
        relative_path=relative_path,
        language=_code_language(context.target_language),
        before_source_hash=source_hash,
        event_ref=event_key,
        semantic_key=operation.semantic_key,
    )
    coherence_replacements = _python_orm_function_signature_coherence_replacements(
        operation=operation,
        source_text=source_text,
        owner_name=owner_name,
        function_name=function_name,
        span_context=span_context,
    )
    if coherence_replacements is None:
        return None
    replacements = [
        meta_generated_materialization_text_span_replacement(
            context=span_context,
            replacement_key=(
                "aware_meta.python_orm.function.signature:" f"{operation.operation_key}"
            ),
            byte_start=byte_start,
            byte_end=byte_end,
            before_text=before_text,
            replacement_text=signature_text,
            graph_selector=graph_selector,
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta."
                        "python_orm_function_signature_replacement"
                    ),
                    "operation_key": operation.operation_key,
                    "renderer_key": _renderer_key(operation=operation),
                    "function_name": function_name,
                    "owner_name": owner_name,
                }
            ),
        ),
        *coherence_replacements,
    ]
    grammar_anchor_render_delta = (
        meta_generated_materialization_correlated_text_span_render_delta(
            package_name=context.package_name,
            package_root=source_state.package_root,
            sources_root=context.sources_root,
            source_key=source_key,
            relative_path=relative_path,
            language=_code_language(context.target_language),
            before_source_hash=source_hash,
            source_text=source_text,
            replacements=replacements,
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta."
                        "python_orm_function_signature_grammar_anchor_render_delta"
                    ),
                    "operation_key": operation.operation_key,
                    "target_kind": CodeGrammarAnchorRenderTargetKind.text_span.value,
                    "renderer_key": _renderer_key(operation=operation),
                    "renderer_profile": context.renderer_profile,
                }
            ),
        )
    )
    return _PythonOrmFunctionSectionDeltaEvidence(
        section_delta=None,
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        renderer_operation_kind=CodeGeneratedRendererDeltaOperationKind.replace_anchor,
        content_text=signature_text,
        mode_reason="python_orm_function_update_signature_grammar_anchor_render_delta_ready",
        before_hash=before_hash,
        after_hash=after_hash,
    )


def _python_orm_function_signature_coherence_replacements(
    *,
    operation: MetaProviderDeltaTypedOperation,
    source_text: str,
    owner_name: str,
    function_name: str,
    span_context: MetaGeneratedMaterializationTextSpanContext,
) -> list[CodeGrammarAnchorRenderReplacement] | None:
    if not _function_signature_requires_invocation_surface(operation=operation):
        return []
    replacements: list[CodeGrammarAnchorRenderReplacement] = []
    expected_payload_text = _python_orm_function_payload_line(
        operation=operation,
        payload=operation.baseline,
    )
    expected_input_model_body = _python_orm_function_input_model_body_text(
        operation=operation,
        payload=operation.baseline,
    )
    payload_span = _python_orm_function_payload_line_span(
        source_text=source_text,
        owner_name=owner_name,
        function_name=function_name,
        expected_payload_text=expected_payload_text,
    )
    current_payload_text = _python_orm_function_payload_line(
        operation=operation,
        payload=operation.current,
    )
    input_model_span = _python_orm_function_input_model_body_span(
        source_text=source_text,
        owner_name=owner_name,
        function_name=function_name,
        expected_body_text=expected_input_model_body,
    )
    current_input_model_body = _python_orm_function_input_model_body_text(
        operation=operation,
        payload=operation.current,
    )
    if missing_correlated_text_span_names(
        {
            "payload": payload_span if current_payload_text is not None else None,
            "input_model": (
                input_model_span if current_input_model_body is not None else None
            ),
        }
    ):
        return None
    if payload_span is None or current_payload_text is None:
        return None
    if input_model_span is None or current_input_model_body is None:
        return None
    replacements.append(
        _python_orm_function_signature_coherence_replacement(
            operation=operation,
            span_context=span_context,
            owner_name=owner_name,
            function_name=function_name,
            field_name="payload",
            byte_start=payload_span[0],
            byte_end=payload_span[1],
            before_text=payload_span[2],
            replacement_text=_python_replacement_with_preserved_line_suffix(
                before_text=payload_span[2],
                replacement_text=current_payload_text,
            ),
        )
    )
    replacements.append(
        _python_orm_function_signature_coherence_replacement(
            operation=operation,
            span_context=span_context,
            owner_name=owner_name,
            function_name=function_name,
            field_name="input_model",
            byte_start=input_model_span[0],
            byte_end=input_model_span[1],
            before_text=input_model_span[2],
            replacement_text=_python_replacement_with_preserved_line_suffix(
                before_text=input_model_span[2],
                replacement_text=current_input_model_body,
            ),
        )
    )
    return replacements


def _python_orm_function_missing_correlated_span_names(
    *,
    operation: MetaProviderDeltaTypedOperation,
    source_text: str,
    owner_name: str,
    function_name: str,
) -> tuple[str, ...]:
    if not _function_signature_requires_invocation_surface(operation=operation):
        return ()
    current_payload_text = _python_orm_function_payload_line(
        operation=operation,
        payload=operation.current,
    )
    current_input_model_body = _python_orm_function_input_model_body_text(
        operation=operation,
        payload=operation.current,
    )
    payload_span = _python_orm_function_payload_line_span(
        source_text=source_text,
        owner_name=owner_name,
        function_name=function_name,
        expected_payload_text=_python_orm_function_payload_line(
            operation=operation,
            payload=operation.baseline,
        ),
    )
    input_model_span = _python_orm_function_input_model_body_span(
        source_text=source_text,
        owner_name=owner_name,
        function_name=function_name,
        expected_body_text=_python_orm_function_input_model_body_text(
            operation=operation,
            payload=operation.baseline,
        ),
    )
    return missing_correlated_text_span_names(
        {
            "payload": payload_span if current_payload_text is not None else None,
            "input_model": (
                input_model_span if current_input_model_body is not None else None
            ),
        }
    )


def _python_orm_function_signature_coherence_replacement(
    *,
    operation: MetaProviderDeltaTypedOperation,
    span_context: MetaGeneratedMaterializationTextSpanContext,
    owner_name: str,
    function_name: str,
    field_name: str,
    byte_start: int,
    byte_end: int,
    before_text: str,
    replacement_text: str,
) -> CodeGrammarAnchorRenderReplacement:
    graph_selector = CodeGraphFieldSelector(
        provider_key=META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        subject_kind="function_config",
        subject_type="FunctionConfig",
        semantic_key=_function_semantic_key(operation=operation),
        object_key=_owner_key(operation=operation),
        field_name=field_name,
        field_path=f"{owner_name}.{function_name}.{field_name}",
        class_fqn=_owner_key(operation=operation),
        class_name=owner_name,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_function_signature_coherence_graph_selector"
                ),
                "operation_key": operation.operation_key,
                "function_name": function_name,
                "owner_name": owner_name,
                "field_name": field_name,
            }
        ),
    )
    return meta_generated_materialization_text_span_replacement(
        context=span_context,
        replacement_key=(
            f"aware_meta.python_orm.function.{field_name}:" f"{operation.operation_key}"
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
                    "python_orm_function_signature_coherence_replacement"
                ),
                "operation_key": operation.operation_key,
                "renderer_key": _renderer_key(operation=operation),
                "field_name": field_name,
            }
        ),
    )


def _python_orm_function_invocation_section_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
    event_key: str,
) -> _PythonOrmFunctionSectionDeltaEvidence | None:
    if (
        operation.ontology_subject_kind != "function_invocation"
        or operation.operation_family != "create"
        or target.relative_path is None
    ):
        return None
    function_name = _function_name(operation=operation)
    owner_name = _owner_name(operation=operation)
    baseline_body_text = _python_orm_function_invocation_baseline_body_text(
        operation=operation,
    )
    body_text = _python_orm_function_invocation_body_text(operation=operation)
    if (
        function_name is None
        or owner_name is None
        or baseline_body_text is None
        or body_text is None
    ):
        return None
    function_semantic_key = _function_semantic_key(operation=operation)
    source_state = _python_orm_generated_source_state(
        context=context,
        target=target,
    )
    if source_state is not None and target.target_key is not None:
        span = _python_function_body_span(
            source_text=source_state.source_text,
            owner_name=owner_name,
            function_name=function_name,
            expected_body_text=baseline_body_text,
        )
        if span is not None:
            byte_start, byte_end, before_text = span
            replacement_body_text = _python_function_body_replacement_text(
                before_text=before_text,
                expected_body_text=baseline_body_text,
                replacement_body_text=body_text,
            )
            replacement_text = _python_replacement_with_preserved_line_suffix(
                before_text=before_text,
                replacement_text=replacement_body_text,
            )
            before_hash = _sha256_digest(before_text)
            after_hash = _sha256_digest(replacement_text)
            source_hash = _sha256_digest(source_state.source_text)
            function_impl_semantic_key = optional_text(
                operation.current.get("function_impl_semantic_key")
            )
            graph_selector = CodeGraphFieldSelector(
                provider_key=(
                    META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY
                ),
                semantic_owner=(
                    META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
                ),
                subject_kind="function_impl",
                subject_type="FunctionImpl",
                semantic_key=function_impl_semantic_key or operation.semantic_key,
                object_key=_owner_key(operation=operation),
                field_name="body",
                field_path=f"{owner_name}.{function_name}.body",
                class_fqn=_owner_key(operation=operation),
                class_name=owner_name,
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.provider_delta.python_orm_"
                            "function_invocation_body_graph_selector"
                        ),
                        "operation_key": operation.operation_key,
                        "function_name": function_name,
                        "function_semantic_key": function_semantic_key,
                        "invocation_position": _invocation_position(
                            operation=operation,
                        ),
                    }
                ),
            )
            span_context = MetaGeneratedMaterializationTextSpanContext(
                target_key=target.target_key,
                source_key=source_state.relative_path,
                relative_path=source_state.relative_path,
                language=_code_language(context.target_language),
                before_source_hash=source_hash,
                event_ref=event_key,
                semantic_key=operation.semantic_key,
            )
            grammar_anchor_render_delta = (
                meta_generated_materialization_correlated_text_span_render_delta(
                    package_name=context.package_name,
                    package_root=source_state.package_root,
                    sources_root=context.sources_root,
                    source_key=source_state.relative_path,
                    relative_path=source_state.relative_path,
                    language=_code_language(context.target_language),
                    before_source_hash=source_hash,
                    replacements=[
                        meta_generated_materialization_text_span_replacement(
                            context=span_context,
                            replacement_key=(
                                "aware_meta.python_orm.function_invocation.body:"
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
                                        "python_orm_function_invocation_body_"
                                        "replacement"
                                    ),
                                    "operation_key": operation.operation_key,
                                    "function_name": function_name,
                                    "owner_name": owner_name,
                                    "renderer_key": _renderer_key(
                                        operation=operation,
                                    ),
                                }
                            ),
                        )
                    ],
                    metadata=_json_object(
                        {
                            "source": (
                                "aware_meta.provider_delta."
                                "python_orm_function_invocation_body_"
                                "grammar_anchor_render_delta"
                            ),
                            "operation_key": operation.operation_key,
                            "target_kind": (
                                CodeGrammarAnchorRenderTargetKind.text_span.value
                            ),
                            "renderer_key": _renderer_key(operation=operation),
                            "renderer_profile": context.renderer_profile,
                        }
                    ),
                )
            )
            return _PythonOrmFunctionSectionDeltaEvidence(
                section_delta=None,
                grammar_anchor_render_delta=grammar_anchor_render_delta,
                renderer_operation_kind=(
                    CodeGeneratedRendererDeltaOperationKind.replace_anchor
                ),
                content_text=replacement_text,
                mode_reason=(
                    "python_orm_function_invocation_body_"
                    "grammar_anchor_render_delta_ready"
                ),
                before_hash=before_hash,
                after_hash=after_hash,
            )
    relative_path = _section_delta_relative_path(
        relative_path=target.relative_path,
        sources_root=context.sources_root,
    )
    function_qualname = ".".join(part for part in (owner_name, function_name) if part)
    before_hash = _sha256_digest(baseline_body_text)
    after_hash = _sha256_digest(body_text)
    section_delta = CodeSectionDeltaSet(
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
                    section_type="function",
                    qualname=function_qualname or None,
                    semantic_key=function_semantic_key,
                    source_refs=list(_sorted_unique(operation.source_refs)),
                    metadata=_json_object(
                        {
                            "source": (
                                "aware_meta.provider_delta."
                                "python_orm_function_invocation_section_ref"
                            ),
                            "operation_key": operation.operation_key,
                            "target_relative_path": target.relative_path,
                        }
                    ),
                ),
                segment_ref=CodeSegmentRef(
                    segment_name="body",
                    before_segment_hash=before_hash,
                    metadata=_json_object(
                        {
                            "source": (
                                "aware_meta.provider_delta."
                                "python_orm_function_invocation_body_segment"
                            ),
                            "operation_key": operation.operation_key,
                            "renderer_key": _renderer_key(operation=operation),
                        }
                    ),
                ),
                content_text=body_text,
                after_hash=after_hash,
                event_ref=event_key,
                semantic_key=operation.semantic_key,
                provider_key=(
                    META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY
                ),
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.provider_delta."
                            "python_orm_function_invocation_section_delta"
                        ),
                        "operation_key": operation.operation_key,
                        "renderer_key": _renderer_key(operation=operation),
                        "renderer_profile": context.renderer_profile,
                    }
                ),
            )
        ],
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "python_orm_function_invocation_section_delta_set"
                ),
                "operation_key": operation.operation_key,
                "renderer_key": _renderer_key(operation=operation),
                "renderer_profile": context.renderer_profile,
            }
        ),
    )
    return _PythonOrmFunctionSectionDeltaEvidence(
        section_delta=section_delta,
        renderer_operation_kind=CodeGeneratedRendererDeltaOperationKind.replace_anchor,
        content_text=body_text,
        mode_reason="python_orm_function_invocation_body_section_delta_ready",
        before_hash=before_hash,
        after_hash=after_hash,
    )


def _python_function_body_span(
    *,
    source_text: str,
    owner_name: str,
    function_name: str,
    expected_body_text: str | None,
) -> tuple[int, int, str] | None:
    if expected_body_text is None:
        return None
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != owner_name:
            continue
        for child in node.body:
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if child.name != function_name or not child.body:
                continue
            first_child = child.body[0]
            last_child = child.body[-1]
            start_span = _python_ast_node_line_span(
                source_text=source_text,
                node=first_child,
            )
            end_span = _python_ast_node_line_span(
                source_text=source_text,
                node=last_child,
            )
            if start_span is None or end_span is None:
                return None
            byte_start = start_span[0]
            byte_end = end_span[1]
            before_text = source_text.encode("utf-8")[byte_start:byte_end].decode(
                "utf-8"
            )
            if not _python_function_body_text_matches(
                before_text=before_text,
                expected_body_text=expected_body_text,
            ):
                return None
            return byte_start, byte_end, before_text
    return None


def _python_function_body_text_matches(
    *,
    before_text: str,
    expected_body_text: str,
) -> bool:
    body = before_text.rstrip("\n")
    if body == expected_body_text:
        return True
    return body == _python_function_body_text_with_leading_indent(
        body_text=expected_body_text,
        leading_indent=_leading_whitespace(before_text),
    )


def _python_function_body_replacement_text(
    *,
    before_text: str,
    expected_body_text: str,
    replacement_body_text: str,
) -> str:
    leading_indent = _leading_whitespace(before_text)
    if before_text.rstrip("\n") == _python_function_body_text_with_leading_indent(
        body_text=expected_body_text,
        leading_indent=leading_indent,
    ):
        return _python_function_body_text_with_leading_indent(
            body_text=replacement_body_text,
            leading_indent=leading_indent,
        )
    return replacement_body_text


def _python_function_body_text_with_leading_indent(
    *,
    body_text: str,
    leading_indent: str,
) -> str:
    if not leading_indent or body_text.startswith(leading_indent):
        return body_text
    return f"{leading_indent}{body_text}"


def _leading_whitespace(value: str) -> str:
    line = value.splitlines()[0] if value.splitlines() else ""
    return line[: len(line) - len(line.lstrip())]


def _python_orm_function_create_content_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    function_name = _function_name(operation=operation)
    if function_name is None:
        return None
    async_prefix = "async " if _function_is_async(operation=operation) else ""
    description = optional_text(
        _function_signature(payload=operation.current).get("description")
    )
    lines = [
        "",
        f"    {async_prefix}def {function_name}(self) -> None:",
    ]
    if description is not None:
        lines.append(f'        """{_python_docstring_line(description)}"""')
    lines.append("        raise NotImplementedError")
    return "\n".join(lines) + "\n"


def _python_orm_function_invocation_baseline_body_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    return _generated_materialization_python_orm_text(
        operation=operation,
        field_names=("baseline_body_text", "before_body_text"),
    )


def _python_orm_function_invocation_body_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    return _generated_materialization_python_orm_text(
        operation=operation,
        field_names=("body_text", "current_body_text", "replacement_body_text"),
    )


def _generated_materialization_python_orm_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
    field_names: tuple[str, ...],
) -> str | None:
    for payload in (
        operation.current,
        operation.semantic_change_projection or {},
        operation.extra,
    ):
        python_orm = orm_runtime_target_payload(payload)
        source_text = _python_orm_text_from_aware_source_payload(
            payload=python_orm,
            field_names=field_names,
        )
        if source_text is not None:
            return source_text
        for field_name in field_names:
            value = python_orm.get(field_name)
            if isinstance(value, str) and value:
                return value
    return None


def _python_orm_text_from_aware_source_payload(
    *,
    payload: Mapping[str, object],
    field_names: tuple[str, ...],
) -> str | None:
    if {"baseline_body_text", "before_body_text"} & set(field_names):
        return _python_orm_baseline_body_text_from_aware_source(payload=payload)
    if {
        "body_text",
        "current_body_text",
        "replacement_body_text",
    } & set(field_names):
        return _python_orm_current_body_text_from_aware_source(payload=payload)
    return None


def _python_orm_baseline_body_text_from_aware_source(
    *,
    payload: Mapping[str, object],
) -> str | None:
    baseline_body_kind = optional_text(payload.get("baseline_body_kind"))
    aware_body_text = _first_text(
        payload.get("baseline_aware_body_text"),
        payload.get("before_aware_body_text"),
    )
    baseline_description = _first_text(
        payload.get("baseline_function_description"),
        payload.get("before_function_description"),
        payload.get("function_description"),
        payload.get("description"),
    )
    if (
        baseline_body_kind != "not_implemented"
        and aware_body_text is None
        and baseline_description is None
    ):
        return None
    description = _first_text(
        _aware_body_docstring_text(aware_body_text),
        baseline_description,
    )
    if description is None:
        return "raise NotImplementedError"
    return f'"""{_python_docstring_line(description)}"""\n        raise NotImplementedError'


def _python_orm_current_body_text_from_aware_source(
    *,
    payload: Mapping[str, object],
) -> str | None:
    aware_body_text = _first_text(
        payload.get("aware_body_text"),
        payload.get("current_aware_body_text"),
        payload.get("replacement_aware_body_text"),
    )
    if aware_body_text is None or parse_function_statements_from_block is None:
        return None
    try:
        statements = parse_function_statements_from_block(aware_body_text)
    except FunctionParseError:
        return None
    lines: list[str] = []
    for statement in statements:
        if getattr(statement, "kind", None) != "set":
            continue
        target_name = optional_text(getattr(statement, "name", None))
        value = getattr(statement, "value", None)
        value_kind = optional_text(getattr(value, "kind", None))
        source_name = optional_text(getattr(value, "text", None))
        if target_name is None or value_kind != "reference" or source_name is None:
            continue
        lines.append(f"self.{target_name} = {source_name}")
    if not lines:
        return None
    lines.append("return self")
    return "\n        ".join(lines)


def _aware_body_docstring_text(value: str | None) -> str | None:
    if value is None or '"""' not in value:
        return None
    _, remainder = value.split('"""', maxsplit=1)
    if '"""' not in remainder:
        return None
    raw_docstring, _ = remainder.split('"""', maxsplit=1)
    return " ".join(line.strip() for line in raw_docstring.splitlines()).strip() or None


def _first_text(*values: object) -> str | None:
    for value in values:
        text = optional_text(value)
        if text is not None:
            return text
    return None


def _python_orm_function_guarded_delta_diagnostics(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
) -> tuple[str, ...]:
    diagnostics = [META_PYTHON_ORM_FUNCTION_EVIDENCE_ONLY_DIAGNOSTIC]
    if target.relative_path is None:
        diagnostics.append(
            META_PYTHON_ORM_FUNCTION_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC
        )
    if (
        operation.ontology_subject_kind == "function_invocation"
        and operation.operation_family == "create"
    ):
        if (
            _python_orm_function_invocation_baseline_body_text(
                operation=operation,
            )
            is None
        ):
            diagnostics.append(
                META_PYTHON_ORM_FUNCTION_INVOCATION_BASELINE_BODY_MISSING_DIAGNOSTIC
            )
        if _python_orm_function_invocation_body_text(operation=operation) is None:
            diagnostics.append(
                META_PYTHON_ORM_FUNCTION_INVOCATION_BODY_MISSING_DIAGNOSTIC
            )
    if (
        operation.ontology_subject_kind == "function"
        and operation.operation_family == "update"
    ):
        if not _function_description_changed(operation=operation):
            if _function_python_signature_changed(operation=operation):
                diagnostics.extend(
                    _python_orm_function_signature_delta_diagnostics(
                        operation=operation,
                        context=context,
                        target=target,
                    )
                )
            else:
                diagnostics.append(
                    META_PYTHON_ORM_FUNCTION_UPDATE_UNSUPPORTED_DIAGNOSTIC
                )
        elif (
            _python_orm_function_body_text_from_signature(
                operation=operation,
                payload=operation.baseline,
            )
            is None
            or _python_orm_function_body_text_from_signature(
                operation=operation,
                payload=operation.current,
            )
            is None
        ):
            diagnostics.append(META_PYTHON_ORM_FUNCTION_UPDATE_BODY_MISSING_DIAGNOSTIC)
    if (
        operation.ontology_subject_kind == "function"
        and operation.operation_family == "delete"
    ):
        diagnostics.append(META_PYTHON_ORM_FUNCTION_DELETE_SPAN_MISSING_DIAGNOSTIC)
    if len(diagnostics) == 1:
        diagnostics.append(META_PYTHON_ORM_FUNCTION_GUARDED_DELTA_MISSING_DIAGNOSTIC)
    return tuple(dict.fromkeys(diagnostics))


def _python_orm_function_signature_delta_diagnostics(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
) -> tuple[str, ...]:
    baseline_signature_text = _python_signature_line(
        operation=operation,
        payload=operation.baseline,
    )
    signature_text = _python_signature_line(
        operation=operation,
        payload=operation.current,
    )
    if baseline_signature_text is None or signature_text is None:
        return (META_PYTHON_ORM_FUNCTION_SIGNATURE_TEXT_MISSING_DIAGNOSTIC,)
    function_name = _function_name(operation=operation)
    owner_name = _owner_name(operation=operation)
    source_state = _python_orm_generated_source_state(
        context=context,
        target=target,
    )
    if function_name is None or owner_name is None or source_state is None:
        return (META_PYTHON_ORM_FUNCTION_SIGNATURE_SPAN_MISSING_DIAGNOSTIC,)
    span = _python_function_signature_span(
        source_text=source_state.source_text,
        owner_name=owner_name,
        function_name=function_name,
        expected_signature_text=baseline_signature_text,
    )
    if span is None:
        async_baseline_signature_text = _python_async_signature_line(
            baseline_signature_text
        )
        if async_baseline_signature_text != baseline_signature_text:
            span = _python_function_signature_span(
                source_text=source_state.source_text,
                owner_name=owner_name,
                function_name=function_name,
                expected_signature_text=async_baseline_signature_text,
            )
    if span is None:
        return (META_PYTHON_ORM_FUNCTION_SIGNATURE_SPAN_MISSING_DIAGNOSTIC,)
    missing = _python_orm_function_missing_correlated_span_names(
        operation=operation,
        source_text=source_state.source_text,
        owner_name=owner_name,
        function_name=function_name,
    )
    diagnostics: list[str] = []
    if "payload" in missing:
        diagnostics.append(
            META_PYTHON_ORM_FUNCTION_SIGNATURE_PAYLOAD_SPAN_MISSING_DIAGNOSTIC
        )
    if "input_model" in missing:
        diagnostics.append(
            META_PYTHON_ORM_FUNCTION_SIGNATURE_INPUT_MODEL_SPAN_MISSING_DIAGNOSTIC
        )
    if diagnostics:
        return tuple(diagnostics)
    return (META_PYTHON_ORM_FUNCTION_SIGNATURE_SPAN_MISSING_DIAGNOSTIC,)


def _python_docstring_line(value: str) -> str:
    return " ".join(value.replace('"""', '\\"\\"\\"').split())


def _python_docstring_lines(value: str, *, indent: str) -> list[str]:
    if "\n" not in value:
        return [f'{indent}"""{_python_docstring_line(value)}"""']
    lines = [f'{indent}"""']
    lines.extend(f"{indent}{line}" if line else "" for line in value.splitlines())
    lines.append(f'{indent}"""')
    return lines


def _requires_generated_materialization_policy(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    if operation.ontology_subject_kind == "function":
        return operation.operation_family in {"create", "update", "delete"}
    if operation.ontology_subject_kind == "function_invocation":
        return operation.operation_family == "create"
    return False


def _function_description_changed(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    current_description = _description_value(
        payload=_function_signature(payload=operation.current)
    )
    baseline_description = _description_value(
        payload=_function_signature(payload=operation.baseline)
    )
    if current_description is _MISSING:
        return False
    return current_description != baseline_description


def _python_orm_function_body_text_from_signature(
    *,
    operation: MetaProviderDeltaTypedOperation,
    payload: Mapping[str, object],
) -> str | None:
    signature = _function_signature(payload=payload)
    if not signature and payload is operation.baseline:
        signature = _function_signature(payload=operation.current)
    if not signature:
        return None
    lines: list[str] = []
    description = _description_value(payload=signature)
    if description is not _MISSING and description is not None:
        description_text = optional_text(description)
        if description_text is not None:
            lines.append(f'"""{_python_docstring_line(description_text)}"""')
    lines.append("        raise NotImplementedError")
    return "\n".join(lines)


def _function_python_signature_changed(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    if (
        operation.ontology_subject_kind != "function"
        or operation.operation_family != "update"
    ):
        return False
    current_signature = _python_signature_line(
        operation=operation,
        payload=operation.current,
    )
    if current_signature is None:
        return False
    baseline_signature = _python_signature_line(
        operation=operation,
        payload=operation.baseline,
    )
    return current_signature != baseline_signature


def _python_signature_line(
    *,
    operation: MetaProviderDeltaTypedOperation,
    payload: Mapping[str, object],
) -> str | None:
    signature = _function_signature(payload=payload)
    if not signature and payload is operation.baseline:
        signature = _function_signature(payload=operation.current)
    function_name = optional_text(signature.get("name")) or _function_name(
        operation=operation
    )
    if function_name is None:
        return None
    input_texts: list[str] = []
    for input_signature in sorted(
        tuple_mappings(signature.get("inputs")),
        key=_function_attribute_sort_key,
    ):
        input_text = _python_function_input_text(input_signature, model_field=False)
        if input_text is None:
            return None
        input_texts.append(input_text)
    return_text = _python_function_return_text(tuple_mappings(signature.get("outputs")))
    if return_text is None:
        return_text = "None"
    async_prefix = "async " if signature.get("is_async") is True else ""
    parameters = ", ".join(("self", *input_texts))
    return f"{async_prefix}def {function_name}({parameters}) -> {return_text}:"


def _python_async_signature_line(signature_text: str) -> str:
    if signature_text.startswith("async def "):
        return signature_text
    if signature_text.startswith("def "):
        return f"async {signature_text}"
    return signature_text


def _python_orm_function_payload_line(
    *,
    operation: MetaProviderDeltaTypedOperation,
    payload: Mapping[str, object],
) -> str | None:
    input_names = tuple(
        name
        for input_signature in _function_signature_inputs(
            operation=operation,
            payload=payload,
        )
        if (name := optional_text(input_signature.get("name"))) is not None
    )
    if not input_names:
        return "        payload = {}"
    payload_items = ", ".join(f'"{name}": {name}' for name in input_names)
    return f"        payload = {{{payload_items}}}"


def _python_orm_function_input_model_body_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
    payload: Mapping[str, object],
) -> str | None:
    lines: list[str] = []
    for input_signature in _function_signature_inputs(
        operation=operation,
        payload=payload,
    ):
        input_text = _python_function_input_text(input_signature, model_field=True)
        if input_text is None:
            return None
        lines.append(f"    {input_text}")
    if not lines:
        return "    pass"
    return "\n".join(lines)


def _function_signature_inputs(
    *,
    operation: MetaProviderDeltaTypedOperation,
    payload: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    signature = _function_signature(payload=payload)
    if not signature and payload is operation.baseline:
        signature = _function_signature(payload=operation.current)
    return tuple(
        sorted(
            tuple_mappings(signature.get("inputs")),
            key=_function_attribute_sort_key,
        )
    )


def _function_signature_requires_invocation_surface(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    return bool(
        _function_signature_inputs(
            operation=operation,
            payload=operation.baseline,
        )
        or _function_signature_inputs(
            operation=operation,
            payload=operation.current,
        )
    )


def _python_function_input_text(
    signature: Mapping[str, object],
    *,
    model_field: bool,
) -> str | None:
    name = optional_text(signature.get("name"))
    type_text = _python_type_text_from_signature(signature)
    if name is None or type_text is None:
        return None
    default_text = _python_function_default_text(
        signature=signature,
        type_text=type_text,
        model_field=model_field,
    )
    if default_text is not None:
        return f"{name}: {type_text} = {default_text}"
    return f"{name}: {type_text}"


def _python_function_default_text(
    *,
    signature: Mapping[str, object],
    type_text: str,
    model_field: bool,
) -> str | None:
    descriptor = mapping_value(signature.get("type_descriptor"))
    is_collection = optional_text(descriptor.get("kind")) == "collection"
    raw_default = signature.get("default_value")
    if is_collection:
        if model_field:
            return "Field(default_factory=list)"
        if raw_default is None:
            return None
    if raw_default is not None:
        rendered_default = _python_signature_default_literal(
            raw_default,
            descriptor=descriptor,
            type_text=type_text,
        )
        if rendered_default is None:
            return None
        if model_field:
            return f"Field(default={rendered_default})"
        return rendered_default
    if signature.get("is_required") is False:
        return "Field(default=None)" if model_field else "None"
    return None


def _python_signature_default_literal(
    value: object,
    *,
    descriptor: Mapping[str, object],
    type_text: str,
) -> str | None:
    parsed_value = _python_parse_default_value(value)
    if parsed_value is None:
        return "None"
    if optional_text(descriptor.get("kind")) == "enum" and isinstance(
        parsed_value, str
    ):
        return f"{type_text}.{_python_enum_option_name(parsed_value)}"
    if _descriptor_is_decimal(descriptor):
        return f"Decimal({canonical_decimal_text(parsed_value)!r})"
    if _descriptor_is_decimal_collection(descriptor) and isinstance(parsed_value, list):
        return (
            "["
            + ", ".join(
                f"Decimal({canonical_decimal_text(item)!r})" for item in parsed_value
            )
            + "]"
        )
    if isinstance(parsed_value, bool):
        return "True" if parsed_value else "False"
    if isinstance(parsed_value, int | float | str | list | dict):
        return repr(parsed_value)
    return None


def _descriptor_is_decimal(descriptor: Mapping[str, object]) -> bool:
    primitive = optional_text(descriptor.get("primitive_base_type"))
    return (
        optional_text(descriptor.get("kind")) == "primitive"
        and primitive is not None
        and primitive.rsplit(".", maxsplit=1)[-1].lower() == "decimal"
    )


def _descriptor_is_decimal_collection(descriptor: Mapping[str, object]) -> bool:
    if optional_text(descriptor.get("kind")) != "collection":
        return False
    return any(
        _descriptor_is_decimal(child)
        for child in _python_descriptor_children(descriptor=descriptor)
    )


def _python_parse_default_value(value: object) -> object | None:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _python_function_return_text(
    outputs: tuple[dict[str, object], ...],
) -> str | None:
    if not outputs:
        return None
    sorted_outputs = tuple(sorted(outputs, key=_function_attribute_sort_key))
    if len(sorted_outputs) == 1:
        return _python_type_text_from_signature(sorted_outputs[0])
    output_texts: list[str] = []
    for output_signature in sorted_outputs:
        output_text = _python_type_text_from_signature(output_signature)
        if output_text is None:
            return None
        output_texts.append(output_text)
    return f"tuple[{', '.join(output_texts)}]"


def _python_type_text_from_signature(signature: Mapping[str, object]) -> str | None:
    descriptor = mapping_value(signature.get("type_descriptor"))
    if not descriptor:
        descriptor = mapping_value(signature)
    base_text = _python_type_text_from_descriptor(descriptor)
    if base_text is None:
        return None
    if signature.get("is_required") is False:
        return f"{base_text} | None"
    return base_text


def _signature_is_optional(signature: Mapping[str, object]) -> bool:
    return signature.get("is_required") is False


def _signature_type_descriptor_kind(signature: Mapping[str, object]) -> str | None:
    descriptor = mapping_value(signature.get("type_descriptor"))
    if not descriptor:
        descriptor = mapping_value(signature)
    return optional_text(descriptor.get("kind"))


def _python_type_text_from_descriptor(
    descriptor: Mapping[str, object],
) -> str | None:
    descriptor_kind = optional_text(descriptor.get("kind"))
    if descriptor_kind == "primitive":
        return _python_primitive_type_text(descriptor.get("primitive_base_type"))
    if descriptor_kind == "class":
        return _fqn_leaf(descriptor.get("class_fqn"))
    if descriptor_kind == "enum":
        return _fqn_leaf(descriptor.get("enum_fqn"))
    if descriptor_kind == "collection":
        child_text = _python_first_child_type_text(descriptor=descriptor)
        if child_text is None:
            return None
        return f"list[{child_text}]"
    if descriptor_kind == "union":
        child_text = _python_single_non_null_child_type_text(descriptor=descriptor)
        if child_text is None:
            return None
        return f"{child_text} | None"
    return None


def _python_primitive_type_text(value: object) -> str | None:
    raw_value = optional_text(value)
    if raw_value is None:
        return None
    key = raw_value.rsplit(".", maxsplit=1)[-1].lower()
    return _PYTHON_PRIMITIVE_TYPE_TEXT.get(key)


def _fqn_leaf(value: object) -> str | None:
    text = optional_text(value)
    if text is None:
        return None
    return text.rsplit(".", maxsplit=1)[-1]


def _python_first_child_type_text(
    *,
    descriptor: Mapping[str, object],
) -> str | None:
    child_descriptors = tuple_mappings(descriptor.get("child_descriptors"))
    if child_descriptors:
        return _python_type_text_from_descriptor(child_descriptors[0])
    child_links = tuple_mappings(descriptor.get("child_links"))
    if not child_links:
        element_primitive = descriptor.get("element_primitive_base_type")
        if element_primitive is not None:
            return _python_primitive_type_text(element_primitive)
        return None
    child = mapping_value(child_links[0].get("child"))
    return _python_type_text_from_descriptor(child)


def _python_single_non_null_child_type_text(
    *,
    descriptor: Mapping[str, object],
) -> str | None:
    child_links = tuple_mappings(descriptor.get("child_links"))
    child_descriptors = tuple_mappings(descriptor.get("child_descriptors"))
    children = child_descriptors or tuple(
        mapping_value(link.get("child")) for link in child_links
    )
    child_texts = tuple(
        text
        for child in children
        if optional_text(child.get("primitive_base_type")) != "null"
        for text in (_python_type_text_from_descriptor(child),)
        if text is not None
    )
    if len(child_texts) != 1:
        return None
    return child_texts[0]


def _function_attribute_sort_key(
    signature: Mapping[str, object],
) -> tuple[int, str]:
    position = signature.get("position")
    resolved_position = position if isinstance(position, int) else 0
    return (resolved_position, optional_text(signature.get("name")) or "")


def _python_enum_option_name(value: str) -> str:
    return _python_snake_case(value)


def _python_snake_case(value: str) -> str:
    chars: list[str] = []
    previous_lower = False
    for char in value:
        if char.isalnum():
            if char.isupper() and previous_lower:
                chars.append("_")
            chars.append(char.lower())
            previous_lower = char.islower() or char.isdigit()
        else:
            if chars and chars[-1] != "_":
                chars.append("_")
            previous_lower = False
    text = "".join(chars).strip("_")
    if not text:
        return "_"
    if text[0].isdigit():
        return f"_{text}"
    return text


def _python_orm_generated_source_state(
    *,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
    target: CodeGeneratedMaterializationTargetRef,
) -> _PythonOrmGeneratedSourceState | None:
    relative_path = _section_delta_relative_path(
        relative_path=target.relative_path,
        sources_root=context.sources_root,
    )
    if relative_path is None or context.package_root is None:
        return None
    if not _safe_relative_path(relative_path):
        return None
    base_path = Path(context.package_root)
    source_root = _normalized_relative_path(context.sources_root)
    source_path_candidates = _python_orm_generated_source_path_candidates(
        base_path=base_path,
        source_root=source_root,
        relative_path=relative_path,
        context=context,
    )
    source_path = next(
        (candidate for candidate in source_path_candidates if candidate.is_file()),
        None,
    )
    if source_path is None:
        return None
    try:
        artifact_root = _python_orm_generated_source_artifact_root(
            source_path=source_path,
            source_root=source_root,
            relative_path=relative_path,
        )
        return _PythonOrmGeneratedSourceState(
            package_root=artifact_root.as_posix(),
            relative_path=relative_path,
            source_text=source_path.read_text(encoding="utf-8"),
        )
    except (OSError, UnicodeDecodeError):
        return None


def _python_orm_generated_source_artifact_root(
    *,
    source_path: Path,
    source_root: str | None,
    relative_path: str,
) -> Path:
    suffix = Path(relative_path)
    if source_root is not None:
        suffix = Path(source_root) / suffix
    return source_path.parents[len(suffix.parts) - 1]


def _python_orm_generated_source_path_candidates(
    *,
    base_path: Path,
    source_root: str | None,
    relative_path: str,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
) -> tuple[Path, ...]:
    direct_path = (
        base_path / source_root / relative_path
        if source_root is not None
        else base_path / relative_path
    )
    candidates = [direct_path]
    renderer_profile = _normalized_relative_path(context.renderer_profile)
    if (
        renderer_profile == META_PYTHON_ORM_FUNCTION_RENDERER_PROFILE
        and base_path.name != renderer_profile
    ):
        renderer_base = base_path / renderer_profile
        candidates.append(
            renderer_base / source_root / relative_path
            if source_root is not None
            else renderer_base / relative_path
        )
    return tuple(dict.fromkeys(candidates))


def _python_function_signature_span(
    *,
    source_text: str,
    owner_name: str,
    function_name: str,
    expected_signature_text: str,
) -> tuple[int, int, str] | None:
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != owner_name:
            continue
        for child in node.body:
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if child.name != function_name:
                continue
            span = _python_function_def_line_span(
                source_text=source_text,
                node=child,
            )
            if span is None:
                return None
            byte_start, byte_end = span
            before_text = source_text.encode("utf-8")[byte_start:byte_end].decode(
                "utf-8",
            )
            if before_text != expected_signature_text:
                return None
            return byte_start, byte_end, before_text
    return None


def _python_orm_function_payload_line_span(
    *,
    source_text: str,
    owner_name: str,
    function_name: str,
    expected_payload_text: str | None,
) -> tuple[int, int, str] | None:
    if expected_payload_text is None:
        return None
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != owner_name:
            continue
        for child in node.body:
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if child.name != function_name:
                continue
            for statement in ast.walk(child):
                if not _python_assignment_targets_name(statement, "payload"):
                    continue
                span = _python_ast_node_line_span(
                    source_text=source_text,
                    node=statement,
                )
                if span is None:
                    return None
                byte_start, byte_end = span
                before_text = source_text.encode("utf-8")[byte_start:byte_end].decode(
                    "utf-8"
                )
                if before_text.rstrip("\n") != expected_payload_text:
                    return None
                return byte_start, byte_end, before_text
    return None


def _python_orm_function_input_model_body_span(
    *,
    source_text: str,
    owner_name: str,
    function_name: str,
    expected_body_text: str | None,
) -> tuple[int, int, str] | None:
    if expected_body_text is None:
        return None
    input_model_name = _python_orm_function_input_model_name(
        owner_name=owner_name,
        function_name=function_name,
    )
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != input_model_name:
            continue
        if not node.body:
            return None
        first_child = node.body[0]
        last_child = node.body[-1]
        start_span = _python_ast_node_line_span(
            source_text=source_text,
            node=first_child,
        )
        end_span = _python_ast_node_line_span(
            source_text=source_text,
            node=last_child,
        )
        if start_span is None or end_span is None:
            return None
        byte_start = start_span[0]
        byte_end = end_span[1]
        before_text = source_text.encode("utf-8")[byte_start:byte_end].decode(
            "utf-8",
        )
        if before_text.rstrip("\n") != expected_body_text:
            return None
        return byte_start, byte_end, before_text
    return None


def _python_assignment_targets_name(node: ast.AST, name: str) -> bool:
    if not isinstance(node, ast.Assign):
        return False
    return any(
        isinstance(target, ast.Name) and target.id == name for target in node.targets
    )


def _python_replacement_with_preserved_line_suffix(
    *,
    before_text: str,
    replacement_text: str,
) -> str:
    if before_text.endswith("\n") and not replacement_text.endswith("\n"):
        return f"{replacement_text}\n"
    return replacement_text


def _python_orm_function_input_model_name(
    *,
    owner_name: str,
    function_name: str,
) -> str:
    return f"{owner_name}{_python_pascal_name(function_name)}Input"


def _python_pascal_name(value: str) -> str:
    parts = [part for part in value.replace("-", "_").split("_") if part]
    if not parts:
        return value[:1].upper() + value[1:]
    return "".join(part[:1].upper() + part[1:] for part in parts)


def _python_function_delete_span(
    *,
    source_text: str,
    owner_name: str,
    function_name: str,
) -> tuple[int, int, str] | None:
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != owner_name:
            continue
        for child in node.body:
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if child.name != function_name:
                continue
            span = _python_function_node_line_span(source_text=source_text, node=child)
            if span is None:
                return None
            byte_start, byte_end = span
            before_text = source_text.encode("utf-8")[byte_start:byte_end].decode(
                "utf-8",
            )
            return byte_start, byte_end, before_text
    return None


def _python_ast_node_line_span(
    *,
    source_text: str,
    node: ast.AST,
) -> tuple[int, int] | None:
    lines = source_text.splitlines(keepends=True)
    lineno = getattr(node, "lineno", None)
    end_lineno = getattr(node, "end_lineno", None)
    if not isinstance(lineno, int) or not isinstance(end_lineno, int):
        return None
    if lineno < 1 or end_lineno < lineno or lineno > len(lines):
        return None
    byte_start = len("".join(lines[: lineno - 1]).encode("utf-8"))
    byte_end = len("".join(lines[:end_lineno]).encode("utf-8"))
    return byte_start, byte_end


def _python_function_def_line_span(
    *,
    source_text: str,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[int, int] | None:
    lines = source_text.splitlines(keepends=True)
    if node.lineno < 1 or node.lineno > len(lines):
        return None
    line_prefix = "".join(lines[: node.lineno - 1])
    line = lines[node.lineno - 1]
    line_start = len(line_prefix.encode("utf-8"))
    line_bytes = line.encode("utf-8")
    if node.col_offset < 0 or node.col_offset >= len(line_bytes):
        return None
    # Parameter annotations contain earlier colons; the span ends at the
    # function definition line terminator.
    colon_offset = line_bytes.rfind(b":")
    if colon_offset < node.col_offset:
        return None
    return line_start + node.col_offset, line_start + colon_offset + 1


def _python_function_node_line_span(
    *,
    source_text: str,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[int, int] | None:
    lines = source_text.splitlines(keepends=True)
    end_lineno = getattr(node, "end_lineno", None)
    if not isinstance(end_lineno, int):
        return None
    if node.lineno < 1 or end_lineno < node.lineno or node.lineno > len(lines):
        return None
    byte_start = len("".join(lines[: node.lineno - 1]).encode("utf-8"))
    byte_end = len("".join(lines[:end_lineno]).encode("utf-8"))
    return byte_start, byte_end


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


def _target_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
) -> CodeGeneratedMaterializationTargetRef:
    owner_key = _owner_key(operation=operation)
    owner_name = _owner_name(operation=operation)
    function_name = _function_name(operation=operation)
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
        provider_key=META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=(
            META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
        ),
        target_language=context.target_language,
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        renderer_key=_renderer_key(operation=operation),
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        output_key=owner_name,
        relative_path=_generated_relative_path(
            operation=operation,
            context=context,
        ),
        metadata=_json_object(
            {
                "source": ("aware_meta.provider_delta.python_orm_function_target_ref"),
                "operation_key": operation.operation_key,
                "owner_key": owner_key,
                "owner_name": owner_name,
                "function_name": function_name,
            }
        ),
    )


def _anchor_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
) -> CodeGeneratedRendererAnchorRef:
    owner_key = _owner_key(operation=operation)
    owner_name = _owner_name(operation=operation)
    function_name = _function_name(operation=operation)
    invocation_position = _invocation_position(operation=operation)
    is_invocation = operation.ontology_subject_kind == "function_invocation"
    anchor_path = ".".join(
        part
        for part in (
            owner_name,
            function_name,
            (
                f"invocation[{invocation_position}]"
                if is_invocation and invocation_position is not None
                else None
            ),
        )
        if part
    )
    return CodeGeneratedRendererAnchorRef(
        anchor_key=(
            META_PYTHON_ORM_FUNCTION_INVOCATION_ANCHOR_KEY
            if is_invocation
            else META_PYTHON_ORM_FUNCTION_ANCHOR_KEY
        ),
        anchor_path=anchor_path,
        anchor_role=(
            "function_invocation_plan" if is_invocation else "function_section"
        ),
        renderer_key=_renderer_key(operation=operation),
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        target_language=context.target_language,
        section_type="function",
        segment_name=("body" if is_invocation else "function"),
        graph_selector=_json_object(
            {
                "provider_key": (
                    META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY
                ),
                "semantic_owner": (
                    META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
                ),
                "class_fqn": owner_key,
                "class_name": owner_name,
                "function_name": function_name,
                "function_path": anchor_path,
                "function_semantic_key": _function_semantic_key(
                    operation=operation,
                ),
                "invocation_position": invocation_position,
            }
        ),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta." "python_orm_function_generated_anchor"
                ),
                "operation_key": operation.operation_key,
                "semantic_key": operation.semantic_key,
            }
        ),
    )


def _python_orm_function_context(
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> MetaPythonOrmFunctionGeneratedMaterializationContext:
    sources_root = _python_orm_sources_root(
        package_name=context.package_name,
        sources_root=context.sources_root,
    )
    return MetaPythonOrmFunctionGeneratedMaterializationContext(
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


def _generated_relative_path(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaPythonOrmFunctionGeneratedMaterializationContext,
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
        python_orm = orm_runtime_target_payload(payload)
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


def _is_authored_aware_sources_root(sources_root: str | None) -> bool:
    return sources_root is None or sources_root == "aware"


def _renderer_key(*, operation: MetaProviderDeltaTypedOperation) -> str:
    if operation.ontology_subject_kind == "function_invocation":
        return META_PYTHON_ORM_FUNCTION_INVOCATION_RENDERER_KEY
    return META_PYTHON_ORM_FUNCTION_RENDERER_KEY


def _policy_key(*, operation: MetaProviderDeltaTypedOperation) -> str:
    if operation.ontology_subject_kind == "function_invocation":
        return "aware_meta.python_orm.function_invocation_plan"
    return "aware_meta.python_orm.function"


def _function_signature(*, payload: Mapping[str, object]) -> Mapping[str, object]:
    signature = mapping_value(payload.get("function_signature"))
    if signature:
        return signature
    nested_payload = mapping_value(payload.get("payload"))
    signature = mapping_value(nested_payload.get("function_signature"))
    if signature:
        return signature
    object_payload = mapping_value(payload.get("object"))
    signature = mapping_value(object_payload.get("function_signature"))
    if signature:
        return signature
    baseline_object = mapping_value(payload.get("baseline_object"))
    return mapping_value(baseline_object.get("function_signature"))


_MISSING = object()


def _description_value(*, payload: Mapping[str, object]) -> object:
    if "description" not in payload:
        return _MISSING
    return payload["description"]


def _function_name(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return (
        optional_text(operation.current.get("function_name"))
        or optional_text(_function_signature(payload=operation.current).get("name"))
        or _function_name_from_semantic_key(_function_semantic_key(operation=operation))
    )


def _function_semantic_key(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str:
    return (
        optional_text(operation.current.get("function_semantic_key"))
        or optional_text(operation.current.get("parent_semantic_key"))
        or _function_semantic_key_from_invocation_key(operation.semantic_key)
        or operation.semantic_key
    )


def _owner_semantic_key(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str:
    return (
        optional_text(operation.current.get("owner_semantic_key"))
        or _owner_key(operation=operation)
        or operation.semantic_key
    )


def _function_name_from_semantic_key(semantic_key: str) -> str | None:
    function_marker = "/function:"
    if function_marker in semantic_key:
        return semantic_key.split(function_marker, maxsplit=1)[-1].split(
            "/",
            maxsplit=1,
        )[0]
    raw_name = semantic_key.rsplit("/", maxsplit=1)[-1].rsplit(".", maxsplit=1)[-1]
    if not raw_name or ":" in raw_name:
        return None
    return raw_name


def _function_semantic_key_from_invocation_key(semantic_key: str) -> str | None:
    invocation_marker = "/invocation:"
    if invocation_marker not in semantic_key:
        return None
    return semantic_key.split(invocation_marker, maxsplit=1)[0]


def _owner_key(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return (
        optional_text(operation.current.get("owner_key"))
        or optional_text(operation.current.get("owner_semantic_key"))
        or optional_text(
            _function_signature(payload=operation.current).get("owner_key")
        )
        or _owner_key_from_semantic_key(_function_semantic_key(operation=operation))
    )


def _owner_name(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    owner_key = _owner_key(operation=operation)
    if owner_key is None:
        return None
    return owner_key.rsplit(".", maxsplit=1)[-1]


def _owner_key_from_semantic_key(semantic_key: str) -> str | None:
    node_marker = "/node:"
    if node_marker not in semantic_key:
        return None
    node_key = semantic_key.split(node_marker, maxsplit=1)[-1]
    if "/function:" in node_key:
        return node_key.split("/function:", maxsplit=1)[0]
    return node_key.rsplit(".", maxsplit=1)[0]


def _invocation_position(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> int | None:
    position = operation.current.get("position")
    return position if isinstance(position, int) else None


def _function_is_async(*, operation: MetaProviderDeltaTypedOperation) -> bool:
    value = operation.current.get("is_async") or _function_signature(
        payload=operation.current
    ).get("is_async")
    return value if isinstance(value, bool) else False


def _function_is_constructor(*, operation: MetaProviderDeltaTypedOperation) -> bool:
    value = operation.current.get("is_constructor") or _function_signature(
        payload=operation.current
    ).get("is_constructor")
    if isinstance(value, bool):
        return value
    kind = optional_text(operation.current.get("kind")) or optional_text(
        _function_signature(payload=operation.current).get("kind")
    )
    return kind == "construct"


def _python_double_quoted(value: str) -> str:
    return (
        '"'
        + value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
        + '"'
    )


def _python_python_literal(value: object) -> str:
    if value is None:
        return "None"
    if isinstance(value, str):
        return _python_double_quoted(value)
    if isinstance(value, bool):
        return _python_bool_literal(value)
    return repr(value)


def _python_bool_literal(value: bool) -> str:
    return "True" if value else "False"


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


def _language_plugin_metadata(
    language_plugin_delta_renderer: str | None,
) -> dict[str, object]:
    if language_plugin_delta_renderer is None:
        return {}
    return {"language_plugin_delta_renderer": language_plugin_delta_renderer}


def _json_object(payload: Mapping[str, object]) -> JsonObject:
    return JsonObject(cast(Any, dict(payload)))


def _sha256_digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


__all__ = [
    "META_PYTHON_ORM_FUNCTION_ANCHOR_KEY",
    "META_PYTHON_ORM_FUNCTION_EVIDENCE_ONLY_DIAGNOSTIC",
    "META_PYTHON_ORM_FUNCTION_GENERATED_MATERIALIZATION_PROVIDER_KEY",
    "META_PYTHON_ORM_FUNCTION_GUARDED_DELTA_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_FUNCTION_INVOCATION_ANCHOR_KEY",
    "META_PYTHON_ORM_FUNCTION_INVOCATION_BASELINE_BODY_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_FUNCTION_INVOCATION_BODY_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_FUNCTION_INVOCATION_RENDERER_KEY",
    "META_PYTHON_ORM_FUNCTION_RENDERER_KEY",
    "META_PYTHON_ORM_FUNCTION_SIGNATURE_SPAN_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_FUNCTION_SIGNATURE_TEXT_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_FUNCTION_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_FUNCTION_UPDATE_BODY_MISSING_DIAGNOSTIC",
    "META_PYTHON_ORM_FUNCTION_UPDATE_UNSUPPORTED_DIAGNOSTIC",
    "MetaPythonOrmFunctionGeneratedMaterializationContext",
    "MetaPythonOrmFunctionGeneratedMaterializationDeltaEvidence",
    "generated_materialization_feature_results_from_function_config_typed_operation",
    "python_orm_generated_materialization_delta_from_function_config_typed_operation",
    "render_python_orm_function_generated_delta",
    "supports_python_orm_function_generated_delta",
]
