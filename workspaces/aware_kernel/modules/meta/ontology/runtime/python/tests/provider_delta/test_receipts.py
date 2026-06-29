from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from aware_meta.materialization.deltas.execution import (
    _provider_delta_initial_head_context,
)
from aware_meta.materialization.deltas.index_patch import (
    _provider_delta_runtime_package_index_patch_receipt,
)
from aware_meta.runtime.package_index import (
    MetaRuntimePackageIndexEntry,
    MetaRuntimePackageIndexPatch,
    MetaRuntimeSemanticObjectIndexEntry,
    build_meta_runtime_package_projection_index,
    meta_runtime_package_projection_index_path,
    record_meta_runtime_package_index_patch,
)

from .fixtures import (
    provider_delta_request,
    provider_delta_uuid,
    write_meta_delta_fixture,
)


@pytest.mark.asyncio
async def test_provider_delta_initial_head_context_uses_hydrated_oig_identity_for_matching_projection(
    tmp_path: Path,
) -> None:
    branch_id = provider_delta_uuid("provider-delta-matching-projection-branch")
    projection_hash = "sha256:test:matching:ObjectConfigGraphPackage"
    domain_commit_id = provider_delta_uuid(
        "provider-delta-matching-projection-domain-head"
    )
    object_instance_graph_id = provider_delta_uuid(
        "provider-delta-matching-projection-oig"
    )
    object_instance_graph_identity_id = provider_delta_uuid(
        "provider-delta-matching-projection-oigi"
    )
    request = SimpleNamespace(
        workspace_root=str(tmp_path),
    )
    hydration = {
        "semantic_projection_hash": projection_hash,
        "details": {
            "materializer_metadata": {
                "domain_commit_id": str(domain_commit_id),
                "object_instance_graph_id": str(object_instance_graph_id),
                "object_instance_graph_identity_id": (
                    str(object_instance_graph_identity_id)
                ),
            },
        },
    }
    baseline_ref = {
        "semantic_projection_hash": projection_hash,
        "semantic_package_commit_id": str(domain_commit_id),
    }

    context = await _provider_delta_initial_head_context(
        request=request,
        hydration=hydration,
        baseline_ref=baseline_ref,
        branch_id=branch_id,
        projection_hash=projection_hash,
        semantic_projection_hash=projection_hash,
    )

    assert context["domain_commit_id"] == domain_commit_id
    assert context["object_instance_graph_id"] == object_instance_graph_id
    assert (
        context["object_instance_graph_identity_id"]
        == object_instance_graph_identity_id
    )


def test_meta_provider_delta_runtime_package_index_patch_blocks_before_commit(
    tmp_path: Path,
) -> None:
    manifest_path = write_meta_delta_fixture(tmp_path)
    base_request = provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
    )
    request = SimpleNamespace(
        package=base_request.package,
        baseline_ref=base_request.baseline_ref,
    )

    receipt = _provider_delta_runtime_package_index_patch_receipt(
        request=request,
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
            "typed_operation_count": 0,
            "typed_operations": (),
        },
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_unavailable",
            "reason": "meta_ocg_provider_delta_head_move_requires_applied_oig_commit",
            "head_refs": {"head_ref_status": "head_refs_unavailable"},
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_not_requested",
            "reason": "meta_ocg_provider_delta_execute_flag_commit_not_requested",
        },
        current_delta_fingerprint="sha256:blocked",
    )

    assert receipt["status"] == "runtime_package_index_patch_blocked"
    assert receipt["did_persist"] is False
    assert "oig_commit_not_applied:execute_flag_commit_not_requested" in cast(
        Sequence[str],
        receipt["blockers"],
    )
    assert not meta_runtime_package_projection_index_path(
        aware_root=tmp_path,
    ).exists()


def test_meta_provider_delta_runtime_package_index_patch_noop_is_empty(
    tmp_path: Path,
) -> None:
    manifest_path = write_meta_delta_fixture(tmp_path)
    base_request = provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
    )
    request = SimpleNamespace(
        package=base_request.package,
        baseline_ref=base_request.baseline_ref,
    )
    head_refs = {
        "head_ref_status": "head_refs_available",
        "source_object_instance_graph_commit_id": (
            base_request.baseline_ref.source_object_instance_graph_commit_id
        ),
        "semantic_branch_id": base_request.baseline_ref.semantic_branch_id,
        "semantic_projection_name": (
            base_request.baseline_ref.semantic_projection_name
        ),
        "semantic_package_id": base_request.baseline_ref.semantic_package_id,
        "semantic_root_id": base_request.baseline_ref.semantic_root_id,
        "semantic_package_commit_id": (
            base_request.baseline_ref.semantic_package_commit_id
        ),
        "semantic_object_instance_graph_commit_id": (
            base_request.baseline_ref.semantic_object_instance_graph_commit_id
        ),
        "semantic_root_object_instance_graph_commit_id": (
            base_request.baseline_ref.semantic_root_object_instance_graph_commit_id
        ),
    }

    receipt = _provider_delta_runtime_package_index_patch_receipt(
        request=request,
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
            "typed_operation_count": 0,
            "typed_operations": (),
        },
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_ready",
            "reason": "meta_ocg_provider_delta_head_stayed_noop",
            "head_refs": head_refs,
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_noop",
            "reason": "meta_ocg_provider_delta_no_semantic_operations",
        },
        current_delta_fingerprint="sha256:noop",
    )

    assert receipt["status"] == "runtime_package_index_patch_empty"
    assert receipt["available"] is True
    assert receipt["semantic_object_upsert_count"] == 0
    assert receipt["semantic_object_delete_count"] == 0
    assert receipt["blockers"] == ()
    assert not meta_runtime_package_projection_index_path(
        aware_root=tmp_path,
    ).exists()


