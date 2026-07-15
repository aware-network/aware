from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from aware_meta.graph.projection.deltas.typed_operations import (
    OBJECT_PROJECTION_GRAPH_BINDING_SUBJECT_KIND,
    OBJECT_PROJECTION_GRAPH_DECLARATION_SUBJECT_KIND,
)
from aware_meta.materialization.deltas.code_dto import (
    CodeGeneratedMaterializationActionBinding,
    CodeGeneratedMaterializationDeltaMode,
    CodeGeneratedMaterializationDeltaRequest,
    CodeGeneratedMaterializationDeltaResult,
    CodeGeneratedMaterializationEventRef,
    CodeGeneratedMaterializationSkippedTarget,
    CodeGeneratedMaterializationTargetRef,
)
from aware_meta.materialization.deltas.coercion import optional_text
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaGeneratedMaterializationContext,
    MetaProviderDeltaGeneratedMaterializationFeatureResult,
    meta_provider_delta_world_change_event_key,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_types import JsonObject


OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_FEATURE_KEY = (
    "object_projection_graph"
)
OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_PROVIDER_KEY = "aware_meta"
OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER = (
    "aware_meta.ocg.opg.projection_declaration"
)
OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_POLICY_KEY = (
    "aware_meta.opg.projection_declaration.graph_runtime_state"
)
OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_REASON = (
    "meta_opg_projection_declaration_generated_materialization_not_required"
)
_SUPPORTED_SUBJECT_KINDS = frozenset(
    (
        OBJECT_PROJECTION_GRAPH_DECLARATION_SUBJECT_KIND,
        OBJECT_PROJECTION_GRAPH_BINDING_SUBJECT_KIND,
    )
)


def generated_materialization_feature_results_from_opg_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> tuple[MetaProviderDeltaGeneratedMaterializationFeatureResult, ...]:
    event_key = meta_provider_delta_world_change_event_key(operation=operation)
    if operation.ontology_subject_kind not in _SUPPORTED_SUBJECT_KINDS:
        return (
            MetaProviderDeltaGeneratedMaterializationFeatureResult.skipped(
                feature_key=OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_FEATURE_KEY,
                operation=operation,
                reason="meta_opg_generated_materialization_subject_not_supported",
                event_refs=(event_key,),
            ),
        )
    if operation.operation_family != "create":
        return (
            MetaProviderDeltaGeneratedMaterializationFeatureResult.skipped(
                feature_key=OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_FEATURE_KEY,
                operation=operation,
                reason="meta_opg_projection_declaration_generated_materialization_family_not_required",
                event_refs=(event_key,),
            ),
        )

    target = _target_ref(operation=operation, context=context)
    delta_request = _delta_request(
        operation=operation,
        context=context,
        event_key=event_key,
        target=target,
    )
    result = _not_required_result(
        operation=operation,
        context=context,
        event_key=event_key,
        target=target,
    )
    return (
        MetaProviderDeltaGeneratedMaterializationFeatureResult.from_evidence(
            feature_key=OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_FEATURE_KEY,
            operation=operation,
            delta_request=delta_request,
            result=result,
            reason="meta_opg_projection_declaration_generated_materialization_evidence_ready",
        ),
    )


def _delta_request(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaGeneratedMaterializationContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
) -> CodeGeneratedMaterializationDeltaRequest:
    return CodeGeneratedMaterializationDeltaRequest(
        provider_key=OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        product_intent="graph_runtime_projection",
        events=[
            CodeGeneratedMaterializationEventRef(
                event_key=event_key,
                semantic_key=operation.semantic_key,
                verb=operation.operation_family,
                subject_type=operation.ontology_subject_kind,
                source="aware_meta.provider_delta.semantic_world_change",
                source_refs=list(sorted(set(operation.source_refs))),
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
                    "aware_meta.opg.projection_declaration.generated_materialization."
                    f"{operation.operation_key}"
                ),
                event_key=event_key,
                target=target,
                policy_key=OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_POLICY_KEY,
                renderer_key="aware_meta.opg.projection_declaration.graph_runtime_state",
                metadata=_json_object(
                    {
                        "source": (
                            "aware_meta.graph.projection.deltas.generated_materialization"
                        ),
                        "operation_key": operation.operation_key,
                    }
                ),
            )
        ],
        targets=[target],
        metadata=_json_object(
            {
                "source": "aware_meta.opg_projection_declaration_generated_materialization_request",
                "reason": OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_REASON,
            }
        ),
    )


def _not_required_result(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaGeneratedMaterializationContext,
    event_key: str,
    target: CodeGeneratedMaterializationTargetRef,
) -> CodeGeneratedMaterializationDeltaResult:
    return CodeGeneratedMaterializationDeltaResult(
        provider_key=OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        available=True,
        mode=CodeGeneratedMaterializationDeltaMode.not_required,
        skipped_targets=[
            CodeGeneratedMaterializationSkippedTarget(
                target=target,
                reason=OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_REASON,
                event_refs=[event_key],
                metadata=_json_object(
                    {
                        "operation_key": operation.operation_key,
                        "provider_operation_type": operation.provider_operation_type,
                    }
                ),
            )
        ],
        metadata=_json_object(
            {
                "source": "aware_meta.opg_projection_declaration_generated_materialization_result",
                "reason": OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_REASON,
                "target_language": context.target_language,
                "target_language_plugin_id": context.target_language_plugin_id,
            }
        ),
    )


def _target_ref(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> CodeGeneratedMaterializationTargetRef:
    target_key = ".".join(
        part
        for part in (
            context.package_name,
            "opg_projection_declaration",
            operation.semantic_key,
        )
        if part
    )
    return CodeGeneratedMaterializationTargetRef(
        target_key=target_key,
        provider_key=OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        semantic_owner=OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_SEMANTIC_OWNER,
        target_language=context.target_language,
        package_name=context.package_name,
        package_root=context.package_root,
        sources_root=context.sources_root,
        renderer_key="aware_meta.opg.projection_declaration.graph_runtime_state",
        renderer_profile=(
            context.generated_materialization_target_profile.renderer_profile
            if context.generated_materialization_target_profile is not None
            else None
        ),
        materialization_source="graph_runtime_projection",
        artifact_family="object_projection_graph",
        artifact_role=operation.ontology_subject_kind,
        output_key=optional_text(operation.current.get("name"))
        or optional_text(operation.current.get("class_fqn"))
        or operation.semantic_key,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.opg_projection_declaration_generated_materialization_target"
                ),
                "operation_key": operation.operation_key,
                "object_kind": operation.ontology_subject_kind,
            }
        ),
    )


def _json_object(payload: Mapping[str, object | None]) -> JsonObject:
    return JsonObject(cast(Any, {key: value for key, value in payload.items()}))


__all__ = [
    "OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_REASON",
    "generated_materialization_feature_results_from_opg_typed_operation",
]
