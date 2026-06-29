from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from aware_meta.materialization.deltas.execution import (
    _provider_delta_oig_commit_receipt,
)
from aware_meta.materialization.deltas.ontology_execution import (
    build_provider_delta_ontology_execution_plan,
)
from aware_meta.runtime.invocation_engine import MetaGraphCallTarget

from ..fixtures import provider_delta_uuid
from .fixtures import (
    ProviderDeltaRuntimeExecutionContext,
    build_provider_delta_runtime_execution_context,
)


async def _commit_relationship_operation(
    *,
    ctx: ProviderDeltaRuntimeExecutionContext,
    typed_operation_plan: dict[str, object],
) -> dict[str, object]:
    ontology_execution_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    assert ontology_execution_plan["status"] == "ontology_execution_plan_ready"
    return await _provider_delta_oig_commit_receipt(
        request=ctx.request,
        baseline_dirty_preflight=ctx.baseline_dirty_preflight,
        provider_delta_mutation_plan={},
        provider_delta_ontology_execution_plan=ontology_execution_plan,
        provider_delta_execute_flag_preflight={
            "status": "execute_flag_preflight_ready",
        },
    )


def _relationship_anchor(
    *,
    source_class_semantic_key: str,
    source_class_config_id: object,
) -> dict[str, object]:
    return {
        "operation_key": (
            "meta_ocg_provider_delta:anchor:class:" f"{source_class_semantic_key}"
        ),
        "operation_family": "anchor",
        "provider_operation_type": "meta_ocg.class.anchor",
        "semantic_key": source_class_semantic_key,
        "ontology_subject_kind": "class",
        "baseline": {"object_id": str(source_class_config_id)},
        "current": {
            "semantic_key": source_class_semantic_key,
            "object_kind": "class",
            "node_type": "class",
            "entity_id": str(source_class_config_id),
            "entity_name": "Room",
        },
    }


@pytest.mark.asyncio
async def test_meta_provider_delta_executes_relationship_create_intent_through_runtime(
    tmp_path: Path,
) -> None:
    ctx = build_provider_delta_runtime_execution_context(
        workspace_root=tmp_path,
        key="provider-delta-relationship-create",
    )
    source_class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    relationship_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room:room_devices:"
        "one_to_many:aware_demo.default.home.Device"
    )
    source_class_config_id = provider_delta_uuid(
        "provider-delta-relationship-create-source-class"
    )
    target_class_config_id = provider_delta_uuid(
        "provider-delta-relationship-create-target-class"
    )
    relationship_config_id = provider_delta_uuid(
        "provider-delta-relationship-create-relationship"
    )
    typed_operation_plan: dict[str, object] = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "semantic_object_anchors": (
            _relationship_anchor(
                source_class_semantic_key=source_class_semantic_key,
                source_class_config_id=source_class_config_id,
            ),
        ),
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:create:relationship:"
                    f"{relationship_semantic_key}"
                ),
                "operation_family": "create",
                "provider_operation_type": "meta_ocg.relationship.create",
                "semantic_key": relationship_semantic_key,
                "semantic_subject_type": "aware_meta.ClassConfigRelationship",
                "ontology_subject_kind": "relationship",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {},
                "current": {
                    "semantic_key": relationship_semantic_key,
                    "object_kind": "relationship",
                    "entity_id": str(relationship_config_id),
                    "relationship_key": "room_devices",
                    "relationship_type": "one_to_many",
                    "relationship_signature": {
                        "target_class_config_id": str(target_class_config_id),
                        "identity_rail": "containment",
                        "forward_required": True,
                    },
                },
            },
        ),
    }

    commit_receipt = await _commit_relationship_operation(
        ctx=ctx,
        typed_operation_plan=typed_operation_plan,
    )

    assert commit_receipt["status"] == "execute_flag_commit_applied"
    invocation_receipt = cast(
        dict[str, object],
        commit_receipt["ontology_function_call_execution_receipt"],
    )
    assert invocation_receipt["status"] == "ontology_function_call_execution_applied"
    assert invocation_receipt["applied_invocation_count"] == 1
    assert len(ctx.runtime.requests) == 1
    create_request = ctx.runtime.requests[0]
    assert create_request.call_target is MetaGraphCallTarget.instance
    assert create_request.function_id == provider_delta_uuid(
        "ClassConfig.create_relationship.function"
    )
    assert create_request.target_object_id == source_class_config_id
    assert create_request.expected_head_commit_id == (
        ctx.baseline_root_domain_commit_id
    )
    assert create_request.domain_projection_hash == ctx.root_projection_hash
    assert create_request.domain_object_instance_graph_id == ctx.baseline_root_oig_id
    assert create_request.domain_object_instance_graph_identity_id == (
        ctx.baseline_root_oigi_id
    )
    assert create_request.kwargs == {
        "target_class_config_id": str(target_class_config_id),
        "relationship_key": "room_devices",
        "relationship_type": "one_to_many",
        "identity_rail": "containment",
        "forward_required": True,
        "forward_loading_strategy": None,
        "reverse_loading_strategy": None,
        "reified_from_relationship_id": None,
        "reified_role": None,
    }
    assert commit_receipt["commit_id"] == str(ctx.runtime.receipts[-1].commit_id)
    assert commit_receipt["object_instance_graph_commit_id"] == str(
        ctx.runtime.receipts[-1].object_instance_graph_commit_id
    )


