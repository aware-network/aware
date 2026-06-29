from __future__ import annotations

from collections.abc import Sequence
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_meta.materialization.deltas.change_evidence import (
    _provider_delta_semantic_change_report,
    _provider_delta_semantic_commit_evidence,
)


def test_meta_provider_delta_change_report_exposes_readable_chain() -> None:
    class_semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    attribute_semantic_key = f"{class_semantic_key}/attribute:name"
    typed_attribute_semantic_key = f"{class_semantic_key}/attribute:capacity"
    function_semantic_key = f"{class_semantic_key}.rename"
    function_impl_semantic_key = f"{function_semantic_key}/function_impl:default"
    relationship_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.Room:doors:one_to_many:"
        "aware_demo.default.home.Door"
    )

    report = _provider_delta_semantic_change_report(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "reason": "meta_ocg_dirty_diff_ready",
            "dirty_entry_count": 8,
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
            "typed_operations": (
                {
                    "operation_family": "update",
                    "ontology_subject_kind": "object_config_graph_package",
                    "semantic_key": "ocg_package:demo-ontology",
                    "source_refs": ("aware.toml",),
                    "current": {
                        "payload": {"package_name": "demo-ontology"},
                    },
                },
                {
                    "operation_family": "update",
                    "ontology_subject_kind": "object_config_graph",
                    "semantic_key": "ocg:aware_demo",
                    "source_refs": ("home/model.aware",),
                    "current": {
                        "payload": {"fqn_prefix": "aware_demo"},
                    },
                },
                {
                    "operation_family": "update",
                    "ontology_subject_kind": "class",
                    "semantic_key": class_semantic_key,
                    "source_refs": ("home/model.aware",),
                    "current": {
                        "entity_name": "Room",
                    },
                },
                {
                    "operation_family": "create",
                    "ontology_subject_kind": "attribute",
                    "semantic_key": attribute_semantic_key,
                    "source_refs": ("home/model.aware",),
                    "current": {
                        "attribute_name": "name",
                        "owner_semantic_key": class_semantic_key,
                    },
                },
                {
                    "operation_family": "update",
                    "ontology_subject_kind": "attribute",
                    "semantic_key": typed_attribute_semantic_key,
                    "source_refs": ("home/model.aware",),
                    "baseline": {
                        "object": {
                            "attribute_name": "capacity",
                            "attribute_signature": {
                                "kind": "primitive",
                                "primitive_base_type": "string",
                                "is_required": True,
                            },
                        },
                    },
                    "current": {
                        "attribute_name": "capacity",
                        "owner_semantic_key": class_semantic_key,
                        "attribute_signature": {
                            "kind": "primitive",
                            "primitive_base_type": "int",
                            "is_required": True,
                        },
                    },
                },
                {
                    "operation_family": "update",
                    "ontology_subject_kind": "function",
                    "semantic_key": function_semantic_key,
                    "source_refs": ("home/model.aware",),
                    "current": {
                        "function_name": "rename",
                        "owner_semantic_key": class_semantic_key,
                        "function_signature": {
                            "description": (
                                "Rename the room for humans and assistants."
                            ),
                        },
                    },
                },
                {
                    "operation_family": "update",
                    "ontology_subject_kind": "function_impl",
                    "semantic_key": function_impl_semantic_key,
                    "source_refs": ("home/model.aware",),
                    "baseline": {
                        "object": {
                            "function_name": "rename",
                            "owner_semantic_key": class_semantic_key,
                            "function_impl_signature": {
                                "instruction_summaries": (),
                            },
                        },
                    },
                    "current": {
                        "function_name": "rename",
                        "owner_semantic_key": class_semantic_key,
                        "function_semantic_key": function_semantic_key,
                        "function_impl_key": "default",
                        "function_impl_signature": {
                            "instruction_summaries": ("set name = new_name",),
                        },
                    },
                },
                {
                    "operation_family": "create",
                    "ontology_subject_kind": "relationship",
                    "semantic_key": relationship_semantic_key,
                    "source_refs": ("home/model.aware",),
                    "current": {
                        "relationship_key": "doors",
                    },
                },
            ),
        },
    )

    assert report["status"] == "semantic_change_report_ready"
    chain = cast(
        dict[str, object],
        report["minimal_readable_semantic_change_chain"],
    )
    assert chain["contract_version"] == (
        "aware.meta.ocg.provider-delta-readable-semantic-change-chain.v1"
    )
    assert chain["source_change_count"] == 8
    assert chain["change_count"] == 6
    assert chain["lines"] == (
        "1. Update class `Room`.",
        "2. Add attribute `name` on `Room`.",
        "3. Update attribute `capacity` on `Room`. "
        "Type changes from `String` to `Int`.",
        "4. Update function `rename` on `Room`. "
        "Rename the room for humans and assistants.",
        "5. Update implementation for function `rename` on `Room`. "
        "Body changes from no executable instructions to `set name = new_name`.",
        "6. Add relationship `doors` from `Room` to `Door`.",
    )
    assert report["readable_semantic_change_chain_markdown"] == (
        "1. Update class `Room`.\n"
        "2. Add attribute `name` on `Room`.\n"
        "3. Update attribute `capacity` on `Room`. "
        "Type changes from `String` to `Int`.\n"
        "4. Update function `rename` on `Room`. "
        "Rename the room for humans and assistants.\n"
        "5. Update implementation for function `rename` on `Room`. "
        "Body changes from no executable instructions to `set name = new_name`.\n"
        "6. Add relationship `doors` from `Room` to `Door`."
    )


