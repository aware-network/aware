from __future__ import annotations

import ast
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from hashlib import sha256
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
    MetaLanguageGeneratedMaterializationDeltaRenderResult,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_types import JsonObject
from python_grammar.renderer_delta_orm_targets import (
    ORM_RUNTIME_PRODUCT_INTENT,
    orm_runtime_target_payload,
)


PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME = "python_orm_runtime"
PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY = "aware_meta"
PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER = "aware_meta.ocg"
PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PRODUCT_INTENT = (
    ORM_RUNTIME_PRODUCT_INTENT
)
PYTHON_ORM_RELATIONSHIP_RENDERER_PROFILE = "orm_runtime"
PYTHON_ORM_RELATIONSHIP_MATERIALIZATION_SOURCE = "ontology_orm_models"
PYTHON_ORM_RELATIONSHIP_RENDERER_KEY = "python.orm.relationship.load_policy"
PYTHON_ORM_RELATIONSHIP_ANCHOR_KEY = "python.orm.relationship.field"
PYTHON_ORM_RELATIONSHIP_EVIDENCE_ONLY_DIAGNOSTIC = (
    "meta_python_orm_relationship_generated_materialization_renderer_operation_"
    "evidence_only"
)
PYTHON_ORM_RELATIONSHIP_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC = (
    "meta_python_orm_relationship_generated_materialization_target_relative_path_"
    "missing"
)
PYTHON_ORM_RELATIONSHIP_FIELD_SPAN_MISSING_DIAGNOSTIC = (
    "meta_python_orm_relationship_generated_materialization_field_span_missing"
)
PYTHON_ORM_RELATIONSHIP_FIELD_TEXT_MISSING_DIAGNOSTIC = (
    "meta_python_orm_relationship_generated_materialization_field_text_missing"
)
PYTHON_ORM_RELATIONSHIP_STRUCTURAL_CREATE_SPAN_MISSING_DIAGNOSTIC = (
    "meta_python_orm_relationship_generated_materialization_create_span_missing"
)
PYTHON_ORM_RELATIONSHIP_STRUCTURAL_DELETE_SPAN_MISSING_DIAGNOSTIC = (
    "meta_python_orm_relationship_generated_materialization_delete_span_missing"
)
PYTHON_ORM_RELATIONSHIP_NOT_REQUIRED_REASON = (
    "meta_python_orm_relationship_load_policy_delta_not_required"
)


@dataclass(frozen=True, slots=True)
class _PythonOrmRelationshipFieldDeltaEvidence:
    grammar_anchor_render_delta: ResolveCodeGrammarAnchorRenderDeltaRequest
    content_text: str
    before_hash: str
    after_hash: str


@dataclass(frozen=True, slots=True)
class _PythonOrmRelationshipTextSpanReplacement:
    replacement_key: str
    byte_start: int
    byte_end: int
    before_text: str
    replacement_text: str
    field_name: str
    field_path: str


def supports_python_orm_relationship_generated_delta(
    request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
) -> bool:
    operation = request.operation
    return (
        operation.ontology_subject_kind == "relationship"
        and operation.operation_family in {"create", "delete", "update"}
    )


def render_python_orm_relationship_generated_delta(
    request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
) -> MetaLanguageGeneratedMaterializationDeltaRenderResult:
    if not supports_python_orm_relationship_generated_delta(request):
        return MetaLanguageGeneratedMaterializationDeltaRenderResult.unhandled(
            reason="python_orm_relationship_generated_delta_operation_not_supported",
        )
    operation = request.operation
    context = _context_with_defaults(request.context)
    event_key = meta_provider_delta_world_change_event_key(operation=operation)
    target = _target_ref(operation=operation, context=context)
    delta_request = _delta_request(
        operation=operation,
        context=context,
        event_key=event_key,
        target=target,
    )
    result = _relationship_result(
        operation=operation,
        context=context,
        event_key=event_key,
        target=target,
    )
    return MetaLanguageGeneratedMaterializationDeltaRenderResult.from_evidence(
        delta_request=delta_request,
        result=result,
        reason="python_orm_runtime_relationship_generated_delta_rendered",
    )


