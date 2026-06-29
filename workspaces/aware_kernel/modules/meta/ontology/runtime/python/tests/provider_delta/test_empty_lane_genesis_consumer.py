from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from uuid import NAMESPACE_URL, uuid5

import pytest

from aware_code.semantic_materialization import SemanticProviderDeltaRequest
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_orm.registry import ORMModelRegistry
from aware_meta.handlers._generated import meta_handlers
from aware_meta.materialization import workspace_provider
from aware_meta.materialization.deltas.ocg_genesis import (
    OCG_GENESIS_COMPOSITION_KEY,
)
from aware_meta.runtime import build_meta_graph_runtime_for_aware_package_manifests
from aware_meta.runtime.handler_executor import (
    MetaGraphFunctionImplOwnership,
    MetaGraphImplementationPolicy,
)
from aware_meta.runtime.package_index import (
    MetaRuntimePackageIndexEntry,
    build_meta_runtime_package_projection_index,
)
from aware_meta_ontology.stable_ids import stable_object_config_graph_package_id

from .test_ocg_genesis_execution import (
    _GeneratedConstructorBootstrapModule,
    _GeneratedLanguageHandlerModule,
    _attach_generated_orm_bindings,
    _meta_package_manifest_paths,
    REPO_ROOT,
)


@pytest.mark.asyncio
async def test_provider_delta_empty_lane_routes_ocg_genesis(
    tmp_path: Path,
) -> None:
    manifest_path = _write_supported_genesis_package(root=tmp_path)
    request = _empty_lane_provider_delta_request(manifest_path=manifest_path)

    result = await workspace_provider.materialize_delta(request=request)

    assert result["status"] == "succeeded", json.dumps(
        result,
        indent=2,
        sort_keys=True,
        default=str,
    )
    details = _mapping(result["details"])
    operation_plan = _mapping(details["delta_operation_plan"])
    typed_plan = _mapping(details["provider_delta_typed_operation_plan"])
    dirty_diff = _mapping(details["semantic_dirty_diff"])
    head_move_plan = _mapping(details["provider_delta_head_move_plan"])
    ontology_plan = _mapping(operation_plan["provider_delta_ontology_execution_plan"])
    capability_matrix = _mapping(
        details["provider_delta_functioncall_capability_matrix"]
    )

    assert (
        operation_plan["provider_delta_empty_lane_genesis_preflight_status"]
        == "ocg_genesis_consumer_ready"
    )
    assert operation_plan["provider_delta_empty_lane_genesis_route_active"] is True
    genesis_preflight = _mapping(
        operation_plan["provider_delta_empty_lane_genesis_preflight"]
    )
    portal_consumer = _mapping(genesis_preflight["projection_portal_consumer"])
    assert genesis_preflight["projection_portal_consumer_status"] == (
        "projection_portal_consumer_ready"
    )
    assert portal_consumer["portal_status"] == "created_in_plan"
    assert portal_consumer["portal_target_lane_status"] == "created_in_plan"
    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["operation_composition"] == {
        "composition_key": OCG_GENESIS_COMPOSITION_KEY,
        "composition_kind": "meta_ocg_package_genesis",
        "package_semantic_key": "ocg_package:demo-ontology",
        "graph_semantic_key": "ocg:aware_demo",
    }
    assert typed_plan["typed_operation_count"] == 7
    assert dirty_diff["baseline_identity_source"] == (
        "workspace.provider_delta_lane_state"
    )
    assert dirty_diff["baseline_index_compare_status"] == "baseline_index_compared"
    assert dirty_diff["dirty_entry_count"] == 7
    assert head_move_plan["status"] == "head_move_plan_ready"
    assert head_move_plan["planned_operation_count"] == 7
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 8
    assert capability_matrix["execution_allowed"] is True
    execute_flag_preflight = _mapping(details["provider_delta_execute_flag_preflight"])
    assert execute_flag_preflight["status"] == ("execute_flag_preflight_not_requested")