def test_meta_provider_delta_runtime_package_index_patch_applies_after_commit(
    tmp_path: Path,
) -> None:
    manifest_path = write_meta_delta_fixture(tmp_path)
    package_entry = MetaRuntimePackageIndexEntry(
        module_id="demo",
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        manifest_path=manifest_path,
    )
    _ = build_meta_runtime_package_projection_index(
        repo_root=tmp_path,
        aware_root=tmp_path,
        package_entries=(package_entry,),
    )
    stale_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:state"
    )
    _ = record_meta_runtime_package_index_patch(
        aware_root=tmp_path,
        patch=MetaRuntimePackageIndexPatch(
            semantic_object_upserts=(
                MetaRuntimeSemanticObjectIndexEntry(
                    semantic_key=stale_semantic_key,
                    object_kind="attribute",
                    package_name="demo-ontology",
                    fqn_prefix="aware_demo",
                    manifest_path=manifest_path,
                    owner_semantic_key=(
                        "ocg:aware_demo/node:aware_demo.default.home.Room"
                    ),
                    attribute_name="state",
                    source_refs=("home/model.aware",),
                ),
            ),
        ),
    )
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    function_semantic_key = f"{class_semantic_key}.rename"
    function_impl_semantic_key = f"{function_semantic_key}/function_impl:default"
    node_id = provider_delta_uuid("index-patch-room-node-id")
    class_config_id = provider_delta_uuid("index-patch-room-class-config-id")
    function_impl_id = provider_delta_uuid("index-patch-room-rename-function-impl-id")
    baseline_node_id = provider_delta_uuid("index-patch-baseline-room-node")
    baseline_function_impl_id = provider_delta_uuid(
        "index-patch-baseline-function-impl"
    )
    commit_id = provider_delta_uuid("index-patch-commit")
    source_commit_id = provider_delta_uuid("index-patch-source-commit")
    semantic_package_id = provider_delta_uuid("index-patch-semantic-package")
    semantic_branch_id = provider_delta_uuid("index-patch-semantic-branch")
    head_refs = {
        "head_ref_status": "head_refs_available",
        "source_object_instance_graph_commit_id": str(source_commit_id),
        "semantic_branch_id": str(semantic_branch_id),
        "semantic_projection_name": "ObjectConfigGraphPackage",
        "semantic_package_id": str(semantic_package_id),
        "semantic_package_commit_id": str(commit_id),
        "semantic_object_instance_graph_commit_id": str(commit_id),
        "semantic_root_object_instance_graph_commit_id": str(commit_id),
    }
    base_request = provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
    )
    request = SimpleNamespace(
        package=base_request.package,
        baseline_ref=base_request.baseline_ref,
        current_delta_fingerprint="sha256:index-patch",
    )

    receipt = _provider_delta_runtime_package_index_patch_receipt(
        request=request,
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
            "typed_operation_count": 3,
            "typed_operations": (
                {
                    "operation_family": "update",
                    "provider_operation_type": "meta_ocg.class.update",
                    "semantic_key": class_semantic_key,
                    "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
                    "ontology_subject_kind": "class",
                    "source_refs": ("home/model.aware",),
                    "baseline": {
                        "object_id": str(baseline_node_id),
                        "object_kind": "class",
                    },
                    "current": {
                        "semantic_key": class_semantic_key,
                        "object_kind": "class",
                        "graph_semantic_key": "ocg:aware_demo",
                        "node_key": "aware_demo.default.home.Room",
                        "entity_id": str(class_config_id),
                        "entity_name": "Room",
                        "payload": {
                            "semantic_key": class_semantic_key,
                            "object_kind": "class",
                            "graph_semantic_key": "ocg:aware_demo",
                            "node_id": str(node_id),
                            "node_key": "aware_demo.default.home.Room",
                            "entity_id": str(class_config_id),
                            "entity_name": "Room",
                            "source_refs": ("home/model.aware",),
                            "semantic_fingerprint": "sha256:room",
                        },
                    },
                },
                {
                    "operation_family": "update",
                    "provider_operation_type": "meta_ocg.function_impl.update",
                    "semantic_key": function_impl_semantic_key,
                    "semantic_subject_type": "aware_meta.FunctionImpl",
                    "ontology_subject_kind": "function_impl",
                    "source_refs": ("home/model.aware",),
                    "baseline": {
                        "object_id": str(baseline_function_impl_id),
                        "object_kind": "function_impl",
                    },
                    "current": {
                        "semantic_key": function_impl_semantic_key,
                        "object_kind": "function_impl",
                        "graph_semantic_key": "ocg:aware_demo",
                        "parent_semantic_key": function_semantic_key,
                        "owner_semantic_key": class_semantic_key,
                        "entity_id": str(function_impl_id),
                        "entity_name": "default",
                        "function_semantic_key": function_semantic_key,
                        "function_name": "rename",
                        "function_impl_key": "default",
                        "function_impl_kind": "instruction_body",
                        "function_impl_signature": {
                            "instruction_count": 1,
                            "instruction_summaries": ("set name = new_name",),
                        },
                        "payload": {
                            "semantic_key": function_impl_semantic_key,
                            "object_kind": "function_impl",
                            "graph_semantic_key": "ocg:aware_demo",
                            "parent_semantic_key": function_semantic_key,
                            "owner_semantic_key": class_semantic_key,
                            "entity_id": str(function_impl_id),
                            "function_semantic_key": function_semantic_key,
                            "function_name": "rename",
                            "function_impl_key": "default",
                            "function_impl_kind": "instruction_body",
                            "function_impl_signature": {
                                "instruction_count": 1,
                                "instruction_summaries": ("set name = new_name",),
                            },
                            "source_refs": ("home/model.aware",),
                            "semantic_fingerprint": "sha256:function-impl",
                        },
                    },
                },
                {
                    "operation_family": "delete",
                    "provider_operation_type": "meta_ocg.attribute.delete",
                    "semantic_key": stale_semantic_key,
                    "semantic_subject_type": "aware_meta.AttributeConfig",
                    "ontology_subject_kind": "attribute",
                    "source_refs": ("home/model.aware",),
                    "baseline": {
                        "object_id": str(
                            provider_delta_uuid("index-patch-baseline-state-attribute")
                        ),
                        "object_kind": "attribute",
                    },
                    "current": {},
                },
            ),
        },
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_ready",
            "reason": "meta_ocg_provider_delta_head_move_applied",
            "head_refs": head_refs,
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_applied",
            "reason": "meta_ocg_provider_delta_oig_commit_applied",
            "commit_id": str(commit_id),
        },
        current_delta_fingerprint="sha256:index-patch",
    )

    assert receipt["status"] == "runtime_package_index_patch_applied"
    assert receipt["did_persist"] is True
    assert receipt["semantic_object_upsert_count"] == 2
    assert receipt["semantic_object_delete_count"] == 1
    assert receipt["semantic_object_upsert_keys"] == (
        class_semantic_key,
        function_impl_semantic_key,
    )
    assert receipt["semantic_object_delete_keys"] == (stale_semantic_key,)
    payload = json.loads(
        meta_runtime_package_projection_index_path(
            aware_root=tmp_path,
        ).read_text(encoding="utf-8")
    )
    semantic_objects = {
        str(item["semantic_key"]): item
        for item in cast(Sequence[dict[str, object]], payload["semantic_objects"])
    }
    assert stale_semantic_key not in semantic_objects
    class_entry = semantic_objects[class_semantic_key]
    assert class_entry["object_id"] == str(baseline_node_id)
    assert class_entry["entity_id"] == str(class_config_id)
    assert class_entry["source_refs"] == ["home/model.aware"]
    assert class_entry["semantic_package_object_instance_graph_commit_id"] == (
        str(commit_id)
    )
    assert class_entry["semantic_root_object_instance_graph_commit_id"] == (
        str(commit_id)
    )
    assert class_entry["source_object_instance_graph_commit_id"] == (
        str(source_commit_id)
    )
    assert class_entry["runtime_delta_fingerprint"] == "sha256:index-patch"
    function_impl_entry = semantic_objects[function_impl_semantic_key]
    assert function_impl_entry["object_kind"] == "function_impl"
    assert function_impl_entry["object_id"] == str(baseline_function_impl_id)
    assert function_impl_entry["parent_semantic_key"] == function_semantic_key
    assert function_impl_entry["owner_semantic_key"] == class_semantic_key
    assert function_impl_entry["source_refs"] == ["home/model.aware"]
    assert function_impl_entry["semantic_package_object_instance_graph_commit_id"] == (
        str(commit_id)
    )
    assert function_impl_entry["runtime_delta_fingerprint"] == "sha256:index-patch"