def test_meta_provider_delta_semantic_commit_evidence_blocks_before_commit() -> None:
    translation = _provider_delta_semantic_commit_evidence(
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_blocked",
            "reason": "meta_ocg_provider_delta_typed_operation_plan_blocked",
            "typed_operations": (),
        },
        provider_delta_head_move_plan={
            "status": "head_move_plan_blocked",
            "reason": "meta_ocg_provider_delta_head_move_plan_blocked",
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
    )

    assert translation["status"] == "semantic_commit_evidence_blocked"
    assert translation["available"] is False
    assert translation["committed_semantic_change_count"] == 0
    blockers = cast(Sequence[str], translation["blockers"])
    assert "typed_operation_plan_not_ready:typed_operation_plan_blocked" in blockers
    assert "oig_commit_not_applied:execute_flag_commit_not_requested" in blockers


def test_meta_provider_delta_semantic_commit_evidence_commits_changes() -> None:
    semantic_key = "ocg:aware_demo/node:aware_demo.default.home.Room"
    commit_id = _test_uuid("changes-commit")
    branch_id = _test_uuid("changes-branch")
    object_instance_graph_id = _test_uuid("changes-oig")
    object_instance_graph_identity_id = _test_uuid("changes-oig-identity")
    head_refs = {
        "head_ref_status": "head_refs_available",
        "source_object_instance_graph_commit_id": str(
            _test_uuid("changes-source-commit")
        ),
        "semantic_branch_id": str(branch_id),
        "semantic_projection_name": "ObjectConfigGraphPackage",
        "semantic_package_id": str(_test_uuid("changes-semantic-package")),
        "semantic_package_commit_id": str(commit_id),
        "semantic_object_instance_graph_commit_id": str(commit_id),
        "semantic_root_object_instance_graph_commit_id": str(commit_id),
    }

    translation = _provider_delta_semantic_commit_evidence(
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
            "typed_operation_count": 1,
            "typed_operations": (
                {
                    "operation_key": "meta_ocg_provider_delta:update:class:room",
                    "operation_family": "update",
                    "provider_operation_type": "meta_ocg.class.update",
                    "semantic_key": semantic_key,
                    "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
                    "ontology_subject_kind": "class",
                    "source_delta_key": "delta:room",
                    "source_refs": ("home/model.aware",),
                    "baseline": {
                        "object_id": "baseline-room",
                        "object_kind": "class",
                    },
                    "current": {
                        "semantic_key": semantic_key,
                        "object_kind": "class",
                        "entity_name": "Room",
                    },
                    "ocg_operation": {
                        "operation": "ensure_object_config_graph_node",
                    },
                    "semantic_change_projection": {
                        "change_key": "aware_meta.provider_delta.class.update",
                        "delta_keys": ("delta:room",),
                        "condition_keys": ("meta.baseline_index_compared",),
                        "payload": {"semantic_key": semantic_key},
                    },
                    "source_semantic_change": {
                        "change_key": "aware_meta.class.updated",
                    },
                },
            ),
        },
        provider_delta_head_move_plan={
            "status": "head_move_applied",
            "reason": "meta_ocg_provider_delta_head_move_applied",
            "head_refs": head_refs,
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
            "branch_id": str(branch_id),
            "projection_hash": "projection-hash",
            "object_instance_graph_id": str(object_instance_graph_id),
            "object_instance_graph_identity_id": str(object_instance_graph_identity_id),
            "graph_hash_pre": "hash-pre",
            "graph_hash_post": "hash-post",
        },
    )

    assert translation["status"] == "semantic_commit_evidence_ready"
    assert translation["available"] is True
    assert translation["committed_semantic_change_count"] == 1
    committed_changes = cast(
        Sequence[dict[str, object]],
        translation["committed_semantic_changes"],
    )
    committed_change = committed_changes[0]
    assert committed_change["change_key"] == (
        "aware_meta.provider_delta.class.update.committed"
    )
    assert committed_change["change_type"] == "semantic_operation_committed"
    assert committed_change["semantic_key"] == semantic_key
    assert committed_change["verb"] == "update"
    assert committed_change["source_refs"] == ("home/model.aware",)
    assert committed_change["delta_keys"] == ("delta:room",)
    assert "meta.provider_delta.oig_commit_applied" in cast(
        Sequence[str],
        committed_change["condition_keys"],
    )
    assert committed_change["head_refs"] == head_refs
    commit_ref = cast(dict[str, object], committed_change["commit_ref"])
    assert commit_ref["commit_id"] == str(commit_id)
    assert commit_ref["branch_id"] == str(branch_id)
    metadata = cast(dict[str, object], committed_change["metadata"])
    assert metadata["typed_operation_key"] == (
        "meta_ocg_provider_delta:update:class:room"
    )