@pytest.mark.asyncio
async def test_provider_delta_empty_lane_executes_ocg_genesis_functioncalls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = _write_supported_genesis_package(root=tmp_path)
    base_request = _empty_lane_provider_delta_request(manifest_path=manifest_path)
    repo_root = REPO_ROOT
    aware_root = tmp_path / "aware-root"
    (aware_root / ".aware").mkdir(parents=True)
    build_meta_runtime_package_projection_index(
        repo_root=tmp_path,
        aware_root=aware_root,
        package_entries=(
            MetaRuntimePackageIndexEntry(
                module_id="demo",
                package_name="demo-ontology",
                fqn_prefix="aware_demo",
                manifest_path=manifest_path,
            ),
        ),
    )
    monkeypatch.setenv("AWARE_ROOT", str(aware_root))
    monkeypatch.setenv("AWARE_PERSISTENCE_BACKEND", "fs")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            _GeneratedLanguageHandlerModule(
                AWARE_META_GRAPH_HANDLERS=meta_handlers.AWARE_META_GRAPH_HANDLERS,
                AWARE_META_GRAPH_INVOCATION_HANDLERS=(
                    meta_handlers.AWARE_META_GRAPH_INVOCATION_HANDLERS
                ),
            ),
        ),
        bootstrap_modules=(
            _GeneratedConstructorBootstrapModule(
                AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS=(
                    meta_handlers.AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS
                ),
            ),
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=(MetaGraphFunctionImplOwnership.authored),
        ),
    )
    context = runtime.context
    assert context is not None
    registry_snapshot = ORMModelRegistry.snapshot_state()
    _attach_generated_orm_bindings(context=context)
    branch_id = uuid5(NAMESPACE_URL, "meta://tests/empty-lane-genesis/branch")
    actor_id = uuid5(NAMESPACE_URL, "meta://tests/empty-lane-genesis/actor")
    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        provider_delta_lane_state=base_request.provider_delta_lane_state,
        semantic_branch_id=str(branch_id),
        actor_id=str(actor_id),
        workspace_root=aware_root,
        runtime=runtime,
        index=context.index,
        context={"aware_meta.graph_runtime_context": context},
        execute_provider_delta_materialization=True,
    )

    try:
        result = await workspace_provider.materialize_delta(request=request)
    finally:
        ORMModelRegistry.restore_state(registry_snapshot)

    details = _mapping(result["details"])
    operation_plan = _mapping(details["delta_operation_plan"])
    execute_preflight = _mapping(details["provider_delta_execute_flag_preflight"])
    commit_receipt = _mapping(details["provider_delta_oig_commit_receipt"])
    mutation_proof = _mapping(details["provider_delta_ontology_mutation_proof"])
    runtime_package_index_patch = _mapping(
        details["provider_delta_runtime_package_index_patch"]
    )
    genesis_preflight_for_failure = _mapping(
        operation_plan.get("provider_delta_empty_lane_genesis_preflight")
    )
    invocation_execution_for_failure = _mapping(
        _ontology_execution_receipt(commit_receipt)
    )
    invocation_receipts_for_failure = _sequence_mapping(
        invocation_execution_for_failure.get("invocation_receipts")
    )
    assert result["status"] == "succeeded", json.dumps(
        {
            "status": result.get("status"),
            "fallback_reason": result.get("fallback_reason"),
            "execute_preflight_status": execute_preflight.get("status"),
            "commit_receipt_status": commit_receipt.get("status"),
            "commit_receipt_error_type": commit_receipt.get("error_type"),
            "commit_receipt_error_message": commit_receipt.get("error_message"),
            "mutation_proof": mutation_proof,
            "runtime_package_index_patch": runtime_package_index_patch,
            "head_move_applied_receipt": details.get(
                "provider_delta_head_move_applied_receipt"
            ),
            "genesis_spec": genesis_preflight_for_failure.get("spec"),
            "applied_invocation_count": invocation_execution_for_failure.get(
                "applied_invocation_count"
            ),
            "invocation_receipts": [
                {
                    "function_name": receipt.get("function_name"),
                    "projection_hash": receipt.get("projection_hash"),
                    "commit_id": receipt.get("commit_id"),
                    "root_object_id": receipt.get("root_object_id"),
                    "expected_result_object_id": receipt.get(
                        "expected_result_object_id"
                    ),
                    "target_projection_name": receipt.get("target_projection_name"),
                    "result_projection_name": receipt.get("result_projection_name"),
                }
                for receipt in invocation_receipts_for_failure
            ],
        },
        indent=2,
        sort_keys=True,
        default=str,
    )
    invocation_execution = _mapping(_ontology_execution_receipt(commit_receipt))
    invocation_receipts = invocation_execution["invocation_receipts"]
    assert isinstance(invocation_receipts, Sequence)
    assert not isinstance(invocation_receipts, str)

    assert (
        operation_plan["provider_delta_empty_lane_genesis_preflight_status"]
        == "ocg_genesis_consumer_ready"
    )
    assert operation_plan["provider_delta_empty_lane_genesis_route_active"] is True
    genesis_preflight = _mapping(
        operation_plan["provider_delta_empty_lane_genesis_preflight"]
    )
    assert genesis_preflight["builder_fallback_used"] is False
    assert genesis_preflight["would_use_builder"] is False
    assert execute_preflight["status"] == "execute_flag_preflight_ready"
    assert execute_preflight["active_execution_rail"] == "ontology_function_call"
    assert commit_receipt["status"] == "execute_flag_commit_applied"
    assert runtime_package_index_patch["status"] == (
        "runtime_package_index_patch_applied"
    )
    assert runtime_package_index_patch["semantic_object_upsert_count"] == 7
    assert runtime_package_index_patch["semantic_object_delete_count"] == 0
    assert runtime_package_index_patch["did_persist"] is True
    assert invocation_execution["status"] == (
        "ontology_function_call_execution_applied"
    )
    assert invocation_execution["applied_invocation_count"] == 8
    assert invocation_execution["did_execute"] is True
    assert invocation_execution["did_persist"] is True
    assert mutation_proof["status"] == "ontology_mutation_proof_ready"
    assert mutation_proof["ready"] is True
    assert mutation_proof["typed_operation_count"] == 7
    assert mutation_proof["ontology_invocation_intent_count"] == 8
    assert mutation_proof["ontology_invocation_receipt_count"] == 8
    assert mutation_proof["ontology_applied_invocation_count"] == 8
    assert mutation_proof["mutation_entry_count"] == 8
    assert mutation_proof["satisfied_mutation_entry_count"] == 8
    assert mutation_proof["blockers"] == ()
    assert mutation_proof["provider_delta_oig_commit_receipt_status"] == (
        "execute_flag_commit_applied"
    )
    assert mutation_proof["provider_delta_head_move_applied_receipt_status"] == (
        "head_move_applied_receipt_ready"
    )
    proof_entries = _sequence_mapping(mutation_proof["entries"])
    assert _proof_entry_exists(
        proof_entries=proof_entries,
        provider_operation_type="meta_ocg.object_config_graph_package.create",
        owner_class_name="ObjectConfigGraphPackage",
        function_name="build",
        mutation_satisfied=True,
    )
    assert _proof_entry_exists(
        proof_entries=proof_entries,
        provider_operation_type="meta_ocg.object_config_graph.create",
        owner_class_name="ObjectConfigGraph",
        function_name="build",
        mutation_satisfied=True,
    )
    assert _proof_entry_exists(
        proof_entries=proof_entries,
        provider_operation_type="meta_ocg.class.create",
        owner_class_name="ObjectConfigGraph",
        function_name="create_node",
        mutation_satisfied=True,
    )
    assert _proof_entry_exists(
        proof_entries=proof_entries,
        provider_operation_type="meta_ocg.class.create",
        owner_class_name="ObjectConfigGraphNode",
        function_name="create_class",
        mutation_satisfied=True,
    )
    assert _proof_entry_exists(
        proof_entries=proof_entries,
        provider_operation_type="meta_ocg.attribute.create",
        owner_class_name="ClassConfig",
        function_name="create_primitive_attribute_config",
        mutation_satisfied=True,
    )
    assert _proof_entry_exists(
        proof_entries=proof_entries,
        provider_operation_type="meta_ocg.object_projection_graph.create",
        owner_class_name="ObjectProjectionGraph",
        function_name="build_via_object_config_graph",
        commit_required=True,
        commit_id_required=True,
        mutation_satisfied=True,
    )
    assert _proof_entry_exists(
        proof_entries=proof_entries,
        provider_operation_type="meta_ocg.object_projection_graph_node.create",
        owner_class_name="ObjectProjectionGraph",
        function_name="create_node",
        commit_required=True,
        commit_id_required=True,
        mutation_satisfied=True,
    )
    assert "legacy_descriptor_tree_readiness_signal" not in details
    assert "legacy_descriptor_tree_execution_gate" not in details
    assert _receipt_exists(
        invocation_receipts=invocation_receipts,
        function_name="build_via_object_config_graph",
        result_projection_name="ObjectProjectionGraph",
    )
    assert _receipt_exists(
        invocation_receipts=invocation_receipts,
        function_name="create_node",
        target_projection_name="ObjectProjectionGraph",
    )


