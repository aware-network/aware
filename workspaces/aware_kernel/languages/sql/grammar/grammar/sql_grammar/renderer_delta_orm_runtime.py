from __future__ import annotations

import re
from pathlib import Path
from hashlib import sha256
from typing import Mapping, cast
from uuid import UUID

from aware_code_service_dto.code.features.package_common import CodePackagePathRole
from aware_code_service_dto.code.features.package_delta import (
    CodePackageDelta,
    CodePackageDeltaAuthorityKind,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_meta.materialization.deltas.code_dto import (
    CodeGeneratedMaterializationActionBinding,
    CodeGeneratedMaterializationDeltaEntry,
    CodeGeneratedMaterializationDeltaMode,
    CodeGeneratedMaterializationDeltaRequest,
    CodeGeneratedMaterializationDeltaResult,
    CodeGeneratedMaterializationEventRef,
    CodeGeneratedMaterializationTargetRef,
    CodeGeneratedRendererDeltaOperation,
    CodeGeneratedRendererDeltaOperationKind,
    CodeLanguage,
)
from aware_meta.materialization.deltas.coercion import (
    mapping_value,
    optional_text,
)
from aware_meta.materialization.deltas.feature_contracts import (
    meta_provider_delta_world_change_event_key,
)
from aware_meta.materialization.deltas.language_renderer_contracts import (
    MetaLanguageGeneratedMaterializationDeltaContext,
    MetaLanguageGeneratedMaterializationDeltaRenderer,
    MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    MetaLanguageGeneratedMaterializationDeltaRenderResult,
    MetaLanguageGeneratedMaterializationTargetHint,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_types import JsonObject
from sql_grammar.layout_strategy import SQLLayoutStrategyNamespace
from sql_grammar.migrations.postgres_ddl import (
    render_add_column,
    render_add_not_null_column_if_table_empty,
    render_drop_column,
    render_drop_not_null,
    render_failfast_sql,
)
from sql_grammar.renderer_policy import SQLRenderPolicy
from sql_grammar.renderers.renderer import SQLRenderer, SqliteSQLRenderer


SQL_ORM_GENERATED_DELTA_RENDERER_NAME = "sql_orm_runtime"
SQL_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY = "aware_meta"
SQL_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER = "aware_meta.ocg"
SQL_ORM_GENERATED_MATERIALIZATION_PRODUCT_INTENT = "orm_runtime"
SQL_ORM_RENDERER_PROFILE = "orm_runtime"
SQL_ORM_MATERIALIZATION_SOURCE = "ontology_orm_models"
SQL_ORM_CLASS_RENDERER_KEY = "sql.orm.class.source_artifact"
SQL_ORM_ATTRIBUTE_MIGRATION_RENDERER_KEY = "sql.orm.attribute.migration"
SQL_ORM_CLASS_ARTIFACT_FAMILY = "ocg_language_materialization"
SQL_ORM_CLASS_ARTIFACT_ROLE = "sql_orm_source_artifact"
SQL_ORM_MIGRATION_ARTIFACT_ROLE = "sql_orm_migration"
SQL_ORM_SOURCE_ARTIFACT_PAYLOAD_KEY = "sql_orm_source_artifact"
SQL_ORM_SOURCE_RENDERER_PROFILE = "orm_models"
SQL_ORM_SOURCE_RENDERER_KIND = "sqlite"


class SqlOrmRuntimeGeneratedDeltaRenderer(MetaLanguageGeneratedMaterializationDeltaRenderer):
    renderer_key = SQL_ORM_GENERATED_DELTA_RENDERER_NAME
    renderer_profile = SQL_ORM_RENDERER_PROFILE
    materialization_source = SQL_ORM_MATERIALIZATION_SOURCE

    def supports_generated_materialization_delta(
        self,
        request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    ) -> bool:
        operation = request.operation
        if operation.ontology_subject_kind == "class":
            return operation.operation_family in {"create", "delete", "update"}
        if operation.ontology_subject_kind == "attribute":
            return operation.operation_family in {"create", "delete", "update"}
        return False

    def render_generated_materialization_delta(
        self,
        request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    ) -> MetaLanguageGeneratedMaterializationDeltaRenderResult:
        if not self.supports_generated_materialization_delta(request):
            return MetaLanguageGeneratedMaterializationDeltaRenderResult.unhandled(
                reason="sql_orm_runtime_generated_delta_operation_not_supported",
            )

        operation = request.operation
        context = _context_with_defaults(request.context)
        event_key = meta_provider_delta_world_change_event_key(operation=operation)
        if operation.ontology_subject_kind == "attribute":
            return _render_attribute_migration_delta(
                operation=operation,
                context=context,
                event_key=event_key,
            )

        target = _target_ref(operation=operation, context=context)
        content_text = _sql_source_artifact_text(
            operation=operation,
            context=context,
            target=target,
        )
        if content_text is None:
            return MetaLanguageGeneratedMaterializationDeltaRenderResult.unhandled(
                reason="sql_orm_runtime_generated_delta_missing_renderer_ready_payload",
            )
        package_delta = _package_delta(
            operation=operation,
            context=context,
            target=target,
            content_text=content_text,
        )
        delta_request = _delta_request(
            operation=operation,
            context=context,
            event_key=event_key,
            target=target,
        )
        result = _delta_result(
            operation=operation,
            context=context,
            event_key=event_key,
            target=target,
            content_text=content_text,
            package_delta=package_delta,
        )
        return MetaLanguageGeneratedMaterializationDeltaRenderResult.from_evidence(
            delta_request=delta_request,
            result=result,
            reason="sql_orm_runtime_source_artifact_generated_delta_rendered",
        )


def _context_with_defaults(
    context: MetaLanguageGeneratedMaterializationDeltaContext,
) -> MetaLanguageGeneratedMaterializationDeltaContext:
    sources_root = _normalized_path(context.sources_root) or "sql"
    return MetaLanguageGeneratedMaterializationDeltaContext(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=sources_root,
        target_language=context.target_language or "sql",
        renderer_profile=context.renderer_profile or SQL_ORM_RENDERER_PROFILE,
        materialization_source=(context.materialization_source or SQL_ORM_MATERIALIZATION_SOURCE),
        product_intent=(context.product_intent or SQL_ORM_GENERATED_MATERIALIZATION_PRODUCT_INTENT),
        artifact_family=context.artifact_family or SQL_ORM_CLASS_ARTIFACT_FAMILY,
        artifact_role=context.artifact_role or SQL_ORM_CLASS_ARTIFACT_ROLE,
        target_hints=context.target_hints,
    )


def _render_attribute_migration_delta(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    event_key: str,
) -> MetaLanguageGeneratedMaterializationDeltaRenderResult:
    migration = _attribute_migration_text(operation=operation)
    if migration is None:
        return MetaLanguageGeneratedMaterializationDeltaRenderResult.unhandled(
            reason="sql_orm_runtime_attribute_migration_payload_missing",
        )
    content_text, diagnostics = migration
    target = _attribute_migration_target_ref(operation=operation, context=context)
    package_delta = _attribute_migration_package_delta(
        operation=operation,
        context=context,
        target=target,
        content_text=content_text,
    )
    delta_request = _delta_request(
        operation=operation,
        context=context,
        event_key=event_key,
        target=target,
    )
    result = _attribute_migration_delta_result(
        operation=operation,
        context=context,
        event_key=event_key,
        target=target,
        content_text=content_text,
        package_delta=package_delta,
        diagnostics=diagnostics,
    )
    return MetaLanguageGeneratedMaterializationDeltaRenderResult.from_evidence(
        delta_request=delta_request,
        result=result,
        reason="sql_orm_runtime_attribute_migration_generated_delta_rendered",
    )


def _delta_request(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
) -> CodeGeneratedMaterializationDeltaRequest:
    return CodeGeneratedMaterializationDeltaRequest(
        provider_key=SQL_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=SQL_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
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
                action_key=("aware_meta.sql_orm.class.source_artifact." f"{operation.operation_key}"),
                event_key=event_key,
                target=target,
                policy_key="aware_meta.generated_materialization.class.sql_source",
                renderer_key=SQL_ORM_CLASS_RENDERER_KEY,
                metadata=_json_object(
                    {
                        "renderer_profile": context.renderer_profile,
                        "materialization_source": context.materialization_source,
                    }
                ),
            )
        ],
        targets=[target],
        metadata=_json_object({"delta_form": "source_artifact"}),
    )