@pytest.mark.asyncio
async def test_meta_provider_delta_executes_relationship_delete_intent_through_runtime(
    tmp_path: Path,
) -> None:
    ctx = build_provider_delta_runtime_execution_context(
        workspace_root=tmp_path,
        key="provider-delta-relationship-delete",
    )
    source_class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    relationship_semantic_key = f"{source_class_semantic_key}/relationship:devices"
    source_class_config_id = provider_delta_uuid(
        "provider-delta-relationship-delete-source-class"
    )
    relationship_config_id = provider_delta_uuid(
        "provider-delta-relationship-delete-relationship"
    )
    typed_operation_plan: dict[str, object] = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "semantic_object_anchors": (
            _relationship_anchor(
                source_class_semantic_key=source_class_semantic_key,
                source_class_config_id=source_class_config_id,
            ),
        ),
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:delete:relationship:"
                    f"{relationship_semantic_key}"
                ),
                "operation_family": "delete",
                "provider_operation_type": "meta_ocg.relationship.delete",
                "semantic_key": relationship_semantic_key,
                "semantic_subject_type": "aware_meta.ClassConfigRelationship",
                "ontology_subject_kind": "relationship",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(relationship_config_id),
                    "object_kind": "relationship",
                    "object": {"relationship_key": "devices"},
                },
                "current": {},
            },
        ),
    }

    commit_receipt = await _commit_relationship_operation(
        ctx=ctx,
        typed_operation_plan=typed_operation_plan,
    )

    assert commit_receipt["status"] == "execute_flag_commit_applied"
    invocation_receipt = cast(
        dict[str, object],
        commit_receipt["ontology_function_call_execution_receipt"],
    )
    assert invocation_receipt["status"] == "ontology_function_call_execution_applied"
    assert invocation_receipt["applied_invocation_count"] == 1
    assert len(ctx.runtime.requests) == 1
    delete_request = ctx.runtime.requests[0]
    assert delete_request.call_target is MetaGraphCallTarget.instance
    assert delete_request.function_id == provider_delta_uuid(
        "ClassConfig.remove_relationship_config.function"
    )
    assert delete_request.target_object_id == source_class_config_id
    assert delete_request.expected_head_commit_id == (
        ctx.baseline_root_domain_commit_id
    )
    assert delete_request.domain_projection_hash == ctx.root_projection_hash
    assert delete_request.domain_object_instance_graph_id == ctx.baseline_root_oig_id
    assert delete_request.domain_object_instance_graph_identity_id == (
        ctx.baseline_root_oigi_id
    )
    assert delete_request.kwargs == {
        "relationship_key": "devices",
        "relationship_config_id": str(relationship_config_id),
    }
    assert commit_receipt["commit_id"] == str(ctx.runtime.receipts[-1].commit_id)
    assert commit_receipt["object_instance_graph_commit_id"] == str(
        ctx.runtime.receipts[-1].object_instance_graph_commit_id
    )


@pytest.mark.asyncio
async def test_meta_provider_delta_executes_relationship_update_intent_through_runtime(
    tmp_path: Path,
) -> None:
    ctx = build_provider_delta_runtime_execution_context(
        workspace_root=tmp_path,
        key="provider-delta-relationship-update",
    )
    source_class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    relationship_semantic_key = f"{source_class_semantic_key}/relationship:devices"
    target_class_config_id = provider_delta_uuid(
        "provider-delta-relationship-update-target-class"
    )
    relationship_config_id = provider_delta_uuid(
        "provider-delta-relationship-update-relationship"
    )
    typed_operation_plan: dict[str, object] = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:relationship:"
                    f"{relationship_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.relationship.update",
                "semantic_key": relationship_semantic_key,
                "semantic_subject_type": "aware_meta.ClassConfigRelationship",
                "ontology_subject_kind": "relationship",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(relationship_config_id),
                    "object_kind": "relationship",
                    "object": {
                        "relationship_key": "devices",
                        "relationship_signature": {
                            "target_class_config_id": str(target_class_config_id),
                        },
                    },
                },
                "current": {
                    "relationship_key": "devices",
                    "relationship_signature": {
                        "target_class_config_id": str(target_class_config_id),
                        "relationship_type": "one_to_one",
                        "identity_rail": "reference",
                        "forward_required": True,
                        "forward_loading_strategy": "eager",
                        "reverse_loading_strategy": "lazy",
                    },
                },
            },
        ),
    }

    commit_receipt = await _commit_relationship_operation(
        ctx=ctx,
        typed_operation_plan=typed_operation_plan,
    )

    assert commit_receipt["status"] == "execute_flag_commit_applied"
    invocation_receipt = cast(
        dict[str, object],
        commit_receipt["ontology_function_call_execution_receipt"],
    )
    assert invocation_receipt["status"] == "ontology_function_call_execution_applied"
    assert invocation_receipt["applied_invocation_count"] == 1
    assert len(ctx.runtime.requests) == 1
    update_request = ctx.runtime.requests[0]
    assert update_request.call_target is MetaGraphCallTarget.instance
    assert update_request.function_id == provider_delta_uuid(
        "ClassConfigRelationship.update_config.function"
    )
    assert update_request.target_object_id == relationship_config_id
    assert update_request.expected_head_commit_id == (
        ctx.baseline_root_domain_commit_id
    )
    assert update_request.domain_projection_hash == ctx.root_projection_hash
    assert update_request.domain_object_instance_graph_id == ctx.baseline_root_oig_id
    assert update_request.domain_object_instance_graph_identity_id == (
        ctx.baseline_root_oigi_id
    )
    assert update_request.kwargs == {
        "relationship_type": "one_to_one",
        "identity_rail": "reference",
        "forward_required": True,
        "forward_loading_strategy": "eager",
        "reverse_loading_strategy": "lazy",
        "reified_from_relationship_id": None,
        "reified_role": None,
    }
    assert commit_receipt["commit_id"] == str(ctx.runtime.receipts[-1].commit_id)
    assert commit_receipt["object_instance_graph_commit_id"] == str(
        ctx.runtime.receipts[-1].object_instance_graph_commit_id
    )