@pytest.mark.asyncio
async def test_provider_delta_existing_head_does_not_activate_empty_lane_genesis(
    tmp_path: Path,
) -> None:
    manifest_path = _write_supported_genesis_package(root=tmp_path)
    request = _empty_lane_provider_delta_request(
        manifest_path=manifest_path,
        lane_status="existing_head",
    )

    result = await workspace_provider.materialize_delta(request=request)

    assert result["status"] == "succeeded"
    details = _mapping(result["details"])
    operation_plan = _mapping(details["delta_operation_plan"])
    typed_plan = _mapping(details["provider_delta_typed_operation_plan"])
    assert (
        operation_plan["provider_delta_empty_lane_genesis_preflight_status"]
        == "ocg_genesis_not_applicable"
    )
    assert operation_plan["provider_delta_empty_lane_genesis_route_active"] is False
    assert typed_plan["typed_operation_count"] == 0


@pytest.mark.asyncio
async def test_provider_delta_empty_lane_blocks_unsupported_shape_without_builder(
    tmp_path: Path,
) -> None:
    manifest_path = _write_supported_genesis_package(
        root=tmp_path,
        class_body=("    name String", "    display_name String"),
    )
    request = _empty_lane_provider_delta_request(manifest_path=manifest_path)

    result = await workspace_provider.materialize_delta(request=request)

    assert result["status"] == "succeeded"
    details = _mapping(result["details"])
    operation_plan = _mapping(details["delta_operation_plan"])
    preflight = _mapping(operation_plan["provider_delta_empty_lane_genesis_preflight"])
    typed_plan = _mapping(details["provider_delta_typed_operation_plan"])
    blockers = preflight["blockers"]
    assert isinstance(blockers, Sequence)
    assert not isinstance(blockers, str)

    assert (
        operation_plan["provider_delta_empty_lane_genesis_preflight_status"]
        == "ocg_genesis_blocked"
    )
    assert operation_plan["provider_delta_empty_lane_genesis_route_active"] is True
    assert "ocg_genesis_requires_one_primitive_attribute:2" in blockers
    assert preflight["builder_fallback_used"] is False
    assert preflight["would_use_builder"] is False
    assert typed_plan["typed_operation_count"] == 0