def _attribute_migration_package_delta(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    target: CodeGeneratedMaterializationTargetRef,
    content_text: str,
) -> CodePackageDelta:
    return CodePackageDelta(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        authority=CodePackageDeltaAuthorityKind.semantic_materialization,
        authority_kind=CodePackageDeltaAuthorityKind.semantic_materialization.value,
        paths=[
            CodePackageDeltaPath(
                relative_path=target.relative_path or _attribute_migration_relative_path(operation=operation),
                kind=CodePackageDeltaKind.create,
                content_text=content_text,
                after_hash=_digest(content_text),
                language=CodeLanguage.sql,
                is_structural=True,
                path_role=CodePackagePathRole.generated_code,
                metadata=_json_object(
                    {
                        "semantic_key": operation.semantic_key,
                        "renderer_key": SQL_ORM_ATTRIBUTE_MIGRATION_RENDERER_KEY,
                        "delta_form": "migration_artifact",
                        "artifact_role": SQL_ORM_MIGRATION_ARTIFACT_ROLE,
                    }
                ),
            )
        ],
        metadata=_json_object(
            {
                "provider_key": SQL_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
                "renderer_profile": context.renderer_profile,
                "materialization_source": context.materialization_source,
                "delta_form": "migration_artifact",
                "artifact_role": SQL_ORM_MIGRATION_ARTIFACT_ROLE,
            }
        ),
    )