def test_meta_provider_delta_semantic_commit_evidence_allows_noop() -> None:
    head_refs = {
        "head_ref_status": "head_refs_available",
        "source_object_instance_graph_commit_id": str(
            _test_uuid("noop-events-source-commit")
        ),
        "semantic_branch_id": str(_test_uuid("noop-events-branch")),
        "semantic_projection_name": "ObjectConfigGraph",
        "semantic_package_id": str(_test_uuid("noop-events-package")),
        "semantic_root_id": str(_test_uuid("noop-events-root")),
        "semantic_package_commit_id": str(_test_uuid("noop-events-commit")),
        "semantic_object_instance_graph_commit_id": str(
            _test_uuid("noop-events-commit")
        ),
        "semantic_root_object_instance_graph_commit_id": str(
            _test_uuid("noop-events-root-commit")
        ),
    }

    translation = _provider_delta_semantic_commit_evidence(
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
            "typed_operations": (),
        },
        provider_delta_head_move_plan={
            "status": "head_move_applied",
            "reason": "meta_ocg_provider_delta_head_move_applied",
            "planned_operation_count": 0,
            "head_refs": head_refs,
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
    )

    assert translation["status"] == "semantic_commit_evidence_ready"
    assert translation["available"] is True
    assert translation["committed_semantic_change_count"] == 0
    assert translation["blockers"] == ()


def _test_uuid(key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"aware:test:meta-provider-delta:{key}")