@pytest.mark.asyncio
async def test_provider_delta_empty_lane_blocks_missing_projection_portal_resolution(
    tmp_path: Path,
) -> None:
    manifest_path = _write_supported_genesis_package(root=tmp_path)
    request = _empty_lane_provider_delta_request(
        manifest_path=manifest_path,
        include_projection_portal_resolution=False,
    )

    result = await workspace_provider.materialize_delta(request=request)

    assert result["status"] == "succeeded"
    details = _mapping(result["details"])
    operation_plan = _mapping(details["delta_operation_plan"])
    preflight = _mapping(operation_plan["provider_delta_empty_lane_genesis_preflight"])
    typed_plan = _mapping(details["provider_delta_typed_operation_plan"])
    blockers = preflight["blockers"]
    assert isinstance(blockers, Sequence)
    assert not isinstance(blockers, str)

    assert (
        operation_plan["provider_delta_empty_lane_genesis_preflight_status"]
        == "ocg_genesis_blocked"
    )
    assert preflight["projection_portal_consumer_status"] == (
        "projection_portal_consumer_blocked"
    )
    assert "projection_portal_resolution_missing" in blockers
    assert typed_plan["typed_operation_count"] == 0


@pytest.mark.asyncio
async def test_provider_delta_empty_lane_blocks_blocked_projection_portal_resolution(
    tmp_path: Path,
) -> None:
    manifest_path = _write_supported_genesis_package(root=tmp_path)
    request = _empty_lane_provider_delta_request(
        manifest_path=manifest_path,
        projection_portal_resolution=_blocked_projection_portal_resolution(),
    )

    result = await workspace_provider.materialize_delta(request=request)

    assert result["status"] == "succeeded"
    details = _mapping(result["details"])
    operation_plan = _mapping(details["delta_operation_plan"])
    preflight = _mapping(operation_plan["provider_delta_empty_lane_genesis_preflight"])
    typed_plan = _mapping(details["provider_delta_typed_operation_plan"])
    blockers = preflight["blockers"]
    assert isinstance(blockers, Sequence)
    assert not isinstance(blockers, str)

    assert (
        operation_plan["provider_delta_empty_lane_genesis_preflight_status"]
        == "ocg_genesis_blocked"
    )
    assert preflight["projection_portal_consumer_status"] == (
        "projection_portal_consumer_blocked"
    )
    assert "projection_lane_unresolved:ObjectProjectionGraph" in blockers
    assert "projection_portal_not_created_in_plan:blocked" in blockers
    assert typed_plan["typed_operation_count"] == 0