def _context_with_defaults(
    context: MetaLanguageGeneratedMaterializationDeltaContext,
) -> MetaLanguageGeneratedMaterializationDeltaContext:
    sources_root = _python_orm_sources_root(
        package_name=context.package_name,
        sources_root=context.sources_root,
    )
    return MetaLanguageGeneratedMaterializationDeltaContext(
        package_name=context.package_name,
        package_root=_python_orm_package_root(
            package_root=context.package_root,
            source_sources_root=context.sources_root,
            generated_sources_root=sources_root,
        ),
        sources_root=sources_root,
        target_language=context.target_language or "python",
        renderer_profile=(
            context.renderer_profile or PYTHON_ORM_RELATIONSHIP_RENDERER_PROFILE
        ),
        materialization_source=(
            context.materialization_source
            or PYTHON_ORM_RELATIONSHIP_MATERIALIZATION_SOURCE
        ),
        product_intent=(
            context.product_intent
            or PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PRODUCT_INTENT
        ),
        artifact_family=context.artifact_family or "ocg_language_materialization",
        artifact_role=context.artifact_role or "python_orm_model",
        target_hints=context.target_hints,
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


def _delta_request(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
) -> CodeGeneratedMaterializationDeltaRequest:
    return CodeGeneratedMaterializationDeltaRequest(
        provider_key=PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=(
            PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
        ),
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        product_intent=context.product_intent,
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
                renderer_key=PYTHON_ORM_RELATIONSHIP_RENDERER_KEY,
                metadata=_json_object(
                    {
                        "source": (
                            "python_grammar."
                            "python_orm_relationship_generated_delta_action"
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
                    "python_grammar." "python_orm_relationship_generated_delta_request"
                ),
                "renderer_profile": context.renderer_profile,
                "materialization_source": context.materialization_source,
                "language_plugin_delta_renderer": (
                    PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
                ),
            }
        ),
    )


def _relationship_result(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
) -> CodeGeneratedMaterializationDeltaResult:
    if _relationship_structural_create_required(operation=operation):
        delta_evidence = _relationship_create_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    elif _relationship_structural_delete_required(operation=operation):
        delta_evidence = _relationship_delete_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    elif _relationship_load_policy_changed(operation=operation):
        delta_evidence = _relationship_field_delta_evidence(
            operation=operation,
            context=context,
            target=target,
            event_key=event_key,
        )
    else:
        return CodeGeneratedMaterializationDeltaResult(
            provider_key=(
                PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY
            ),
            semantic_owner=(
                PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
            ),
            available=True,
            mode=CodeGeneratedMaterializationDeltaMode.not_required,
            skipped_targets=[
                CodeGeneratedMaterializationSkippedTarget(
                    target=target,
                    reason=PYTHON_ORM_RELATIONSHIP_NOT_REQUIRED_REASON,
                    event_refs=[event_key],
                )
            ],
            metadata=_json_object(
                {
                    "language_plugin_delta_renderer": (
                        PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
                    ),
                }
            ),
        )
    has_delta = delta_evidence is not None
    diagnostics = (
        ()
        if has_delta
        else _guarded_delta_diagnostics(operation=operation, target=target)
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
        renderer_key=PYTHON_ORM_RELATIONSHIP_RENDERER_KEY,
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
                "source": "python_grammar.python_orm_relationship_operation",
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "mode_reason": (
                    "python_orm_relationship_grammar_anchor_render_delta_ready"
                    if has_delta
                    else "python_orm_relationship_guarded_delta_missing"
                ),
                "language_plugin_delta_renderer": (
                    PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
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
                    "python_grammar." "python_orm_relationship_generated_delta_entry"
                ),
                "operation_key": operation.operation_key,
                "package_delta_emitted": False,
                "section_delta_emitted": False,
                "grammar_anchor_render_delta_emitted": has_delta,
                "language_plugin_delta_renderer": (
                    PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
                ),
            }
        ),
    )
    return CodeGeneratedMaterializationDeltaResult(
        provider_key=PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=(
            PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
        ),
        available=True,
        mode=entry_mode,
        entries=[entry],
        diagnostics=list(diagnostics),
        metadata=_json_object(
            {
                "source": (
                    "python_grammar." "python_orm_relationship_generated_delta_result"
                ),
                "operation_key": operation.operation_key,
                "renderer_operation_count": 1,
                "package_delta_emitted": False,
                "section_delta_emitted": False,
                "grammar_anchor_render_delta_emitted": has_delta,
                "language_plugin_delta_renderer": (
                    PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
                ),
            }
        ),
    )


def _relationship_field_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
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
    source_state = _generated_source_state(context=context, target=target)
    if (
        class_name is None
        or relationship_key is None
        or replacement_text is None
        or source_state is None
    ):
        return None
    relative_path, source_text = source_state
    relationship_span = _python_relationship_field_span(
        source_text=source_text,
        class_name=class_name,
        relationship_key=relationship_key,
    )
    foreign_key = _relationship_foreign_key_name(relationship_key)
    foreign_key_replacement_text = _python_relationship_foreign_key_field_text(
        operation=operation,
    )
    if foreign_key is None or foreign_key_replacement_text is None:
        return None
    foreign_key_span = _python_relationship_field_span(
        source_text=source_text,
        class_name=class_name,
        relationship_key=foreign_key,
    )
    if (
        relationship_span is None
        or foreign_key_span is None
    ):
        return None
    byte_start, byte_end, before_text = relationship_span
    fk_byte_start, fk_byte_end, fk_before_text = foreign_key_span
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
        operation_label="load_policy",
        additional_replacements=(
            _PythonOrmRelationshipTextSpanReplacement(
                replacement_key=(
                    "aware_meta.python_orm.relationship.foreign_key."
                    f"load_policy:{operation.operation_key}"
                ),
                byte_start=fk_byte_start,
                byte_end=fk_byte_end,
                before_text=fk_before_text,
                replacement_text=foreign_key_replacement_text,
                field_name="relationship_foreign_key",
                field_path=".".join(
                    part for part in (class_name, foreign_key, "__field__") if part
                ),
            ),
        ),
    )
    if grammar_anchor_render_delta is None:
        return None
    return _PythonOrmRelationshipFieldDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
    )