def _delta_result(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
    content_text: str,
    package_delta: CodePackageDelta,
) -> CodeGeneratedMaterializationDeltaResult:
    content_hash = _digest(content_text)
    renderer_operation = CodeGeneratedRendererDeltaOperation(
        operation_key=f"sql_orm_source_artifact:{operation.operation_key}",
        kind=CodeGeneratedRendererDeltaOperationKind.replace_section,
        target=target,
        renderer_key=SQL_ORM_CLASS_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        after_hash=content_hash,
        content_text=content_text,
        replacement_text=content_text,
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        diagnostics=[
            "sql_orm_source_artifact_render_equivalent",
            "sql_orm_source_artifact_delta_first_not_migration",
        ],
        metadata=_json_object(
            {
                "delta_form": "source_artifact",
                "future_artifact_role": "migration",
            }
        ),
    )
    entry = CodeGeneratedMaterializationDeltaEntry(
        entry_key=f"sql_orm_source_artifact:{operation.operation_key}",
        mode=CodeGeneratedMaterializationDeltaMode.package_delta_ready,
        target=target,
        package_delta=package_delta,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        artifact_key=target.target_key,
        relative_path=target.relative_path,
        after_hash=content_hash,
        renderer_operations=[renderer_operation],
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        metadata=_json_object({"delta_form": "source_artifact"}),
    )
    return CodeGeneratedMaterializationDeltaResult(
        provider_key=SQL_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=SQL_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        available=True,
        mode=CodeGeneratedMaterializationDeltaMode.package_delta_ready,
        entries=[entry],
        diagnostics=[
            "sql_orm_source_artifact_render_equivalent",
            "sql_orm_source_artifact_delta_first_not_migration",
        ],
        fingerprint=content_hash,
        metadata=_json_object({"delta_form": "source_artifact"}),
    )


