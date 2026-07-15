from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

import pytest

from aware_code.semantic_materialization import (
    SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
    SemanticProviderDeltaDurableExecutionInputs,
)
from aware_meta.materialization import workspace_provider
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)

from ..fixtures import (
    baseline_ref_payload,
    baseline_semantic_object_index_payload,
    provider_delta_request,
    write_meta_delta_fixture,
)


@pytest.mark.asyncio
async def test_meta_provider_delta_execute_flag_ignores_retired_append_ready_inputs(
    tmp_path: Path,
) -> None:
    manifest_path = write_meta_delta_fixture(tmp_path)
    base_request = provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
    )
    semantic_branch_id = uuid4()
    baseline_ref = baseline_ref_payload(manifest_path=manifest_path)
    baseline_ref["semantic_branch_id"] = str(semantic_branch_id)
    object_instance_graph_id = uuid4()
    object_projection_graph_id = uuid4()
    root_class_config_id = uuid4()
    root_source_object_id = uuid4()
    root_class_instance = ClassInstance(
        id=uuid4(),
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=root_class_config_id,
        source_object_id=root_source_object_id,
    )
    baseline_oig = ObjectInstanceGraph(
        id=object_instance_graph_id,
        object_projection_graph_id=object_projection_graph_id,
        key="baseline",
        name="Baseline",
        description=None,
        hash="",
        root_class_instance=root_class_instance,
        root_class_instance_id=root_class_instance.id,
        class_instances=[root_class_instance],
        class_instance_relationships=[],
    )
    object_instance_graph_identity_id = uuid4()
    author_id = uuid4()

    async def baseline_oig_hydrator(
        *,
        request: object,
        baseline_ref: Mapping[str, object],
    ) -> tuple[ObjectInstanceGraph, dict[str, object]]:
        _ = request
        assert baseline_ref["semantic_branch_id"] == str(semantic_branch_id)
        return (
            baseline_oig,
            {
                "semantic_projection_hash": "projection-hash",
                "baseline_semantic_object_index": (
                    baseline_semantic_object_index_payload()
                ),
            },
        )

    durable_execution_inputs = SemanticProviderDeltaDurableExecutionInputs(
        provider_key="aware_meta",
        semantic_owner="aware_meta.provider",
        semantic_branch_id=str(semantic_branch_id),
        semantic_projection_hash="projection-hash",
        semantic_projection_name="ObjectConfigGraphPackage",
        author_id=str(author_id),
        source_object_instance_graph_commit_id="source-oig-commit",
        semantic_object_instance_graph_commit_id="semantic-package-oig-commit",
        semantic_root_object_instance_graph_commit_id="semantic-root-oig-commit",
        semantic_package_id="semantic-package-id",
        semantic_package_commit_id="semantic-package-commit-id",
        object_instance_graph_identity_id=str(object_instance_graph_identity_id),
        provider_inputs={
            "baseline_oig_hydrator": baseline_oig_hydrator,
        },
    ).model_dump(mode="python")
    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        baseline_ref=baseline_ref,
        baseline_source_object_instance_graph_commit_id=(
            base_request.baseline_source_object_instance_graph_commit_id
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            base_request.baseline_semantic_object_instance_graph_commit_id
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            base_request.baseline_semantic_root_object_instance_graph_commit_id
        ),
        context={
            SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY: (
                durable_execution_inputs
            ),
        },
        execute_provider_delta_materialization=True,
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])
    execute_preflight = cast(
        dict[str, object],
        details["provider_delta_execute_flag_preflight"],
    )
    operation_execution = cast(
        dict[str, object],
        details["provider_delta_operation_execution"],
    )
    mutation_plan = cast(
        dict[str, object],
        details["provider_delta_mutation_plan"],
    )
    commit_receipt = cast(
        dict[str, object],
        details["provider_delta_oig_commit_receipt"],
    )
    head_move_applied_receipt = cast(
        dict[str, object],
        details["provider_delta_head_move_applied_receipt"],
    )
    head_move_plan = cast(
        dict[str, object],
        details["provider_delta_head_move_plan"],
    )
    semantic_commit_evidence = cast(
        dict[str, object],
        details["provider_delta_semantic_commit_evidence"],
    )
    operation_plan = cast(dict[str, object], details["delta_operation_plan"])
    dirty_diff = cast(dict[str, object], details["semantic_dirty_diff"])

    assert result["status"] == "fallback_required"
    assert result["fallback_reason"] == (
        "meta_ocg_delta_execute_flag_preflight_blocked"
    )
    assert result["applied_semantic_keys"] == ()
    assert dirty_diff["status"] == "semantic_dirty_diff_blocked"
    assert dirty_diff["reason"] == (
        "meta_ocg_runtime_delta_transform_unsupported_semantic_shape"
    )
    assert execute_preflight["status"] == "execute_flag_preflight_blocked"
    assert execute_preflight["reason"] == (
        "meta_ocg_provider_delta_execute_flag_preflight_blocked"
    )
    assert execute_preflight["baseline_hydration_status"] == "baseline_hydrated"
    assert execute_preflight["semantic_dirty_diff_status"] == (
        "semantic_dirty_diff_blocked"
    )
    assert execute_preflight["provider_delta_head_move_status"] == (
        "head_move_plan_blocked"
    )
    assert execute_preflight["provider_delta_typed_operation_status"] == (
        "typed_operation_plan_blocked"
    )
    assert execute_preflight["provider_delta_mutation_plan_status"] == (
        "mutation_plan_blocked"
    )
    assert "semantic_dirty_diff_not_ready:semantic_dirty_diff_blocked" in cast(
        Sequence[str],
        execute_preflight["blockers"],
    )
    assert _descriptor_tree_payload_keys(execute_preflight) == ()
    assert _descriptor_tree_payload_keys(mutation_plan) == ()
    assert _descriptor_tree_payload_keys(commit_receipt) == ()
    assert "provider_delta_durable_oig_execution_inputs_preflight" not in details
    assert "durable_oig_execution_inputs_status" not in commit_receipt
    assert "durable_oig_execution_inputs_preflight" not in operation_execution
    assert "provider_delta_durable_oig_execution_inputs_status" not in operation_plan
    assert commit_receipt["status"] == "execute_flag_commit_blocked"
    assert head_move_applied_receipt["status"] == (
        "head_move_applied_receipt_unavailable"
    )
    assert head_move_plan["status"] == "head_move_plan_blocked"
    assert semantic_commit_evidence["status"] == ("semantic_commit_evidence_blocked")
    assert operation_plan["provider_delta_head_move_status"] == (
        "head_move_plan_blocked"
    )


def _descriptor_tree_payload_keys(payload: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(sorted(key for key in payload if "descriptor_tree" in key))