def _relationship_create_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
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
    replacement_text = _python_relationship_create_relationship_section_text(
        operation=operation,
    )
    source_state = _generated_source_state(context=context, target=target)
    if (
        class_name is None
        or relationship_key is None
        or replacement_text is None
        or source_state is None
    ):
        return None
    relative_path, source_text = source_state
    span = _python_relationship_create_relationship_section_insert_span(
        source_text=source_text,
        class_name=class_name,
        relationship_key=relationship_key,
    )
    if span is None:
        return None
    byte_start, byte_end, before_text = span
    additional_replacements = _relationship_create_structural_replacements(
        operation=operation,
        context=context,
        source_text=source_text,
        class_name=class_name,
        event_key=event_key,
    )
    if additional_replacements is None:
        return None
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
        additional_replacements=additional_replacements,
    )
    if grammar_anchor_render_delta is None:
        return None
    return _PythonOrmRelationshipFieldDeltaEvidence(
        grammar_anchor_render_delta=grammar_anchor_render_delta,
        content_text=replacement_text,
        before_hash=before_hash,
        after_hash=after_hash,
    )


def _relationship_delete_delta_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
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
    source_state = _generated_source_state(context=context, target=target)
    if class_name is None or relationship_key is None or source_state is None:
        return None
    relative_path, source_text = source_state
    span = _python_relationship_delete_relationship_section_span(
        source_text=source_text,
        class_name=class_name,
        relationship_key=relationship_key,
    )
    if span is None:
        return None
    byte_start, byte_end, before_text = span
    replacement_text = ""
    additional_replacements = _relationship_delete_structural_replacements(
        operation=operation,
        source_text=source_text,
        class_name=class_name,
        relationship_key=relationship_key,
        relationship_span=span,
        event_key=event_key,
    )
    if additional_replacements is None:
        return None
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
        additional_replacements=additional_replacements,
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
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    target: CodeGeneratedMaterializationTargetRef,
    relative_path: str,
    source_text: str,
    byte_start: int,
    byte_end: int,
    before_text: str,
    replacement_text: str,
    event_key: str,
    operation_label: str,
    additional_replacements: tuple[_PythonOrmRelationshipTextSpanReplacement, ...] = (),
) -> ResolveCodeGrammarAnchorRenderDeltaRequest | None:
    source_hash = _sha256_digest(source_text)
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
    primary_replacement = _PythonOrmRelationshipTextSpanReplacement(
        replacement_key=(
            "aware_meta.python_orm.relationship.field."
            f"{operation_label}:{operation.operation_key}"
        ),
        byte_start=byte_start,
        byte_end=byte_end,
        before_text=before_text,
        replacement_text=replacement_text,
        field_name="relationship_field",
        field_path=".".join(
            part
            for part in (
                _source_class_name(operation=operation),
                _relationship_key(operation=operation),
                "__field__",
            )
            if part
        ),
    )
    replacements = (primary_replacement, *additional_replacements)
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
                replacement_key=replacement.replacement_key,
                byte_start=replacement.byte_start,
                byte_end=replacement.byte_end,
                before_text=replacement.before_text,
                replacement_text=replacement.replacement_text,
                graph_selector=_relationship_field_graph_selector(
                    operation=operation,
                    field_name=replacement.field_name,
                    field_path=replacement.field_path,
                ),
                metadata=_json_object(
                    {
                        "source": "python_grammar.python_orm_relationship_span",
                        "operation_key": operation.operation_key,
                        "relationship_key": _relationship_key(
                            operation=operation,
                        ),
                        "language_plugin_delta_renderer": (
                            PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
                        ),
                    }
                ),
            )
            for replacement in replacements
        ],
        metadata=_json_object(
            {
                "source": (
                    "python_grammar."
                    "python_orm_relationship_grammar_anchor_render_delta"
                ),
                "operation_key": operation.operation_key,
                "target_kind": CodeGrammarAnchorRenderTargetKind.text_span.value,
                "renderer_key": PYTHON_ORM_RELATIONSHIP_RENDERER_KEY,
                "renderer_profile": context.renderer_profile,
                "language_plugin_delta_renderer": (
                    PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
                ),
            }
        ),
    )


def _relationship_field_graph_selector(
    *,
    operation: MetaProviderDeltaTypedOperation,
    field_name: str = "relationship_field",
    field_path: str | None = None,
) -> CodeGraphFieldSelector:
    class_fqn = _source_class_fqn(operation=operation)
    class_name = _source_class_name(operation=operation)
    relationship_key = _relationship_key(operation=operation)
    resolved_field_path = field_path or ".".join(
        part for part in (class_name, relationship_key, "__field__") if part
    )
    return CodeGraphFieldSelector(
        provider_key=PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=(
            PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
        ),
        subject_kind="relationship_config",
        subject_type="ClassConfigRelationship",
        semantic_key=operation.semantic_key,
        object_key=class_fqn,
        field_name=field_name,
        field_path=resolved_field_path,
        class_fqn=class_fqn,
        class_name=class_name,
        metadata=_json_object(
            {
                "source": "python_grammar.python_orm_relationship_graph_selector",
                "operation_key": operation.operation_key,
                "relationship_key": relationship_key,
            }
        ),
    )


