from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from aware_meta.materialization.deltas.execution import (
    _provider_delta_oig_commit_receipt,
)
from aware_meta.materialization.deltas.ontology_execution.service import (
    build_provider_delta_ontology_execution_plan,
)
from aware_meta.runtime.invocation_engine import MetaGraphCallTarget

from ..fixtures import provider_delta_uuid
from .fixtures import (
    ProviderDeltaRuntimeExecutionContext,
    build_provider_delta_runtime_execution_context,
)


async def _commit_class_parent_operation(
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
async def test_meta_provider_delta_executes_class_parent_update_intent_through_runtime(
    tmp_path: Path,
) -> None:
    ctx = build_provider_delta_runtime_execution_context(
        workspace_root=tmp_path,
        key="provider-delta-class-parent-update",
    )
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Child"
    parent_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Parent"
    class_config_id = provider_delta_uuid("provider-delta-class-parent-update-child")
    parent_class_config_id = provider_delta_uuid(
        "provider-delta-class-parent-update-parent"
    )
    typed_operation_plan: dict[str, object] = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:class_parent:"
                    f"{class_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.class.parent.update",
                "semantic_key": class_semantic_key,
                "semantic_subject_type": "aware_meta.ClassConfig",
                "ontology_subject_kind": "class",
                "source_refs": ("aware/home/model.aware",),
                "baseline": {
                    "object_id": str(class_config_id),
                    "object_kind": "class",
                    "object": {
                        "class_config_id": str(class_config_id),
                        "class_fqn": "aware_demo.default.home.Child",
                        "class_name": "Child",
                        "parent_class_id": None,
                    },
                },
                "current": {
                    "semantic_key": class_semantic_key,
                    "object_kind": "class",
                    "entity_id": str(class_config_id),
                    "class_config_id": str(class_config_id),
                    "class_fqn": "aware_demo.default.home.Child",
                    "class_name": "Child",
                    "parent_class_id": str(parent_class_config_id),
                    "parent_class_fqn": "aware_demo.default.home.Parent",
                    "parent_class_semantic_key": parent_semantic_key,
                    "previous_parent_class_id": None,
                    "semantic_scope_closure_consumed": True,
                    "semantic_scope_closure_ready": True,
                    "semantic_scope_closure_blockers": (),
                },
            },
        ),
    }

    commit_receipt = await _commit_class_parent_operation(
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
        "ClassConfig.update_parent_class.function"
    )
    assert update_request.target_object_id == class_config_id
    assert update_request.expected_head_commit_id == (
        ctx.baseline_root_domain_commit_id
    )
    assert update_request.domain_projection_hash == ctx.root_projection_hash
    assert update_request.domain_object_instance_graph_id == ctx.baseline_root_oig_id
    assert update_request.domain_object_instance_graph_identity_id == (
        ctx.baseline_root_oigi_id
    )
    assert update_request.kwargs == {
        "parent_class_config_id": str(parent_class_config_id),
    }
    assert commit_receipt["commit_id"] == str(ctx.runtime.receipts[-1].commit_id)
    assert commit_receipt["object_instance_graph_commit_id"] == str(
        ctx.runtime.receipts[-1].object_instance_graph_commit_id
    )
