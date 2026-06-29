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


async def _commit_function_operation(
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


@pytest.mark.asyncio
async def test_meta_provider_delta_executes_function_update_intent_through_runtime(
    tmp_path: Path,
) -> None:
    ctx = build_provider_delta_runtime_execution_context(
        workspace_root=tmp_path,
        key="provider-delta-function-update",
    )
    function_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
    generic_object_id = provider_delta_uuid(
        "provider-delta-function-update-generic-object"
    )
    function_config_id = provider_delta_uuid("provider-delta-function-update-function")
    typed_operation_plan: dict[str, object] = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:function:"
                    f"{function_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.function.update",
                "semantic_key": function_semantic_key,
                "semantic_subject_type": "aware_meta.FunctionConfig",
                "ontology_subject_kind": "function",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(generic_object_id),
                    "object_kind": "function",
                    "object": {
                        "object_id": str(generic_object_id),
                        "payload": {
                            "entity_id": str(function_config_id),
                            "function_config_id": str(function_config_id),
                            "owner_key": "aware_demo.default.home.Room",
                            "name": "rename",
                            "kind": "instance",
                        },
                        "owner_key": "aware_demo.default.home.Room",
                        "name": "rename",
                        "kind": "instance",
                    },
                },
                "current": {
                    "object_id": str(generic_object_id),
                    "entity_id": str(function_config_id),
                    "function_config_id": str(function_config_id),
                    "function_name": "rename",
                    "function_signature": {
                        "owner_key": "aware_demo.default.home.Room",
                        "name": "rename",
                        "kind": "instance",
                        "description": "Rename a room.",
                        "verb": "rename",
                        "is_async": True,
                    },
                },
            },
        ),
    }

    commit_receipt = await _commit_function_operation(
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
        "FunctionConfig.update_config.function"
    )
    assert update_request.target_object_id == function_config_id
    assert update_request.expected_head_commit_id == (
        ctx.baseline_root_domain_commit_id
    )
    assert update_request.domain_projection_hash == ctx.root_projection_hash
    assert update_request.domain_object_instance_graph_id == ctx.baseline_root_oig_id
    assert update_request.domain_object_instance_graph_identity_id == (
        ctx.baseline_root_oigi_id
    )
    assert update_request.kwargs == {
        "description": "Rename a room.",
        "verb": "rename",
        "is_async": True,
    }


@pytest.mark.asyncio
async def test_meta_provider_delta_executes_function_membership_update_intent_through_runtime(
    tmp_path: Path,
) -> None:
    ctx = build_provider_delta_runtime_execution_context(
        workspace_root=tmp_path,
        key="provider-delta-function-membership-update",
    )
    function_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
    membership_semantic_key = f"{function_semantic_key}/membership:class_config"
    edge_id = provider_delta_uuid("provider-delta-function-membership-update-edge")
    class_config_id = provider_delta_uuid(
        "provider-delta-function-membership-update-class"
    )
    function_config_id = provider_delta_uuid(
        "provider-delta-function-membership-update-function"
    )
    typed_operation_plan: dict[str, object] = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:function_membership:"
                    f"{membership_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.function_membership.update",
                "semantic_key": membership_semantic_key,
                "semantic_subject_type": "aware_meta.ClassConfigFunctionConfig",
                "ontology_subject_kind": "function_membership",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(edge_id),
                    "object_kind": "function_membership",
                    "object": {
                        "class_config_function_config_id": str(edge_id),
                        "class_config_id": str(class_config_id),
                        "function_config_id": str(function_config_id),
                    },
                },
                "current": {
                    "function_semantic_key": function_semantic_key,
                    "class_config_function_config_id": str(edge_id),
                    "class_config_id": str(class_config_id),
                    "function_config_id": str(function_config_id),
                    "function_membership_signature": {
                        "class_config_id": str(class_config_id),
                        "function_config_id": str(function_config_id),
                        "is_public": False,
                        "is_constructor": True,
                        "position": 2,
                    },
                },
            },
        ),
    }

    commit_receipt = await _commit_function_operation(
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
        "ClassConfigFunctionConfig.update_config.function"
    )
    assert update_request.target_object_id == edge_id
    assert update_request.expected_head_commit_id == (
        ctx.baseline_root_domain_commit_id
    )
    assert update_request.domain_projection_hash == ctx.root_projection_hash
    assert update_request.domain_object_instance_graph_id == ctx.baseline_root_oig_id
    assert update_request.domain_object_instance_graph_identity_id == (
        ctx.baseline_root_oigi_id
    )
    assert update_request.kwargs == {
        "is_public": False,
        "is_constructor": True,
        "position": 2,
    }