def _relationship_create_structural_replacements(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    source_text: str,
    class_name: str,
    event_key: str,
) -> tuple[_PythonOrmRelationshipTextSpanReplacement, ...] | None:
    replacements: list[_PythonOrmRelationshipTextSpanReplacement] = []
    import_replacements = _python_relationship_required_import_replacements(
        source_text=source_text,
        operation=operation,
        context=context,
    )
    if import_replacements is None:
        return None
    replacements.extend(import_replacements)

    relationship_key = _relationship_key(operation=operation)
    foreign_key = _relationship_foreign_key_name(relationship_key)
    foreign_key_section_text = _python_relationship_create_foreign_key_section_text(
        operation=operation,
    )
    foreign_key_span = _python_relationship_create_foreign_key_section_insert_span(
        source_text=source_text,
        class_name=class_name,
        relationship_key=relationship_key,
    )
    if (
        foreign_key is None
        or foreign_key_section_text is None
        or foreign_key_span is None
    ):
        return None
    byte_start, byte_end, before_text = foreign_key_span
    replacements.append(
        _PythonOrmRelationshipTextSpanReplacement(
            replacement_key=(
                "aware_meta.python_orm.relationship.foreign_key."
                f"create:{operation.operation_key}"
            ),
            byte_start=byte_start,
            byte_end=byte_end,
            before_text=before_text,
            replacement_text=foreign_key_section_text,
            field_name="relationship_foreign_key",
            field_path=".".join(
                part for part in (class_name, foreign_key, "__field__") if part
            ),
        )
    )
    return tuple(replacements)


def _relationship_delete_structural_replacements(
    *,
    operation: MetaProviderDeltaTypedOperation,
    source_text: str,
    class_name: str,
    relationship_key: str,
    relationship_span: tuple[int, int, str],
    event_key: str,
) -> tuple[_PythonOrmRelationshipTextSpanReplacement, ...] | None:
    foreign_key = _relationship_foreign_key_name(relationship_key)
    foreign_key_span = _python_relationship_delete_foreign_key_section_span(
        source_text=source_text,
        class_name=class_name,
        relationship_key=relationship_key,
    )
    if foreign_key is None or foreign_key_span is None:
        return None
    fk_byte_start, fk_byte_end, fk_before_text = foreign_key_span
    preview_text = _preview_text_span_replacements(
        source_text=source_text,
        replacements=(
            (relationship_span[0], relationship_span[1], ""),
            (fk_byte_start, fk_byte_end, ""),
        ),
    )
    import_replacements = _python_relationship_unused_import_delete_replacements(
        source_text=source_text,
        preview_text=preview_text,
        operation=operation,
    )
    if import_replacements is None:
        return None
    return (
        _PythonOrmRelationshipTextSpanReplacement(
            replacement_key=(
                "aware_meta.python_orm.relationship.foreign_key."
                f"delete:{operation.operation_key}"
            ),
            byte_start=fk_byte_start,
            byte_end=fk_byte_end,
            before_text=fk_before_text,
            replacement_text="",
            field_name="relationship_foreign_key",
            field_path=".".join(
                part for part in (class_name, foreign_key, "__field__") if part
            ),
        ),
        *import_replacements,
    )


def _python_relationship_field_span(
    *,
    source_text: str,
    class_name: str,
    relationship_key: str,
) -> tuple[int, int, str] | None:
    node = _python_relationship_field_node(
        source_text=source_text,
        class_name=class_name,
        relationship_key=relationship_key,
    )
    if node is None:
        return None
    return _node_line_span(source_text=source_text, node=node)


def _python_relationship_field_node(
    *,
    source_text: str,
    class_name: str,
    relationship_key: str,
) -> ast.AnnAssign | None:
    class_node = _python_class_node(source_text=source_text, class_name=class_name)
    if class_node is None:
        return None
    for node in class_node.body:
        if not isinstance(node, ast.AnnAssign):
            continue
        target = node.target
        if isinstance(target, ast.Name) and target.id == relationship_key:
            return node
    return None