def _write_supported_genesis_package(
    *,
    root: Path,
    class_body: tuple[str, ...] = ("    name String",),
) -> Path:
    source_path = root / "aware" / "home" / "room.aware"
    source_path.parent.mkdir(parents=True)
    source_path.write_text(
        "\n".join(
            [
                "class Room {",
                *class_body,
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    manifest_path = root / "aware.toml"
    manifest_path.write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_demo"',
                'sources_dir = "aware"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
                "[build.namespace]",
                '"home/**/*.aware" = "default.home"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return manifest_path


def _empty_lane_provider_delta_request(
    *,
    manifest_path: Path,
    lane_status: str = "empty_lane",
    include_projection_portal_resolution: bool = True,
    projection_portal_resolution: Mapping[str, object] | None = None,
) -> SemanticProviderDeltaRequest:
    package = {
        "package_name": "demo-ontology",
        "workspace_manifest_kind": "aware_toml",
        "manifest_path": manifest_path.as_posix(),
        "source_code_package_id": "source-code-package-id",
    }
    semantic_contract = {
        "module": "aware_meta.semantic_contract",
        "provider_key": "aware_meta",
        "role": "aware_meta.provider",
        "name": "aware.semantic_provider",
    }
    source_text = (manifest_path.parent / "aware" / "home" / "room.aware").read_text(
        encoding="utf-8"
    )
    payload: dict[str, object] = {
        "package": package,
        "semantic_contract": semantic_contract,
        "current_delta_fingerprint": "sha256:empty-lane-genesis",
        "provider_delta_lane_state": {
            "status": lane_status,
            "reason": (
                "baseline_receipts_unavailable"
                if lane_status == "empty_lane"
                else "baseline_ref_resolved"
            ),
            "package": package,
            "semantic_contract": semantic_contract,
            "candidate_count": 0 if lane_status == "empty_lane" else 1,
            "evidence_complete": lane_status == "empty_lane",
            "missing_required_fields": [],
            "blockers": [],
            "source_object_instance_graph_commit_id": str(
                uuid5(
                    NAMESPACE_URL,
                    "meta://tests/empty-lane-genesis/source-oig-commit",
                )
            ),
            "semantic_package_id": str(
                stable_object_config_graph_package_id(
                    package_name="demo-ontology",
                    fqn_prefix="aware_demo",
                )
            ),
        },
        "code_package_delta": CodePackageDelta(
            package_name="demo-ontology",
            package_root=".",
            sources_root="aware",
            manifest_relative_path="aware.toml",
            authority_kind="workspace_sdk",
            source_revision_id="empty-lane-genesis-current",
            paths=[
                CodePackageDeltaPath(
                    relative_path="aware/home/room.aware",
                    kind=CodePackageDeltaKind.create,
                    content_text=source_text,
                    language=CodeLanguage.aware,
                    is_structural=True,
                )
            ],
        ),
    }
    if include_projection_portal_resolution:
        payload["previous_materialization_evidence"] = {
            "projection_portal_resolution": (
                projection_portal_resolution or _ready_projection_portal_resolution()
            )
        }
    return SemanticProviderDeltaRequest.model_validate(payload)


def _ready_projection_portal_resolution() -> dict[str, object]:
    return {
        "resolution_kind": "workspace_semantic_projection_portal_resolution",
        "status": "ready",
        "reason": "projection_portal_resolution_ready",
        "provider_key": "aware_meta",
        "operation_family": "ocg_genesis",
        "primary_projection": "ObjectConfigGraphPackage",
        "projection_lanes": [
            {
                "projection_name": "ObjectConfigGraphPackage",
                "status": "empty_lane",
                "reason": "baseline_receipt_unavailable",
                "participation": "required",
            },
            {
                "projection_name": "ObjectConfigGraph",
                "status": "empty_lane",
                "reason": "baseline_receipt_unavailable",
                "participation": "required",
            },
            {
                "projection_name": "ObjectProjectionGraph",
                "status": "created_in_plan",
                "reason": "projection_created_in_plan",
                "participation": "created_in_plan",
            },
        ],
        "portals": [
            {
                "policy_key": "aware_meta.ocg_genesis.object_projection_graphs",
                "source_projection": "ObjectConfigGraph",
                "source_path": "ObjectConfigGraph.object_projection_graphs",
                "target_projection": "ObjectProjectionGraph",
                "hydration": "created_in_plan",
                "status": "created_in_plan",
                "reason": "portal_target_created_in_plan",
                "target_lane_status": "created_in_plan",
                "blockers": [],
            },
        ],
        "blockers": [],
    }


def _blocked_projection_portal_resolution() -> dict[str, object]:
    payload = _ready_projection_portal_resolution()
    payload["status"] = "blocked"
    payload["reason"] = "projection_portal_resolution_blocked"
    payload["blockers"] = ["projection_lane_unresolved:ObjectProjectionGraph"]
    portals = cast(list[dict[str, object]], payload["portals"])
    portals[0] = {
        **portals[0],
        "status": "blocked",
        "reason": "portal_target_lane_blocked",
        "target_lane_status": "blocked",
        "blockers": [
            "projection_lane_unresolved:ObjectProjectionGraph",
            "portal_target_lane_blocked:aware_meta.ocg_genesis.object_projection_graphs",
        ],
    }
    return payload


def _receipt_exists(
    *,
    invocation_receipts: object,
    function_name: str,
    result_projection_name: str | None = None,
    target_projection_name: str | None = None,
) -> bool:
    if not isinstance(invocation_receipts, Sequence) or isinstance(
        invocation_receipts,
        str,
    ):
        return False
    for receipt in invocation_receipts:
        if not isinstance(receipt, Mapping):
            continue
        if receipt.get("function_name") != function_name:
            continue
        if (
            result_projection_name is not None
            and receipt.get("result_projection_name") != result_projection_name
        ):
            continue
        if (
            target_projection_name is not None
            and receipt.get("target_projection_name") != target_projection_name
        ):
            continue
        return True
    return False


def _proof_entry_exists(
    *,
    proof_entries: object,
    provider_operation_type: str,
    owner_class_name: str,
    function_name: str,
    mutation_satisfied: bool,
    commit_required: bool | None = None,
    commit_id_required: bool = False,
) -> bool:
    if not isinstance(proof_entries, Sequence) or isinstance(proof_entries, str):
        return False
    for entry in proof_entries:
        if not isinstance(entry, Mapping):
            continue
        if entry.get("provider_operation_type") != provider_operation_type:
            continue
        if entry.get("owner_class_name") != owner_class_name:
            continue
        if entry.get("function_name") != function_name:
            continue
        if entry.get("mutation_satisfied") is not mutation_satisfied:
            continue
        if (
            commit_required is not None
            and entry.get("commit_required") is not commit_required
        ):
            continue
        if commit_id_required and not entry.get("commit_id"):
            continue
        return True
    return False


def _sequence_mapping(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _ontology_execution_receipt(
    commit_receipt: Mapping[str, object],
) -> object:
    return commit_receipt.get(
        "ontology_function_call_execution_receipt"
    ) or commit_receipt.get("ontology_invocation_execution_receipt")


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, Mapping)
    return dict(cast(Mapping[str, object], value))