def _attribute_migration_delta_result(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
    content_text: str,
    package_delta: CodePackageDelta,
    diagnostics: tuple[str, ...],
) -> CodeGeneratedMaterializationDeltaResult:
    content_hash = _digest(content_text)
    renderer_operation = CodeGeneratedRendererDeltaOperation(
        operation_key=f"sql_orm_attribute_migration:{operation.operation_key}",
        kind=CodeGeneratedRendererDeltaOperationKind.replace_section,
        target=target,
        renderer_key=SQL_ORM_ATTRIBUTE_MIGRATION_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        after_hash=content_hash,
        content_text=content_text,
        replacement_text=content_text,
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        diagnostics=list(diagnostics),
        metadata=_json_object(
            {
                "delta_form": "migration_artifact",
                "artifact_role": SQL_ORM_MIGRATION_ARTIFACT_ROLE,
            }
        ),
    )
    entry = CodeGeneratedMaterializationDeltaEntry(
        entry_key=f"sql_orm_attribute_migration:{operation.operation_key}",
        mode=CodeGeneratedMaterializationDeltaMode.package_delta_ready,
        target=target,
        package_delta=package_delta,
        artifact_family=context.artifact_family,
        artifact_role=SQL_ORM_MIGRATION_ARTIFACT_ROLE,
        artifact_key=target.target_key,
        relative_path=target.relative_path,
        after_hash=content_hash,
        renderer_operations=[renderer_operation],
        event_refs=[event_key],
        semantic_keys=[operation.semantic_key],
        metadata=_json_object(
            {
                "delta_form": "migration_artifact",
                "artifact_role": SQL_ORM_MIGRATION_ARTIFACT_ROLE,
            }
        ),
    )
    return CodeGeneratedMaterializationDeltaResult(
        provider_key=SQL_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=SQL_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        available=True,
        mode=CodeGeneratedMaterializationDeltaMode.package_delta_ready,
        entries=[entry],
        diagnostics=list(diagnostics),
        fingerprint=content_hash,
        metadata=_json_object(
            {
                "delta_form": "migration_artifact",
                "artifact_role": SQL_ORM_MIGRATION_ARTIFACT_ROLE,
            }
        ),
    )


def _target_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
) -> CodeGeneratedMaterializationTargetRef:
    owner_key = _owner_key(operation)
    hint = _target_hint(context=context, owner_key=owner_key)
    relative_path = (
        hint.relative_path
        if hint is not None and hint.relative_path is not None
        else _relative_path(operation=operation, context=context)
    )
    return CodeGeneratedMaterializationTargetRef(
        target_key=(
            hint.target_key
            if hint is not None and hint.target_key is not None
            else f"sql_orm:{owner_key or operation.semantic_key}"
        ),
        provider_key=SQL_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=SQL_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        target_language=context.target_language,
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        renderer_key=SQL_ORM_CLASS_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        artifact_family=context.artifact_family,
        artifact_role=context.artifact_role,
        output_key=hint.output_key if hint is not None else None,
        relative_path=relative_path,
        metadata=_json_object(
            {
                "owner_key": owner_key,
                "descriptor_key": hint.descriptor_key if hint is not None else None,
                "capability_key": hint.capability_key if hint is not None else None,
                "delta_form": "source_artifact",
            }
        ),
    )


def _attribute_migration_target_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
) -> CodeGeneratedMaterializationTargetRef:
    relative_path = _attribute_migration_relative_path(operation=operation)
    return CodeGeneratedMaterializationTargetRef(
        target_key=f"sql_orm_migration:{operation.operation_key}",
        provider_key=SQL_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=SQL_ORM_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        target_language=context.target_language,
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        renderer_key=SQL_ORM_ATTRIBUTE_MIGRATION_RENDERER_KEY,
        renderer_profile=context.renderer_profile,
        materialization_source=context.materialization_source,
        artifact_family=context.artifact_family,
        artifact_role=SQL_ORM_MIGRATION_ARTIFACT_ROLE,
        output_key=_attribute_name(operation),
        relative_path=relative_path,
        metadata=_json_object(
            {
                "owner_key": _owner_key(operation),
                "delta_form": "migration_artifact",
                "artifact_role": SQL_ORM_MIGRATION_ARTIFACT_ROLE,
            }
        ),
    )