def _python_relationship_create_relationship_section_insert_span(
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
    lines = source_text.splitlines(keepends=True)
    attributes_line = _python_class_section_marker_line(
        lines=lines,
        class_node=class_node,
        marker="Attributes",
    )
    if attributes_line is None:
        first_field_line = _python_class_first_field_line(class_node=class_node)
        if first_field_line is None:
            return None
        return _line_range_span(
            source_text=source_text,
            lines=lines,
            start_line=first_field_line,
            end_line=first_field_line,
        )
    return _line_range_span(
        source_text=source_text,
        lines=lines,
        start_line=attributes_line,
        end_line=attributes_line,
    )


def _python_relationship_create_foreign_key_section_insert_span(
    *,
    source_text: str,
    class_name: str,
    relationship_key: str | None,
) -> tuple[int, int, str] | None:
    foreign_key = _relationship_foreign_key_name(relationship_key)
    if foreign_key is None:
        return None
    class_node = _python_class_node(source_text=source_text, class_name=class_name)
    if class_node is None or _python_class_has_field(
        class_node=class_node,
        field_name=foreign_key,
    ):
        return None
    end_lineno_value = getattr(class_node, "end_lineno", None)
    if not isinstance(end_lineno_value, int):
        return None
    lines = source_text.splitlines(keepends=True)
    if end_lineno_value <= 0 or end_lineno_value > len(lines):
        return None
    return _line_range_span(
        source_text=source_text,
        lines=lines,
        start_line=end_lineno_value,
        end_line=end_lineno_value,
    )


def _python_relationship_delete_relationship_section_span(
    *,
    source_text: str,
    class_name: str,
    relationship_key: str,
) -> tuple[int, int, str] | None:
    return _python_relationship_delete_section_span(
        source_text=source_text,
        class_name=class_name,
        field_name=relationship_key,
        marker="Relationships",
        include_preceding_blank=False,
    )


def _python_relationship_delete_foreign_key_section_span(
    *,
    source_text: str,
    class_name: str,
    relationship_key: str,
) -> tuple[int, int, str] | None:
    foreign_key = _relationship_foreign_key_name(relationship_key)
    if foreign_key is None:
        return None
    return _python_relationship_delete_section_span(
        source_text=source_text,
        class_name=class_name,
        field_name=foreign_key,
        marker="Foreign Keys",
        include_preceding_blank=True,
    )


def _python_relationship_delete_section_span(
    *,
    source_text: str,
    class_name: str,
    field_name: str,
    marker: str,
    include_preceding_blank: bool,
) -> tuple[int, int, str] | None:
    class_node = _python_class_node(source_text=source_text, class_name=class_name)
    field_node = _python_relationship_field_node(
        source_text=source_text,
        class_name=class_name,
        relationship_key=field_name,
    )
    if class_node is None or field_node is None:
        return None
    lines = source_text.splitlines(keepends=True)
    field_start_line = getattr(field_node, "lineno", None)
    field_end_line = getattr(field_node, "end_lineno", None)
    if not isinstance(field_start_line, int) or not isinstance(field_end_line, int):
        return None
    marker_line = field_start_line - 2
    if marker_line >= 0 and lines[marker_line] == f"    # {marker}\n":
        section_end_line = _python_class_section_end_line(
            lines=lines,
            class_node=class_node,
            marker_line=marker_line,
        )
        if section_end_line is None:
            return None
        section_field_lines = _python_section_field_lines(
            lines=lines,
            start_line=marker_line + 1,
            end_line=section_end_line,
        )
        if section_field_lines == (field_start_line - 1,):
            start_line = marker_line
            if (
                include_preceding_blank
                and start_line > 0
                and not lines[start_line - 1].strip()
            ):
                start_line -= 1
            return _line_range_span(
                source_text=source_text,
                lines=lines,
                start_line=start_line,
                end_line=section_end_line,
            )
    return _node_line_span(source_text=source_text, node=field_node)


def _python_class_section_marker_line(
    *,
    lines: list[str],
    class_node: ast.ClassDef,
    marker: str,
) -> int | None:
    class_start = getattr(class_node, "lineno", None)
    class_end = getattr(class_node, "end_lineno", None)
    if not isinstance(class_start, int) or not isinstance(class_end, int):
        return None
    for line_index in range(class_start, class_end):
        if line_index >= len(lines):
            return None
        if lines[line_index] == f"    # {marker}\n":
            return line_index
    return None


def _python_class_first_field_line(*, class_node: ast.ClassDef) -> int | None:
    field_lines = tuple(
        getattr(node, "lineno", None)
        for node in class_node.body
        if isinstance(node, (ast.AnnAssign, ast.Assign))
    )
    int_lines = tuple(line for line in field_lines if isinstance(line, int))
    if not int_lines:
        return None
    return min(int_lines) - 1


def _python_class_section_end_line(
    *,
    lines: list[str],
    class_node: ast.ClassDef,
    marker_line: int,
) -> int | None:
    class_end = getattr(class_node, "end_lineno", None)
    if not isinstance(class_end, int):
        return None
    for line_index in range(marker_line + 1, class_end):
        if line_index >= len(lines):
            return None
        if line_index != marker_line + 1 and _python_orm_section_marker_line(
            lines[line_index]
        ):
            return line_index
    return class_end


def _python_section_field_lines(
    *,
    lines: list[str],
    start_line: int,
    end_line: int,
) -> tuple[int, ...]:
    field_lines: list[int] = []
    for line_index in range(start_line, end_line):
        stripped = lines[line_index].strip()
        if not stripped or stripped.startswith("#"):
            continue
        field_lines.append(line_index)
    return tuple(field_lines)


def _python_orm_section_marker_line(line: str) -> bool:
    stripped = line.strip()
    return line.startswith("    # ") and stripped in {
        "# Attributes",
        "# Relationships",
        "# Foreign Keys",
        "# Functions",
    }


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


def _line_range_span(
    *,
    source_text: str,
    lines: list[str],
    start_line: int,
    end_line: int,
) -> tuple[int, int, str] | None:
    if start_line < 0 or end_line < start_line or end_line > len(lines):
        return None
    byte_start = len("".join(lines[:start_line]).encode("utf-8"))
    byte_end = len("".join(lines[:end_line]).encode("utf-8"))
    before_text = source_text.encode("utf-8")[byte_start:byte_end].decode("utf-8")
    return byte_start, byte_end, before_text


def _byte_offset_for_char_index(source_text: str, char_index: int) -> int:
    return len(source_text[:char_index].encode("utf-8"))


def _python_relationship_field_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    relationship_key = _relationship_key(operation=operation)
    target_class_name = _target_class_name(operation=operation)
    if relationship_key is None or target_class_name is None:
        return None
    strategy = _current_forward_loading_strategy(operation=operation) or "lazy"
    if strategy == "eager":
        return f"    {relationship_key}: {target_class_name}\n"
    if strategy == "lazy":
        return (
            f"    {relationship_key}: {target_class_name} | None = "
            "Field(default=None, exclude=True)\n"
        )
    return None


def _python_relationship_create_relationship_section_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    field_text = _python_relationship_field_text(operation=operation)
    if field_text is None:
        return None
    return f"    # Relationships\n{field_text}\n"


def _python_relationship_create_foreign_key_section_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    field_text = _python_relationship_foreign_key_field_text(operation=operation)
    if field_text is None:
        return None
    return f"\n    # Foreign Keys\n{field_text}"


def _python_relationship_foreign_key_field_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    relationship_key = _relationship_key(operation=operation)
    class_name = _source_class_name(operation=operation)
    foreign_key = _relationship_foreign_key_name(relationship_key)
    if relationship_key is None or class_name is None or foreign_key is None:
        return None
    description = f"Foreign key for {class_name}.{relationship_key}"
    description_literal = json.dumps(description)
    strategy = _current_forward_loading_strategy(operation=operation) or "lazy"
    if strategy == "eager":
        return (
            f"    {foreign_key}: UUID | None = "
            f"Field(default=None, description={description_literal})\n"
        )
    if strategy == "lazy":
        return (
            f"    {foreign_key}: UUID | None = "
            f"Field(default=None, description={description_literal})\n"
        )
    return None


def _relationship_foreign_key_name(relationship_key: str | None) -> str | None:
    if relationship_key is None:
        return None
    return f"{relationship_key}_id"


def _python_relationship_required_import_replacements(
    *,
    source_text: str,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
) -> tuple[_PythonOrmRelationshipTextSpanReplacement, ...] | None:
    has_uuid_import = "from uuid import UUID\n" in source_text
    has_field_import = "from pydantic import Field\n" in source_text
    has_type_checking_import = "from typing import TYPE_CHECKING\n" in source_text
    type_checking_replacement = _python_relationship_type_checking_import_replacement(
        source_text=source_text,
        operation=operation,
        context=context,
    )
    if has_uuid_import and has_field_import and type_checking_replacement is None:
        return ()

    orm_marker = "# Orm\n"
    orm_marker_index = source_text.find(orm_marker)
    if orm_marker_index < 0:
        byte_start = _python_markerless_relationship_import_insert_offset(
            source_text=source_text,
        )
        if byte_start is None:
            return None
        replacement_parts: list[str] = []
        if type_checking_replacement is not None and not has_type_checking_import:
            replacement_parts.extend(("from typing import TYPE_CHECKING\n", "\n"))
        if not has_uuid_import:
            replacement_parts.extend(("from uuid import UUID\n", "\n"))
        if not has_field_import:
            replacement_parts.extend(("from pydantic import Field\n", "\n"))
        replacements = [
            _PythonOrmRelationshipTextSpanReplacement(
                replacement_key=(
                    "aware_meta.python_orm.relationship.imports.markerless."
                    f"create:{operation.operation_key}"
                ),
                byte_start=byte_start,
                byte_end=byte_start,
                before_text="",
                replacement_text="".join(replacement_parts),
                field_name="relationship_runtime_imports",
                field_path="__imports__.relationship_runtime",
            ),
        ]
        if type_checking_replacement is not None:
            replacements.append(type_checking_replacement)
        return tuple(replacements)

    if not has_uuid_import and not has_field_import:
        standard_lines = []
        if type_checking_replacement is not None and not has_type_checking_import:
            standard_lines.append("from typing import TYPE_CHECKING\n")
        standard_lines.append("from uuid import UUID\n")
        replacement_text = (
            "# Standard\n"
            f"{''.join(standard_lines)}"
            "\n"
            "# Third-party\n"
            "from pydantic import Field\n"
            "\n"
        )
        byte_start = _byte_offset_for_char_index(source_text, orm_marker_index)
        replacements = [
            _PythonOrmRelationshipTextSpanReplacement(
                replacement_key=(
                    "aware_meta.python_orm.relationship.imports."
                    f"create:{operation.operation_key}"
                ),
                byte_start=byte_start,
                byte_end=byte_start,
                before_text="",
                replacement_text=replacement_text,
                field_name="relationship_runtime_imports",
                field_path="__imports__.relationship_runtime",
            ),
        ]
        if type_checking_replacement is not None:
            replacements.append(type_checking_replacement)
        return tuple(replacements)

    if not has_uuid_import:
        third_party_marker_index = source_text.find("# Third-party\n")
        if third_party_marker_index < 0:
            return None
        standard_lines = []
        if type_checking_replacement is not None and not has_type_checking_import:
            standard_lines.append("from typing import TYPE_CHECKING\n")
        standard_lines.append("from uuid import UUID\n")
        byte_start = _byte_offset_for_char_index(source_text, third_party_marker_index)
        replacements = [
            _PythonOrmRelationshipTextSpanReplacement(
                replacement_key=(
                    "aware_meta.python_orm.relationship.imports.uuid."
                    f"create:{operation.operation_key}"
                ),
                byte_start=byte_start,
                byte_end=byte_start,
                before_text="",
                replacement_text=f"# Standard\n{''.join(standard_lines)}\n",
                field_name="relationship_runtime_imports",
                field_path="__imports__.uuid",
            ),
        ]
        if type_checking_replacement is not None:
            replacements.append(type_checking_replacement)
        return tuple(replacements)

    replacements: list[_PythonOrmRelationshipTextSpanReplacement] = []
    if type_checking_replacement is not None and not has_type_checking_import:
        import_line_replacement = (
            _python_relationship_type_checking_import_line_replacement(
                source_text=source_text,
                operation=operation,
            )
        )
        if import_line_replacement is None:
            return None
        replacements.append(import_line_replacement)
    if not has_field_import:
        byte_start = _byte_offset_for_char_index(source_text, orm_marker_index)
        replacements.append(
            _PythonOrmRelationshipTextSpanReplacement(
                replacement_key=(
                    "aware_meta.python_orm.relationship.imports.field."
                    f"create:{operation.operation_key}"
                ),
                byte_start=byte_start,
                byte_end=byte_start,
                before_text="",
                replacement_text="# Third-party\nfrom pydantic import Field\n\n",
                field_name="relationship_runtime_imports",
                field_path="__imports__.field",
            )
        )
    if type_checking_replacement is not None:
        replacements.append(type_checking_replacement)
    return tuple(replacements)


def _python_relationship_type_checking_import_replacement(
    *,
    source_text: str,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
) -> _PythonOrmRelationshipTextSpanReplacement | None:
    target_class_name = _target_class_name(operation=operation)
    target_module_name = _python_relationship_target_module_name(
        operation=operation,
        context=context,
    )
    if target_class_name is None or target_module_name is None:
        return None
    if (
        f"class {target_class_name}(" in source_text
        or f"class {target_class_name}:" in source_text
    ):
        return None
    import_line = f"    from {target_module_name} import {target_class_name}\n"
    if import_line.strip() in source_text:
        return None
    type_checking_block = f"if TYPE_CHECKING:\n{import_line}\n"
    if "from typing import TYPE_CHECKING\n" in source_text:
        byte_start = _python_type_checking_block_insert_offset(source_text=source_text)
        if byte_start is None:
            return None
        return _PythonOrmRelationshipTextSpanReplacement(
            replacement_key=(
                "aware_meta.python_orm.relationship.imports.type_checking."
                f"create:{operation.operation_key}"
            ),
            byte_start=byte_start,
            byte_end=byte_start,
            before_text="",
            replacement_text=type_checking_block,
            field_name="relationship_type_checking_import",
            field_path="__imports__.type_checking",
        )
    byte_start = _python_type_checking_block_insert_offset(source_text=source_text)
    if byte_start is None:
        return None
    return _PythonOrmRelationshipTextSpanReplacement(
        replacement_key=(
            "aware_meta.python_orm.relationship.imports.type_checking."
            f"create:{operation.operation_key}"
        ),
        byte_start=byte_start,
        byte_end=byte_start,
        before_text="",
        replacement_text=type_checking_block,
        field_name="relationship_type_checking_import",
        field_path="__imports__.type_checking",
    )


def _python_relationship_type_checking_import_line_replacement(
    *,
    source_text: str,
    operation: MetaProviderDeltaTypedOperation,
) -> _PythonOrmRelationshipTextSpanReplacement | None:
    standard_marker = "# Standard\n"
    standard_index = source_text.find(standard_marker)
    if standard_index >= 0:
        byte_start = _byte_offset_for_char_index(
            source_text,
            standard_index + len(standard_marker),
        )
        replacement_text = "from typing import TYPE_CHECKING\n"
    else:
        byte_start = _python_markerless_relationship_import_insert_offset(
            source_text=source_text,
        )
        if byte_start is None:
            return None
        replacement_text = "# Standard\nfrom typing import TYPE_CHECKING\n\n"
    return _PythonOrmRelationshipTextSpanReplacement(
        replacement_key=(
            "aware_meta.python_orm.relationship.imports.type_checking_import."
            f"create:{operation.operation_key}"
        ),
        byte_start=byte_start,
        byte_end=byte_start,
        before_text="",
        replacement_text=replacement_text,
        field_name="relationship_type_checking_import_line",
        field_path="__imports__.type_checking_import",
    )


def _python_relationship_target_module_name(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
) -> str | None:
    target_fqn = _target_class_fqn(operation=operation)
    sources_root = _normalized_path(context.sources_root)
    if target_fqn is None or sources_root is None:
        return None
    parts = [part for part in target_fqn.split(".") if part]
    if len(parts) < 2:
        return None
    module_parts = (*parts[1:-1], _python_snake_case(parts[-1]))
    return ".".join((sources_root, *module_parts))


def _target_class_fqn(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    current_signature = _relationship_signature(payload=operation.current)
    baseline_signature = _relationship_signature(payload=operation.baseline)
    return (
        optional_text(operation.current.get("target_class_fqn"))
        or optional_text(current_signature.get("target_class_fqn"))
        or optional_text(operation.baseline.get("target_class_fqn"))
        or optional_text(baseline_signature.get("target_class_fqn"))
    )


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


def _python_type_checking_block_insert_offset(*, source_text: str) -> int | None:
    marker = "if TYPE_CHECKING:\n"
    marker_index = source_text.find(marker)
    if marker_index >= 0:
        insert_index = marker_index + len(marker)
        return _byte_offset_for_char_index(source_text, insert_index)
    class_index = source_text.find("\n\nclass ")
    if class_index >= 0:
        return _byte_offset_for_char_index(source_text, class_index + 1)
    return None


def _python_markerless_relationship_import_insert_offset(
    *,
    source_text: str,
) -> int | None:
    future_import = "from __future__ import annotations\n"
    future_index = source_text.find(future_import)
    if future_index >= 0:
        insert_index = future_index + len(future_import)
        if source_text[insert_index : insert_index + 1] == "\n":
            insert_index += 1
        return _byte_offset_for_char_index(source_text, insert_index)
    import_index = source_text.find("import ")
    from_index = source_text.find("from ")
    candidates = tuple(
        index for index in (import_index, from_index) if index >= 0
    )
    if not candidates:
        return 0
    return _byte_offset_for_char_index(source_text, min(candidates))


def _python_relationship_unused_import_delete_replacements(
    *,
    source_text: str,
    preview_text: str,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[_PythonOrmRelationshipTextSpanReplacement, ...] | None:
    import_block = (
        "# Standard\n"
        "from uuid import UUID\n"
        "\n"
        "# Third-party\n"
        "from pydantic import Field\n"
        "\n"
    )
    preview_import_index = preview_text.find(import_block)
    if preview_import_index < 0:
        return ()
    preview_without_imports = (
        preview_text[:preview_import_index]
        + preview_text[preview_import_index + len(import_block) :]
    )
    if "UUID" in preview_without_imports or "Field(" in preview_without_imports:
        return ()

    source_import_index = source_text.find(import_block)
    if source_import_index < 0:
        return None
    byte_start = _byte_offset_for_char_index(source_text, source_import_index)
    byte_end = _byte_offset_for_char_index(
        source_text,
        source_import_index + len(import_block),
    )
    return (
        _PythonOrmRelationshipTextSpanReplacement(
            replacement_key=(
                "aware_meta.python_orm.relationship.imports."
                f"delete:{operation.operation_key}"
            ),
            byte_start=byte_start,
            byte_end=byte_end,
            before_text=import_block,
            replacement_text="",
            field_name="relationship_runtime_imports",
            field_path="__imports__.relationship_runtime",
        ),
    )


def _preview_text_span_replacements(
    *,
    source_text: str,
    replacements: tuple[tuple[int, int, str], ...],
) -> str:
    source_bytes = source_text.encode("utf-8")
    for byte_start, byte_end, replacement_text in sorted(replacements, reverse=True):
        source_bytes = (
            source_bytes[:byte_start]
            + replacement_text.encode("utf-8")
            + source_bytes[byte_end:]
        )
    return source_bytes.decode("utf-8")


def _guarded_delta_diagnostics(
    *,
    operation: MetaProviderDeltaTypedOperation,
    target: CodeGeneratedMaterializationTargetRef,
) -> tuple[str, ...]:
    diagnostics = [PYTHON_ORM_RELATIONSHIP_EVIDENCE_ONLY_DIAGNOSTIC]
    if target.relative_path is None:
        diagnostics.append(
            PYTHON_ORM_RELATIONSHIP_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC
        )
    if _python_relationship_field_text(operation=operation) is None:
        diagnostics.append(PYTHON_ORM_RELATIONSHIP_FIELD_TEXT_MISSING_DIAGNOSTIC)
    elif _relationship_structural_create_required(operation=operation):
        diagnostics.append(
            PYTHON_ORM_RELATIONSHIP_STRUCTURAL_CREATE_SPAN_MISSING_DIAGNOSTIC
        )
    elif _relationship_structural_delete_required(operation=operation):
        diagnostics.append(
            PYTHON_ORM_RELATIONSHIP_STRUCTURAL_DELETE_SPAN_MISSING_DIAGNOSTIC
        )
    else:
        diagnostics.append(PYTHON_ORM_RELATIONSHIP_FIELD_SPAN_MISSING_DIAGNOSTIC)
    return tuple(dict.fromkeys(diagnostics))


def _generated_source_state(
    *,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
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
    context: MetaLanguageGeneratedMaterializationDeltaContext,
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
        provider_key=PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=(
            PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
        ),
        target_language=context.target_language,
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        renderer_key=PYTHON_ORM_RELATIONSHIP_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        output_key=class_name,
        relative_path=_generated_relative_path(operation=operation, context=context),
        metadata=_json_object(
            {
                "source": "python_grammar.python_orm_relationship_target_ref",
                "operation_key": operation.operation_key,
                "class_fqn": class_fqn,
                "class_name": class_name,
                "relationship_key": relationship_key,
                "language_plugin_delta_renderer": (
                    PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
                ),
            }
        ),
    )


def _anchor_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
) -> CodeGeneratedRendererAnchorRef:
    class_name = _source_class_name(operation=operation)
    relationship_key = _relationship_key(operation=operation)
    anchor_path = ".".join(
        part for part in (class_name, relationship_key, "load_policy") if part
    )
    return CodeGeneratedRendererAnchorRef(
        anchor_key=PYTHON_ORM_RELATIONSHIP_ANCHOR_KEY,
        anchor_path=anchor_path,
        anchor_role="relationship_load_policy_field",
        renderer_key=PYTHON_ORM_RELATIONSHIP_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        target_language=context.target_language,
        section_type="attribute",
        segment_name="field_line",
        graph_selector=_json_object(
            {
                "provider_key": (
                    PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_PROVIDER_KEY
                ),
                "semantic_owner": (
                    PYTHON_ORM_RELATIONSHIP_GENERATED_MATERIALIZATION_SEMANTIC_OWNER
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
                "source": "python_grammar.python_orm_relationship_anchor",
                "operation_key": operation.operation_key,
                "semantic_key": operation.semantic_key,
                "language_plugin_delta_renderer": (
                    PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
                ),
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
    context: MetaLanguageGeneratedMaterializationDeltaContext,
) -> str | None:
    explicit_relative_path = _explicit_generated_relative_path(operation=operation)
    if explicit_relative_path is not None:
        return explicit_relative_path
    hinted_relative_path = context.relative_path_for_owner(
        _source_class_fqn(operation=operation)
    )
    if hinted_relative_path is not None:
        return hinted_relative_path
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


def _code_language(value: str | None) -> CodeLanguage:
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
    "PYTHON_ORM_RELATIONSHIP_ANCHOR_KEY",
    "PYTHON_ORM_RELATIONSHIP_RENDERER_KEY",
    "render_python_orm_relationship_generated_delta",
    "supports_python_orm_relationship_generated_delta",
]
