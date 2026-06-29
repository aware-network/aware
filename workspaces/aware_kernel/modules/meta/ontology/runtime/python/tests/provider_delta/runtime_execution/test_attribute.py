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
    RecordingProviderDeltaOntologyRuntime,
    provider_delta_ontology_invocation_runtime_context,
    write_root_oig_head_context,
)


@pytest.mark.asyncio
async def test_meta_provider_delta_executes_attribute_replacement_intents_through_runtime(
    tmp_path: Path,
) -> None:
    branch_id = provider_delta_uuid("provider-delta-attribute-replacement-branch")
    actor_id = provider_delta_uuid("provider-delta-attribute-replacement-actor")
    baseline_domain_commit_id = provider_delta_uuid(
        "provider-delta-attribute-replacement-baseline-domain-head"
    )
    baseline_oig_commit_id = provider_delta_uuid(
        "provider-delta-attribute-replacement-baseline-oig-head"
    )
    baseline_root_domain_commit_id = provider_delta_uuid(
        "provider-delta-attribute-replacement-baseline-root-domain-head"
    )
    baseline_root_oig_commit_id = provider_delta_uuid(
        "provider-delta-attribute-replacement-baseline-root-oig-head"
    )
    baseline_root_oig_id = provider_delta_uuid(
        "provider-delta-attribute-replacement-baseline-root-oig"
    )
    baseline_root_oigi_id = provider_delta_uuid(
        "provider-delta-attribute-replacement-baseline-root-oigi"
    )
    package_projection_hash = "sha256:test:ObjectConfigGraphPackage"
    root_projection_hash = "sha256:test:ObjectConfigGraph"
    runtime = RecordingProviderDeltaOntologyRuntime()
    graph_runtime_context = provider_delta_ontology_invocation_runtime_context(
        root_projection_hash=root_projection_hash,
        package_projection_hash=package_projection_hash,
    )
    write_root_oig_head_context(
        workspace_root=tmp_path,
        branch_id=branch_id,
        root_projection_hash=root_projection_hash,
        root_domain_commit_id=baseline_root_domain_commit_id,
        root_oig_commit_id=baseline_root_oig_commit_id,
        root_oig_id=baseline_root_oig_id,
        root_oigi_id=baseline_root_oigi_id,
    )
    function_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room.rename"
    attribute_semantic_key = f"{function_semantic_key}/attribute:input:name"
    membership_semantic_key = f"{attribute_semantic_key}/membership:function_config"
    function_config_id = provider_delta_uuid(
        "provider-delta-attribute-replacement-function"
    )
    baseline_attribute_config_id = provider_delta_uuid(
        "provider-delta-attribute-replacement-baseline-attribute"
    )
    current_attribute_config_id = provider_delta_uuid(
        "provider-delta-attribute-replacement-current-attribute"
    )
    edge_id = provider_delta_uuid("provider-delta-attribute-replacement-edge")
    typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operation_count": 1,
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:attribute_membership:"
                    f"{membership_semantic_key}"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.attribute_membership.update",
                "semantic_key": membership_semantic_key,
                "semantic_subject_type": ("aware_meta.FunctionConfigAttributeConfig"),
                "ontology_subject_kind": "attribute_membership",
                "source_refs": ("aware/home/room.aware",),
                "baseline": {
                    "object_id": str(edge_id),
                    "object_kind": "attribute_membership",
                    "object": {
                        "function_config_attribute_config_id": str(edge_id),
                        "function_config_id": str(function_config_id),
                        "attribute_config_id": str(baseline_attribute_config_id),
                        "attribute_name": "name",
                        "attribute_signature": {
                            "name": "name",
                            "description": "Original name.",
                            "default_value": None,
                            "is_primary": False,
                            "is_public": True,
                            "is_required": True,
                            "is_unique": False,
                            "is_virtual": False,
                            "type_descriptor": {
                                "kind": "primitive",
                                "primitive_base_type": "string",
                            },
                        },
                        "attribute_membership_signature": {
                            "owner_kind": "function",
                            "function_config_id": str(function_config_id),
                            "attribute_config_id": str(baseline_attribute_config_id),
                            "name": "name",
                            "type": "input",
                            "position": 1,
                            "is_identity_key": True,
                            "identity_key_origin": "propagated_parent",
                        },
                    },
                },
                "current": {
                    "function_config_attribute_config_id": str(edge_id),
                    "function_config_id": str(function_config_id),
                    "attribute_config_id": str(current_attribute_config_id),
                    "attribute_name": "display_name",
                    "attribute_membership_owner_kind": "function",
                    "attribute_membership_identity_replacement_fields": (
                        "name",
                        "type",
                    ),
                    "payload": {
                        "attribute_signature": {
                            "name": "display_name",
                            "description": "New display name.",
                            "default_value": None,
                            "is_primary": False,
                            "is_public": True,
                            "is_required": True,
                            "is_unique": False,
                            "is_virtual": False,
                            "type_descriptor": {
                                "kind": "primitive",
                                "primitive_base_type": "string",
                            },
                        },
                    },
                    "attribute_membership_signature": {
                        "owner_kind": "function",
                        "function_config_id": str(function_config_id),
                        "attribute_config_id": str(current_attribute_config_id),
                        "name": "display_name",
                        "type": "output",
                        "position": 1,
                        "is_identity_key": False,
                        "identity_key_origin": "standalone",
                    },
                },
            },
        ),
    }
    ontology_execution_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    assert ontology_execution_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_execution_plan["invocation_intent_count"] == 2
    request = SimpleNamespace(
        execute_provider_delta_materialization=True,
        context={
            "runtime": runtime,
            "aware_meta.graph_runtime_context": graph_runtime_context,
        },
        workspace_root=str(tmp_path),
        provider_delta_author_id=str(actor_id),
        semantic_branch_id=str(branch_id),
        semantic_projection_hash=package_projection_hash,
        baseline_semantic_object_instance_graph_commit_id=str(baseline_oig_commit_id),
        baseline_semantic_root_object_instance_graph_commit_id=(
            str(baseline_root_oig_commit_id)
        ),
        semantic_package_commit_id=str(baseline_domain_commit_id),
    )
    baseline_dirty_preflight = {
        "status": "baseline_commit_refs_available",
        "commit_backed_baseline_available": True,
        "baseline_ref_available": True,
        "baseline_ref_hydrator_ready": True,
        "baseline_hydration_preflight": {
            "status": "baseline_hydrated",
            "semantic_branch_id": str(branch_id),
            "semantic_projection_hash": package_projection_hash,
            "semantic_object_instance_graph_commit_id": str(baseline_oig_commit_id),
            "semantic_root_object_instance_graph_commit_id": (
                str(baseline_root_oig_commit_id)
            ),
            "details": {
                "materializer_metadata": {
                    "domain_commit_id": str(baseline_domain_commit_id),
                },
            },
        },
    }

    commit_receipt = await _provider_delta_oig_commit_receipt(
        request=request,
        baseline_dirty_preflight=baseline_dirty_preflight,
        provider_delta_mutation_plan={},
        provider_delta_ontology_execution_plan=ontology_execution_plan,
        provider_delta_execute_flag_preflight={
            "status": "execute_flag_preflight_ready",
        },
    )

    assert commit_receipt["status"] == "execute_flag_commit_applied"
    invocation_receipt = cast(
        dict[str, object],
        commit_receipt["ontology_function_call_execution_receipt"],
    )
    assert invocation_receipt["status"] == "ontology_function_call_execution_applied"
    assert invocation_receipt["applied_invocation_count"] == 2
    assert len(runtime.requests) == 2
    remove_request = runtime.requests[0]
    assert remove_request.call_target is MetaGraphCallTarget.instance
    assert remove_request.function_id == provider_delta_uuid(
        "FunctionConfig.remove_attribute_config.function"
    )
    assert remove_request.target_object_id == function_config_id
    assert remove_request.expected_head_commit_id == baseline_root_domain_commit_id
    assert remove_request.domain_projection_hash == root_projection_hash
    assert remove_request.domain_object_instance_graph_id == baseline_root_oig_id
    assert remove_request.domain_object_instance_graph_identity_id == (
        baseline_root_oigi_id
    )
    assert remove_request.kwargs == {
        "name": "name",
        "attribute_config_id": str(baseline_attribute_config_id),
        "type": "input",
    }
    create_request = runtime.requests[1]
    assert create_request.call_target is MetaGraphCallTarget.instance
    assert create_request.function_id == provider_delta_uuid(
        "FunctionConfig.add_primitive_attribute_config.function"
    )
    assert create_request.target_object_id == function_config_id
    assert create_request.expected_head_commit_id == runtime.receipts[0].commit_id
    assert create_request.expected_graph_hash_pre == runtime.receipts[0].graph_hash_post
    assert create_request.kwargs == {
        "name": "display_name",
        "description": "New display name.",
        "default_value": None,
        "is_primary": False,
        "is_public": True,
        "is_required": True,
        "is_unique": False,
        "is_virtual": False,
        "position": 1,
        "type": "output",
        "is_identity_key": False,
        "primitive_base_type": "string",
    }
    assert commit_receipt["commit_id"] == str(runtime.receipts[-1].commit_id)
    assert commit_receipt["object_instance_graph_commit_id"] == str(
        runtime.receipts[-1].object_instance_graph_commit_id
    )