def _package_delta(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    target: CodeGeneratedMaterializationTargetRef,
    content_text: str,
) -> CodePackageDelta:
    return CodePackageDelta(
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        authority=CodePackageDeltaAuthorityKind.semantic_materialization,
        authority_kind=CodePackageDeltaAuthorityKind.semantic_materialization.value,
        paths=[
            CodePackageDeltaPath(
                relative_path=target.relative_path
                or _relative_path(
                    operation=operation,
                    context=context,
                ),
                kind=(
                    CodePackageDeltaKind.delete
                    if operation.operation_family == "delete"
                    else (
                        CodePackageDeltaKind.create
                        if operation.operation_family == "create"
                        else CodePackageDeltaKind.update
                    )
                ),
                content_text=(None if operation.operation_family == "delete" else content_text),
                after_hash=(None if operation.operation_family == "delete" else _digest(content_text)),
                language=CodeLanguage.sql,
                is_structural=True,
                path_role=CodePackagePathRole.generated_code,
                metadata=_json_object(
                    {
                        "semantic_key": operation.semantic_key,
                        "renderer_key": SQL_ORM_CLASS_RENDERER_KEY,
                        "delta_form": "source_artifact",
                    }
                ),
            )
        ],
        metadata=_json_object(
            {
                "provider_key": SQL_ORM_GENERATED_MATERIALIZATION_PROVIDER_KEY,
                "renderer_profile": context.renderer_profile,
                "materialization_source": context.materialization_source,
                "delta_form": "source_artifact",
            }
        ),
    )


def _sql_source_artifact_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    target: CodeGeneratedMaterializationTargetRef,
) -> str | None:
    if operation.operation_family == "delete":
        table_name = _table_name(operation)
        return f"DROP TABLE IF EXISTS {table_name};\n"

    payload = _sql_source_artifact_payload(operation=operation)
    if payload is None:
        return None

    renderer = _sql_source_artifact_renderer(
        payload=payload,
        context=context,
    )
    language_graph = _language_graph_from_payload(payload)
    if language_graph is not None:
        renderer.layout_strategy.bind_graph(language_graph)
        renderer.bind_object_config_graph(language_graph)
        class_lookup = _class_lookup_from_graph(language_graph)
        source_container = _source_container_from_graph(
            graph=language_graph,
            renderer=renderer,
            target=target,
            payload=payload,
        )
        if source_container is not None:
            enums, classes = source_container
            return _non_empty_source_artifact(
                renderer.render_source_artifact(
                    enums=enums,
                    classes=classes,
                    class_lookup=class_lookup,
                )
            )
        cls = _class_from_graph(
            operation=operation,
            class_lookup=class_lookup,
        )
        if cls is None:
            return None
        return _non_empty_source_artifact(
            renderer.render_class_source_artifact(
                cls,
                class_lookup=class_lookup,
            )
        )

    cls = _class_config_from_payload(payload)
    if cls is None:
        return None
    class_lookup = _class_lookup_from_payload(payload)
    class_lookup.setdefault(cls.id, cls)
    return _non_empty_source_artifact(
        renderer.render_class_source_artifact(
            cls,
            class_lookup=class_lookup,
        )
    )


def _non_empty_source_artifact(source_text: str) -> str | None:
    if not source_text.strip():
        return None
    return source_text


def _attribute_migration_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[str, tuple[str, ...]] | None:
    table_name = _table_name(operation)
    column_name = _attribute_name(operation)
    if table_name is None or column_name is None:
        return None
    if operation.operation_family == "create":
        current_signature = _current_attribute_signature(operation)
        sql_type = _sql_type_from_attribute_signature(current_signature)
        if sql_type is None:
            return (
                render_failfast_sql(
                    reasons=(f"unsupported SQL attribute create migration: {table_name}.{column_name}",),
                ),
                (
                    "sql_orm_migration_artifact_ready",
                    "sql_orm_migration_unsupported_attribute_type",
                    "sql_orm_migration_failfast",
                ),
            )
        if _signature_is_required(current_signature):
            return (
                render_add_not_null_column_if_table_empty(
                    table_name=table_name,
                    column_name=column_name,
                    sql_type=sql_type,
                ),
                (
                    "sql_orm_migration_artifact_ready",
                    "sql_orm_migration_attribute_create_add_column",
                    "sql_orm_migration_required_add_empty_table_guard",
                ),
            )
        return (
            render_add_column(
                table_name=table_name,
                column_name=column_name,
                sql_type=sql_type,
            )
            + "\n",
            (
                "sql_orm_migration_artifact_ready",
                "sql_orm_migration_attribute_create_add_column",
            ),
        )

    if operation.operation_family == "delete":
        return (
            render_drop_column(table_name=table_name, column_name=column_name) + "\n",
            (
                "sql_orm_migration_artifact_ready",
                "sql_orm_migration_attribute_delete_drop_column",
            ),
        )

    if operation.operation_family == "update":
        baseline_signature = _baseline_attribute_signature(operation)
        current_signature = _current_attribute_signature(operation)
        baseline_type = _sql_type_from_attribute_signature(baseline_signature)
        current_type = _sql_type_from_attribute_signature(current_signature)
        baseline_required = _signature_is_required(baseline_signature)
        current_required = _signature_is_required(current_signature)
        if (
            baseline_type is not None
            and current_type is not None
            and baseline_type == current_type
            and baseline_required
            and not current_required
        ):
            return (
                render_drop_not_null(table_name=table_name, column_name=column_name) + "\n",
                (
                    "sql_orm_migration_artifact_ready",
                    "sql_orm_migration_attribute_update_drop_not_null",
                ),
            )
        return (
            render_failfast_sql(
                reasons=("unsupported SQL attribute update migration: " f"{table_name}.{column_name}",),
            ),
            (
                "sql_orm_migration_artifact_ready",
                "sql_orm_migration_unsupported_attribute_update",
                "sql_orm_migration_failfast",
            ),
        )
    return None


def _attribute_migration_relative_path(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str:
    safe_operation = re.sub(r"[^a-zA-Z0-9_.-]+", "_", operation.operation_key).strip("_.-")
    if not safe_operation:
        safe_operation = _digest(operation.operation_key).split(":", 1)[1][:12]
    return f"migrations/{safe_operation}.sql"


def _attribute_name(operation: MetaProviderDeltaTypedOperation) -> str | None:
    for payload in _operation_payloads(operation):
        attribute_name = optional_text(payload.get("attribute_name")) or optional_text(payload.get("name"))
        if attribute_name is not None:
            return attribute_name
    return _attribute_name_from_key(operation.semantic_key)


def _attribute_name_from_key(semantic_key: str) -> str | None:
    marker = "/attribute:"
    if marker not in semantic_key:
        return None
    tail = semantic_key.split(marker, 1)[1].split("/", 1)[0]
    return tail or None


def _current_attribute_signature(
    operation: MetaProviderDeltaTypedOperation,
) -> Mapping[str, object]:
    for payload in (mapping_value(operation.current), mapping_value(operation.extra)):
        signature = mapping_value(payload.get("attribute_signature"))
        if signature:
            return signature
    return {}


def _baseline_attribute_signature(
    operation: MetaProviderDeltaTypedOperation,
) -> Mapping[str, object]:
    baseline = mapping_value(operation.baseline)
    for payload in (mapping_value(baseline.get("object")), baseline):
        signature = mapping_value(payload.get("attribute_signature"))
        if signature:
            return signature
    return {}


def _signature_is_required(signature: Mapping[str, object]) -> bool:
    return bool(signature.get("is_required"))


def _sql_type_from_attribute_signature(
    signature: Mapping[str, object],
) -> str | None:
    descriptor = mapping_value(signature.get("type_descriptor"))
    if descriptor.get("kind") != "primitive":
        return None
    primitive = optional_text(descriptor.get("primitive_base_type"))
    if primitive is None:
        return None
    primitive_key = primitive.lower()
    return {
        "string": "TEXT",
        "str": "TEXT",
        "integer": "INTEGER",
        "int": "INTEGER",
        "number": "DOUBLE PRECISION",
        "float": "DOUBLE PRECISION",
        "boolean": "BOOLEAN",
        "bool": "BOOLEAN",
        "uuid": "UUID",
        "datetime": "TIMESTAMPTZ",
        "timestamp": "TIMESTAMPTZ",
        "date": "DATE",
    }.get(primitive_key)


def _source_container_from_graph(
    *,
    graph: ObjectConfigGraph,
    renderer: SQLRenderer,
    target: CodeGeneratedMaterializationTargetRef,
    payload: Mapping[str, object],
) -> tuple[tuple[EnumConfig, ...], tuple[ClassConfig, ...]] | None:
    target_path = _target_source_relative_path(target=target, payload=payload)
    if target_path is None:
        return None

    enums: list[EnumConfig] = []
    classes: list[ClassConfig] = []
    layout = renderer.layout_strategy
    for node in graph.object_config_graph_nodes:
        if node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
            enum_path = layout.get_enum_file_path(node.enum_config)
            if _same_relative_path(enum_path, target_path):
                enums.append(node.enum_config)
            continue
        if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
            class_path = layout.get_class_file_path(node.class_config)
            if _same_relative_path(class_path, target_path):
                classes.append(node.class_config)

    if not enums and not classes:
        return None
    return (tuple(enums), tuple(classes))


def _target_source_relative_path(
    *,
    target: CodeGeneratedMaterializationTargetRef,
    payload: Mapping[str, object],
) -> Path | None:
    value = optional_text(payload.get("relative_path")) or target.relative_path
    if not value:
        return None
    return Path(value)


def _same_relative_path(left: Path, right: Path) -> bool:
    def normalize(path: Path) -> str:
        return path.as_posix().lstrip("./")

    return normalize(left) == normalize(right)


def _sql_source_artifact_payload(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> Mapping[str, object] | None:
    for source in (
        operation.current,
        operation.extra,
        operation.baseline,
        mapping_value(operation.current.get("payload")),
    ):
        value = source.get(SQL_ORM_SOURCE_ARTIFACT_PAYLOAD_KEY)
        if isinstance(value, Mapping):
            return value
    return None


def _sql_source_artifact_renderer(
    *,
    payload: Mapping[str, object],
    context: MetaLanguageGeneratedMaterializationDeltaContext,
) -> SQLRenderer:
    base_dir = Path(context.package_root or ".")
    layout_strategy = SQLLayoutStrategyNamespace(base_dir)
    renderer_kind = (
        optional_text(payload.get("renderer_kind"))
        or optional_text(payload.get("source_renderer_kind"))
        or SQL_ORM_SOURCE_RENDERER_KIND
    )
    if renderer_kind == "sqlite":
        renderer: SQLRenderer = SqliteSQLRenderer(layout_strategy=layout_strategy)
    else:
        renderer = SQLRenderer(layout_strategy=layout_strategy)

    renderer_profile = (
        optional_text(payload.get("source_renderer_profile"))
        or optional_text(payload.get("renderer_profile"))
        or SQL_ORM_SOURCE_RENDERER_PROFILE
    )
    if renderer_profile == SQL_ORM_SOURCE_RENDERER_PROFILE:
        renderer.set_policy(SQLRenderPolicy.orm_models_default())
    else:
        renderer.set_policy(SQLRenderPolicy.projection_default())
    return renderer


def _language_graph_from_payload(
    payload: Mapping[str, object],
) -> ObjectConfigGraph | None:
    value = payload.get("language_graph") or payload.get("object_config_graph")
    if not isinstance(value, Mapping):
        return None
    return ObjectConfigGraph.model_validate(value)


def _class_config_from_payload(
    payload: Mapping[str, object],
) -> ClassConfig | None:
    value = payload.get("class_config") or payload.get("class")
    if not isinstance(value, Mapping):
        return None
    return ClassConfig.model_validate(value)


def _class_lookup_from_payload(
    payload: Mapping[str, object],
) -> dict[UUID, ClassConfig]:
    lookup: dict[UUID, ClassConfig] = {}
    classes = payload.get("class_lookup") or payload.get("classes")
    if not isinstance(classes, tuple | list):
        return lookup
    for item in classes:
        if not isinstance(item, Mapping):
            continue
        cls = ClassConfig.model_validate(item)
        lookup[cls.id] = cls
    return lookup


def _class_lookup_from_graph(graph: ObjectConfigGraph) -> dict[UUID, ClassConfig]:
    lookup: dict[UUID, ClassConfig] = {}
    for node in graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        lookup[node.class_config.id] = node.class_config
    return lookup


def _class_from_graph(
    *,
    operation: MetaProviderDeltaTypedOperation,
    class_lookup: Mapping[UUID, ClassConfig],
) -> ClassConfig | None:
    class_name = _class_name(operation)
    class_fqn = _owner_key(operation)
    candidates = tuple(cls for cls in class_lookup.values() if cls.value_mode == ClassValueMode.graph_ref)
    for cls in candidates:
        if class_name is not None and cls.name == class_name:
            return cls
    if class_fqn is not None:
        tail = class_fqn.rsplit(".", 1)[-1]
        for cls in candidates:
            if cls.name == tail:
                return cls
    if len(candidates) == 1:
        return candidates[0]
    return None


def _target_hint(
    *,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
    owner_key: str | None,
) -> MetaLanguageGeneratedMaterializationTargetHint | None:
    for hint in context.target_hints:
        if hint.target_language and hint.target_language != "sql":
            continue
        if hint.renderer_profile and hint.renderer_profile != SQL_ORM_RENDERER_PROFILE:
            continue
        if hint.materialization_source and hint.materialization_source != SQL_ORM_MATERIALIZATION_SOURCE:
            continue
        if owner_key and hint.owner_key and hint.owner_key != owner_key:
            continue
        return hint
    return None


def _relative_path(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaLanguageGeneratedMaterializationDeltaContext,
) -> str:
    sources_root = _normalized_path(context.sources_root)
    source_ref = next(iter(operation.source_refs), None)
    if source_ref:
        source_path = _normalized_path(source_ref)
        if source_path and source_path.endswith(".aware"):
            path = f"{source_path[:-len('.aware')]}.sql"
            if sources_root and not path.startswith(f"{sources_root}/"):
                return f"{sources_root}/{path}"
            return path
    file_name = f"{_snake_case(_class_name(operation) or 'ontology')}.sql"
    return f"{sources_root}/{file_name}" if sources_root else file_name


def _owner_key(operation: MetaProviderDeltaTypedOperation) -> str | None:
    for payload in _operation_payloads(operation):
        owner_key = optional_text(payload.get("owner_key"))
        if owner_key is not None:
            return owner_key
        class_fqn = optional_text(payload.get("class_fqn"))
        if class_fqn is not None:
            return class_fqn
    return _semantic_owner_from_key(operation.semantic_key)


def _table_name(operation: MetaProviderDeltaTypedOperation) -> str:
    return _snake_case(_class_name(operation) or "aware_object")


def _class_name(operation: MetaProviderDeltaTypedOperation) -> str | None:
    for payload in _operation_payloads(operation):
        class_name = (
            optional_text(payload.get("class_name"))
            or optional_text(payload.get("name"))
            or optional_text(payload.get("entity_name"))
        )
        if class_name is not None:
            return class_name
    owner = _owner_key(operation)
    if owner is not None:
        tail = owner.rsplit(".", 1)[-1]
        if tail:
            return tail
    return None


def _operation_payloads(
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[Mapping[str, object], ...]:
    baseline = mapping_value(operation.baseline)
    current = mapping_value(operation.current)
    payloads = (
        current,
        mapping_value(current.get("payload")),
        mapping_value(baseline.get("object")),
        baseline,
        mapping_value(operation.semantic_change_projection or {}),
        mapping_value(operation.extra),
    )
    return tuple(payload for payload in payloads if payload)


def _semantic_owner_from_key(semantic_key: str) -> str | None:
    marker = "/node:"
    if marker not in semantic_key:
        return None
    tail = semantic_key.split(marker, 1)[1].split("/", 1)[0]
    return tail or None


def _normalized_path(value: str | None) -> str | None:
    text = optional_text(value)
    if text is None:
        return None
    parts = [part for part in text.replace("\\", "/").split("/") if part and part != "."]
    return "/".join(parts) or None


def _snake_case(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z]+", "_", value).strip("_")
    if not cleaned:
        return "aware_object"
    first_pass = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cleaned)
    second_pass = re.sub("([a-z0-9])([A-Z])", r"\1_\2", first_pass)
    return second_pass.lower().strip("_") or "aware_object"


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _sorted_unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({item for item in values if item}))


def _json_object(value: Mapping[str, object]) -> JsonObject:
    return cast(JsonObject, {key: item for key, item in value.items() if item is not None})


__all__ = [
    "SQL_ORM_GENERATED_DELTA_RENDERER_NAME",
    "SQL_ORM_MATERIALIZATION_SOURCE",
    "SQL_ORM_RENDERER_PROFILE",
    "SqlOrmRuntimeGeneratedDeltaRenderer",
]
